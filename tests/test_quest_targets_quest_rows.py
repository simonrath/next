"""Quest row clicks retain a live target of the same quest."""
import unittest
import test_quest_targets as addon


class QuestRowTargetTests(unittest.TestCase):
    setUp = addon.QuestTargetsTests.setUp

    def test_repeat_click_on_all_quest_list_buttons(self):
        for interface in (11509, 20506, 50504, 16001, 120105):
            with self.subTest(interface=interface):
                self.setUp()
                self.lua.globals().testInterface = interface
                self.lua.execute("""
                    GetBuildInfo=function() return '', '', '', testInterface end
                    QuestTargetsDB={ellesmereTrackerButtons=true}; boot()
                    local line=CreateFrame('Button',nil,UIParent)
                    line.mode='quest'
                    line.Quest={Id=1}
                    line.expandQuest=CreateFrame('Button',nil,line)
                    line.expandQuest.left=120
                    line.expandQuest.centerY=400
                    Questie={db={profile={trackerEnabled=true}}}
                    QuestieLoader={ImportModule=function()
                        return {GetHighestIndex=function() return 1 end, GetLine=function() return line end}
                    end}
                    NS.QuestieTracker.Sync(NS.app)
                    local buttons={NS.UI.rows[1], assert(NS.QuestieTracker.buttons[1])}
                    if testInterface==16001 then
                        function RegisterStateDriver() end
                        function GameTooltip:IsOwned() return false end
                        EllesmereUI={RegisterQuestTrackerRow=function(_,callback) ellesmereRow=callback; return true end}
                        NS.EllesmereTracker.Sync(NS.app)
                        ellesmereRow(line,1); flush()
                        buttons[#buttons+1]=assert(NS.EllesmereTracker.buttons[1])
                        FlareUI_QuestTrackerAPI={version=1, RegisterCallback=function() end,
                            UnregisterCallback=function() end, IsActive=function() return true end,
                            GetRows=function() return {{questID=1,point='TOPRIGHT',x=120,y=400,size=22}} end}
                        NS.app.db.flareUITrackerButtons=true
                        NS.FlareUITracker.Sync(NS.app)
                        buttons[#buttons+1]=assert(NS.FlareUITracker.buttons[1])
                    end
                    plate('Waldwolf','','').guid='A'
                    plate('Waldwolf','','').guid='B'
                    for index,button in ipairs(buttons) do
                        currentGUID=nil
                        button.scripts.PreClick(button,'LeftButton',false)
                        assert(button.attributes.macrotext1:find('/targetexact',1,true), index)
                        currentGUID='A'
                        button.scripts.PostClick(button,'LeftButton',false)
                        for i=1,3 do
                            button.scripts.PreClick(button,'LeftButton',false)
                            local macro=button.attributes.macrotext1 or ''
                            assert(not macro:find('/target',1,true) and not macro:find('/cleartarget',1,true), index)
                            button.scripts.PostClick(button,'LeftButton',false)
                        end
                        if index<=2 then
                            assert(button.attributes.macrotext1:match('^/stopmacro %[combat,exists,harm,nodead%]'))
                        end
                    end
                """)
