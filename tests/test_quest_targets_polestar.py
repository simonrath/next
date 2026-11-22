"""Polestar guide integration exercises Quest Targets' real secure master path."""
import unittest
import test_quest_targets as addon


class PolestarTests(unittest.TestCase):
    setUp = addon.QuestTargetsTests.setUp

    def test_polestar_option_and_upstream_lock_fit_and_work_together(self):
        self.lua.execute('''
            C_AddOns={IsAddOnLoaded=function(name) return name=='Polestar' end}
            Polestar={Engine={GetStepIndex=function() return 1 end,
                GetStepView=function() return {goals={{t='kill',status='active',subject='Wolf'}}} end}}
            boot()
            NS.UI.Settings(NS.app)
            local options, master = NS.UI.settings, NS.UI.masterSettings
            local bar = master.lockToggle.parent
            assert(options.polestarToggle.parent==bar)
            assert(options.polestarToggle.point[2] > options.masterToggle.point[2])
            assert(options.masterToggle.point[3] > options.polestarToggle.point[3])
            assert(options.polestarToggle.point[3] > options.restedXPToggle.point[3])
            assert(master.dividersToggle.point[3] > master.lockToggle.point[3])
            assert(master.lockToggle.point[3] > master.moveButton.point[3])
            assert(master.moveHelp.point[5] - master.moveHelp.height >= -bar.height)
            assert(options.pages[3].content.height >= 390 + bar.height)
            options.polestarToggle.scripts.OnClick()
            assert(NS.app.db.polestarIntegration and NS.UI.master.entry.name=='Wolf')
            master.lockToggle.scripts.OnClick()
            assert(NS.app.db.masterLocked and NS.UI.master.entry.name=='Wolf')
        ''')

    def test_collect_alternative_cycles_and_excludes_unsafe_or_object_sources(self):
        self.lua.execute('''
            Polestar={Engine={GetStepIndex=function() return 1 end,
                GetStepView=function() return {goals={
                    {t='collect',status='active',source={kind='npc',name='Grell',also='Grellkin',enemy=true}},
                    {t='collect',status='pending',source={kind='npc',name='Grell',also='Bad/quit',enemy=true}},
                    {t='collect',status='active',source={kind='object',name='Chest',also='Crate'}},
                }} end}}
            QuestTargetsDB={polestarIntegration=true,autoMark=false}
            boot()
            assert(table.concat(NS.RestedXP.targets,'|')=='Grell|Grellkin')
            local button=NS.UI.master
            button.scripts.PreClick(button,'LeftButton',false)
            assert(button.attributes.macrotext1:find('Grell',1,true))
            button.scripts.PostClick(button,'LeftButton',false)
            assert(button.entry.name=='Grellkin')
            button.scripts.PreClick(button,'LeftButton',false)
            assert(button.attributes.macrotext1:find('Grellkin',1,true))
        ''')

    def test_friendly_collect_sources_stay_selected_across_master_clicks(self):
        self.lua.execute('''
            local goals={{t='collect',status='active',source={kind='npc',
                name='Friendly Trader',also='Other Trader',enemy=false}}}
            Polestar={Engine={GetStepIndex=function() return 1 end,
                GetStepView=function() return {goals=goals} end}}
            QuestTargetsDB={polestarIntegration=true,autoMark=false}
            boot()
            assert(NS.RestedXP.allEntry.finisherNames['Friendly Trader'])
            assert(NS.RestedXP.allEntry.finisherNames['Other Trader'])
            units.target={name='Friendly Trader',friendly=true}
            assert(NS.Core.ValidCurrentTarget(NS.RestedXP.allEntry))
            local button=NS.UI.master
            button.scripts.PreClick(button,'LeftButton',false)
            assert(not button.attributes.macrotext1:find('/cleartarget',1,true))
            button.scripts.PostClick(button,'LeftButton',false)
            button.scripts.PreClick(button,'LeftButton',false)
            assert(not button.attributes.macrotext1:find('/cleartarget',1,true))
            goals[1].source.enemy=true
            NS.RestedXP.Sync(NS.app)
            assert(not NS.RestedXP.allEntry.finisherNames['Friendly Trader'])
            assert(not NS.Core.ValidCurrentTarget(NS.RestedXP.allEntry))
        ''')

    def test_friendly_collect_source_overrides_matching_native_name_only(self):
        self.lua.execute('''
            local goals={{t='collect',status='active',source={kind='npc',
                name='Waldwolf',also='Other Trader',enemy=false}}}
            Polestar={Engine={GetStepIndex=function() return 1 end,
                GetStepView=function() return {goals=goals} end}}
            QuestTargetsDB={polestarIntegration=true,autoMark=false}
            boot()
            assert(NS.UI.master.defaultEntry.names['Waldwolf'])
            assert(NS.RestedXP.allEntry.finisherNames['Waldwolf'])
            units.target={name='Other Trader',friendly=true}
            assert(NS.Core.ValidCurrentTarget(NS.RestedXP.allEntry))
            NS.UI.master.scripts.PreClick(NS.UI.master,'LeftButton',false)
            assert(not NS.UI.master.attributes.macrotext1:find('/cleartarget',1,true))
            goals[1].npcName='Different Mob'
            NS.RestedXP.Sync(NS.app)
            assert(not NS.RestedXP.allEntry.finisherNames['Different Mob'])
            assert(NS.RestedXP.allEntry.finisherNames['Other Trader'])
        ''')

    def test_master_follows_open_polestar_goals_and_returns_to_native(self):
        self.lua.execute('''
            local goals = {
                {t='kill', status='active', subject='Timber Wolf', subjectKind='npc'},
                {t='turnin', status='pending', npcName='Marshal McBride'},
                {t='kill', status='done', subject='Old Wolf', subjectKind='npc'},
            }
            Polestar={Engine={GetStepIndex=function() return 1 end,
                GetStepView=function() return {goals=goals} end,
                GetGuide=function() return {steps={{goals={}}}} end}}
            QuestTargetsDB={polestarIntegration=true,autoMark=false}
            boot()
            assert(NS.UI.master.entry.name=='Timber Wolf')
            NS.UI.master.scripts.PreClick(NS.UI.master,'LeftButton',false)
            assert(NS.UI.master.attributes.macrotext1:find('Timber Wolf',1,true))
            NS.UI.master.scripts.PostClick(NS.UI.master,'LeftButton',false)
            assert(NS.UI.master.entry.name=='Marshal McBride')
            assert(not NS.RestedXP.allEntry.names['Old Wolf'])
            goals={}
            NS.app:Poll()
            assert(NS.UI.master.entry==NS.UI.master.defaultEntry)
        ''')

    def test_provider_absence_errors_and_combat_keep_native_safe(self):
        self.lua.execute('''
            QuestTargetsDB={polestarIntegration=true}
            boot()
            assert(not NS.RestedXP.active)
            Polestar={Engine={GetStepIndex=function() return 1 end,
                GetStepView=function() error('provider failed') end}}
            NS.app:Poll()
            assert(NS.UI.master.entry==NS.UI.master.defaultEntry)
            local before=NS.UI.master.attributes.macrotext1
            combat=true
            NS.app:Poll()
            NS.RestedXP.Sync(NS.app)
            assert(NS.UI.master.attributes.macrotext1==before)
            combat=false
            Polestar=nil
            NS.app:Poll()
            assert(not NS.RestedXP.active)
            assert(NS.UI.master.entry==NS.UI.master.defaultEntry)
        ''')

    def test_selected_npc_never_borrows_another_raw_npc(self):
        self.lua.execute('''
            Polestar={Names={Npc=function(id) if id==1 then return 'Wrong NPC' end end},
                Engine={GetStepIndex=function() return 1 end,
                GetStepView=function() return {goals={
                    {t='turnin',status='active',npcName='Correct NPC'}}} end,
                GetGuide=function() return {steps={{goals={{npc=1}}}}} end}}
            QuestTargetsDB={polestarIntegration=true}
            boot()
            assert(not NS.RestedXP.allEntry.names['Wrong NPC'])
            assert(NS.UI.master.entry.name=='Correct NPC')
        ''')

    def test_no_target_for_inactive_objects_or_unsafe_names(self):
        self.lua.execute('''
            Polestar={Engine={GetStepIndex=function() return 1 end,
                GetStepView=function() return {goals={
                    {t='accept',status='na',npcName='Hidden'},
                    {t='kill',status='skipped',subject='Skipped'},
                    {t='collect',status='active',subject='Copper Ore',source={kind='object',name='Chest'}},
                    {t='turnin',status='active',npcName='Bad\\n/quit'},
                }} end}}
            QuestTargetsDB={polestarIntegration=true}
            boot()
            assert(#NS.RestedXP.targets==0)
            assert(NS.UI.master.entry==NS.UI.master.defaultEntry)
        ''')

    def test_restedxp_precedence_and_handoff_to_polestar(self):
        self.lua.execute('''
            Polestar={Engine={GetStepIndex=function() return 1 end,
                GetStepView=function() return {goals={{t='kill',status='active',subject='Polestar Wolf'}}} end}}
            local rxp={RXPFrame={activeSteps={{active=true,elements={{mobs={'RXP Bear'}}}}}},
                GetCreatureName=function(id) return id end}
            local oldLibStub=LibStub
            LibStub=function(name) if name=='AceAddon-3.0' then
                return {GetAddon=function() return rxp end}
            else return oldLibStub(name) end end
            QuestTargetsDB={polestarIntegration=true,restedXPIntegration=true}
            boot()
            assert(NS.RestedXP.provider=='restedxp')
            assert(NS.UI.master.entry.name=='RXP Bear')
            NS.app.db.restedXPIntegration=false
            NS.RestedXP.Sync(NS.app)
            assert(NS.RestedXP.provider=='polestar')
            assert(NS.UI.master.entry.name=='Polestar Wolf')
            assert(not NS.RestedXP.button:IsShown())
            NS.app.db.polestarIntegration=false
            NS.RestedXP.Sync(NS.app)
            assert(NS.UI.master.entry==NS.UI.master.defaultEntry)
        ''')

    def test_step_change_refreshes_after_combat(self):
        self.lua.execute('''
            local name='First Wolf'
            Polestar={Engine={GetStepIndex=function() return 1 end,
                GetStepView=function() return {goals={{t='kill',status='active',subject=name}}} end}}
            QuestTargetsDB={polestarIntegration=true}
            boot()
            assert(NS.UI.master.entry.name=='First Wolf')
            combat=true
            name='Second Wolf'
            NS.app:Poll()
            assert(NS.UI.master.entry.name=='First Wolf')
            combat=false
            event('PLAYER_REGEN_ENABLED')
            flush()
            NS.app:Poll()
            assert(NS.UI.master.entry.name=='Second Wolf')
        ''')
