import unittest

import test_quest_targets as addon


class FollowTheArrowTests(unittest.TestCase):
    setUp = addon.QuestTargetsTests.setUp

    def test_master_reads_only_current_guide_targets_and_rereads_on_click(self):
        self.lua.execute(r'''
            GetBuildInfo=function() return '1.60.1','','',16001 end
            C_AddOns={IsAddOnLoaded=function(name) return name=='FollowTheArrow' end}
            FTADB={profile={general={}}}
            FTACharDB={progress={activeModuleId='test_guide'}}
            local body='/cleartarget\n/targetexact Guide NPC\n/cleartarget [dead]'
                ..'\n/targetexact [noexists] Other NPC\n/cleartarget [dead]'
                ..'\n/ping [@target]\n/targetexact Extra Command'
            GetMacroIndexByName=function(name) assert(name=='FTA Target'); return 25 end
            GetMacroBody=function(index) assert(index==25); return body end
            QuestTargetsDB={followTheArrowIntegration=true,autoMark=false}
            boot()
            assert(not NS.Database.Provider() and not NS.RestedXP.active)
            local button=NS.UI.master
            assert(button.entry.name=='Guide NPC' and button.entry.finisherNames['Guide NPC'])
            assert(button.entry.names['Other NPC'] and button.entry.names.Waldwolf)
            assert(not button.entry.names['Extra Command'])
            button.scripts.PreClick(button,'LeftButton',false)
            assert(button.attributes.macrotext1:find('/targetexact [noexists] Guide NPC',1,true))
            assert(not button.attributes.macrotext1:find('/ping',1,true))
            body='/cleartarget\n/targetexact New NPC\n/cleartarget [dead]'
            button.scripts.PreClick(button,'LeftButton',false)
            assert(button.entry.name=='New NPC' and not button.entry.names['Guide NPC'])
            NS.app.db.masterAllModules=false
            button.scripts.PreClick(button,'LeftButton',false)
            assert(not button.entry.names['New NPC'] and button.entry.names.Waldwolf)
        ''')

    def test_opt_in_retail_and_invalid_or_stale_macro(self):
        self.lua.execute(r'''
            local loaded=true
            C_AddOns={IsAddOnLoaded=function(name) return loaded and name=='FollowTheArrow' end}
            FTACharDB={progress={activeModuleId='test_guide'}}
            FTADB={profile={general={}}}
            local body='/cleartarget\n/targetexact Malformed;name\n/cleartarget [dead]'
            GetMacroIndexByName=function() return 1 end
            GetMacroBody=function() return body end
            boot()
            assert(not NS.app.db.followTheArrowIntegration)
            NS.UI.Settings(NS.app)
            local toggle=NS.UI.settings.followTheArrowToggle
            assert(toggle.enabled)
            toggle.scripts.OnClick()
            assert(NS.app.db.followTheArrowIntegration)
            local app, button=NS.app, NS.UI.master
            assert(button.entry==button.defaultEntry)
            body='/cleartarget\n/targetexact Guide NPC\n/cleartarget [dead]'
            button.scripts.PreClick(button,'LeftButton',false)
            assert(button.entry.names['Guide NPC'])
            FTACharDB.progress.activeModuleId=''
            button.scripts.PreClick(button,'LeftButton',false)
            assert(not button.entry.names['Guide NPC'])
            FTACharDB.progress.activeModuleId='test_guide'
            FTADB.profile.general.enableTargetingMacro=false
            button.scripts.PreClick(button,'LeftButton',false)
            assert(not button.entry.names['Guide NPC'])
            FTADB.profile.general.enableTargetingMacro=true
            loaded=false
            button.scripts.PreClick(button,'LeftButton',false)
            assert(not button.entry.names['Guide NPC'])
            loaded=true
            GetBuildInfo=function() return '12.1.5','','',120105 end
            NS.UI.UpdateSettings(app)
            assert(not toggle.enabled)
        ''')
