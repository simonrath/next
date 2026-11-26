"""FlareUI's public row API provides positions without protecting its tracker."""
import unittest
import test_quest_targets as addon


class FlareUITrackerTests(unittest.TestCase):
    setUp = addon.QuestTargetsTests.setUp

    def test_options_disable_without_supported_api(self):
        self.lua.execute("""
            boot()
            NS.UI.Settings(NS.app)
            assert(not NS.UI.settings.flareUIToggle.enabled)
            FlareUI_QuestTrackerAPI={version=2}
            NS.UI.UpdateSettings(NS.app)
            assert(not NS.UI.settings.flareUIToggle.enabled)
            assert(#NS.FlareUITracker.buttons==0)
        """)

    def test_opt_in_row_updates_and_combat_recovery(self):
        self.lua.execute("""
            function RegisterStateDriver(button, state, condition)
                assert(not combat and state=='combat' and condition=='[combat] combat; peace')
                button.driver=condition
            end
            function GameTooltip:IsOwned() return false end
            flareRows={}
            local active=true
            local registrations=0
            FlareUI_QuestTrackerAPI={
                version=1,
                IsActive=function() return active end,
                GetRows=function() return flareRows end,
                RegisterCallback=function(_, owner, callback)
                    registrations=registrations+1
                    rowCallback=callback
                end,
                UnregisterCallback=function() rowCallback=nil end,
            }
            boot()
            NS.UI.Settings(NS.app)
            local toggle=NS.UI.settings.flareUIToggle
            assert(toggle.enabled and not rowCallback)
            local line=CreateFrame('Frame',nil,UIParent)
            flareRows={{questID=1, point='TOPRIGHT', x=175, y=350, size=22, line=line}}
            toggle.scripts.OnClick()
            local tracker=NS.FlareUITracker
            local button=tracker.buttons[1]
            assert(rowCallback and registrations==1 and button:IsShown() and button.parent==UIParent)
            assert(button.point[1]=='TOPRIGHT' and button.point[2]==UIParent and not line.protected)
            assert(button.point[4]==175 and button.point[5]==350 and button.driver)
            assert(button.attributes['_onstate-combat']:find('self:Hide()',1,true))
            button.scripts.PreClick(button,'LeftButton',false)
            assert(button.attributes.macrotext1:find('Waldwolf',1,true))
            button.scripts.PostClick(button,'RightButton',false)
            assert(NS.app.db.focusQuestID==1 and button.focusMark:IsShown())
            flareRows[1].questID=999
            rowCallback(flareRows)
            assert(not button:IsShown() and button.attributes.macrotext1==nil)
            flareRows[1].questID=1
            flareRows[1].x=145
            rowCallback(flareRows)
            assert(button:IsShown() and button.point[4]==145 and registrations==1)
            combat=true
            button.shown=false -- Model the secure state driver.
            rowCallback(flareRows)
            assert(not button:IsShown())
            combat=false
            event('PLAYER_REGEN_ENABLED')
            assert(button:IsShown())
            flareRows={}
            rowCallback(flareRows)
            assert(not button:IsShown() and button.attributes.macrotext1==nil)
            toggle.scripts.OnClick()
            assert(not rowCallback)
        """)
