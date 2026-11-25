"""EllesmereUI public row hooks must never protect the tracker they decorate."""
import unittest
import test_quest_targets as addon


class EllesmereTrackerTests(unittest.TestCase):
    setUp = addon.QuestTargetsTests.setUp

    def tracker(self):
        self.lua.execute('''
            registrations=0
            function RegisterStateDriver(button, state, condition)
                assert(not combat and state=='combat' and condition=='[combat] combat; peace')
                button.driver=condition
            end
            EllesmereUI={RegisterQuestTrackerRow=function(id, callback, width)
                assert(id=='QuestTargets' and width==26)
                registrations=registrations+1; rowCallback=callback
                return true
            end}
        ''')

    def test_optional_api_late_loading_and_options(self):
        self.lua.execute('''
            boot(); NS.UI.Settings(NS.app)
            assert(not NS.UI.settings.ellesmereToggle.enabled)
            assert(not NS.UI.settings.ellesmereOffsetControl.slider.enabled)
            assert(#NS.EllesmereTracker.buttons==0)
        ''')
        self.tracker()
        self.lua.execute('''
            event('ADDON_LOADED','EllesmereUIQuestTracker'); flush()
            NS.UI.UpdateSettings(NS.app)
            assert(NS.UI.settings.ellesmereToggle.enabled)
            local panel=NS.UI.settings
            assert(panel.ellesmereOffsetControl.slider.enabled)
            for _,control in ipairs({panel.tooltipToggle,panel.minimapToggle,panel.questieTrackerToggle,
                panel.questieOffsetControl,panel.ellesmereToggle,panel.ellesmereOffsetControl}) do
                assert(control.parent.parent==panel.pages[3].content)
            end
            assert(registrations==1)
            NS.EllesmereTracker.Sync(NS.app)
            assert(registrations==1)
            NS.UI.settings.ellesmereToggle.scripts.OnClick()
            assert(NS.app.db.ellesmereTrackerButtons==false)
            assert(not panel.ellesmereOffsetControl.slider.enabled)
        ''')

    def test_idle_tracker_uses_callback_and_skips_redundant_secure_writes(self):
        self.tracker()
        self.lua.execute('''
            local now=0
            GetTime=function() return now end
            boot()
            local slot=CreateFrame('Frame',nil,UIParent)
            rowCallback(slot,1); flush()
            local button=NS.EllesmereTracker.buttons[1]
            local writes, reads=0,0
            local setAttribute, getCenter=button.SetAttribute,slot.GetCenter
            button.SetAttribute=function(self,...) writes=writes+1; return setAttribute(self,...) end
            slot.GetCenter=function(self) reads=reads+1; return getCenter(self) end
            now=1
            NS.EllesmereTracker.Sync(NS.app,true)
            assert(reads==0, 'row callback should handle immediate changes')
            now=3
            NS.EllesmereTracker.Sync(NS.app,true)
            assert(reads==1 and writes==0, 'periodic check must not rewrite an identical secure macro')
            rowCallback(slot,999); flush()
            assert(not button:IsShown())
        ''')

    def test_row_reuse_visibility_focus_and_combat(self):
        self.tracker()
        self.lua.execute('''
            boot()
            local slot=CreateFrame('Frame',nil,UIParent)
            slot:SetFrameStrata('HIGH'); slot:SetFrameLevel(10)
            slot.scale=0.5; slot.centerX=300; slot.centerY=400
            rowCallback(slot,1); flush()
            local button=NS.EllesmereTracker.buttons[1]
            assert(button and button:IsShown() and button.parent==UIParent)
            assert(not slot.protected and button.point[2]==UIParent)
            assert(button.point[4]==150 and button.point[5]==200)
            NS.UI.Settings(NS.app)
            NS.UI.settings.ellesmereOffsetControl.slider:SetValue(20)
            flush()
            assert(button.point[4]==160 and button.point[5]==200)
            NS.app.db.ellesmereTrackerOffset=-40
            NS.EllesmereTracker.Sync(NS.app)
            assert(button.point[4]==130)
            assert(button:GetFrameStrata()=='HIGH' and button:GetFrameLevel()==11)
            assert(button.entry.questID==1 and button.driver)
            assert(button.attributes['_onstate-combat']:find('self:Hide()',1,true))
            button.scripts.PreClick(button,'LeftButton',false)
            assert(button.attributes.macrotext1:find('Waldwolf',1,true))
            button.scripts.PostClick(button,'LeftButton',false)
            button.scripts.PostClick(button,'RightButton',false)
            assert(NS.app.db.focusQuestID==1 and button.focusMark:IsShown())
            NS.UI.ToggleFocus(NS.app,button.entry)
            assert(not button.focusMark:IsShown())
            rowCallback(slot,999)
            button.scripts.PreClick(button,'LeftButton',false)
            assert(not button:IsShown() and button.attributes.macrotext1==nil)
            flush()
            rowCallback(slot,1); flush()
            assert(button:IsShown() and #NS.EllesmereTracker.buttons==1)
            slot:Hide()
            NS.EllesmereTracker.Sync(NS.app)
            assert(not button:IsShown())
            slot:Show(); NS.EllesmereTracker.Sync(NS.app)
            combat=true
            -- Simulate the secure state driver independently of addon code.
            button.shown=false
            rowCallback(slot,999)
            NS.EllesmereTracker.Sync(NS.app)
            button.scripts.PreClick(button,'LeftButton',false)
            assert(button.questID==1 and not button:IsShown())
            combat=false
            event('PLAYER_REGEN_ENABLED')
            assert(button.attributes.macrotext1==nil and not button:IsShown())
            rowCallback(slot,1); flush()
            assert(button:IsShown())
            NS.app.db.ellesmereTrackerButtons=false
            NS.EllesmereTracker.Sync(NS.app)
            assert(not button:IsShown() and button.attributes.macrotext1==nil)
            NS.app.db.ellesmereTrackerButtons=true
            NS.EllesmereTracker.Sync(NS.app)
            assert(button:IsShown() and registrations==1)
        ''')
