"""Spatial ranking and fallback regressions against the real Lua modules."""
import unittest
import test_quest_targets as addon


class ProximityTests(unittest.TestCase):
    setUp = addon.QuestTargetsTests.setUp
    database = addon.QuestTargetsTests.database

    def spatial(self):
        self.database()
        self.lua.execute('''
            LibQuestieDB.flavor.name='Forever'
            LibQuestieDB.Support={Get=function() return {private={
                areaIdToUiMapId='return {[215]=1412,[99]=999}'}} end}
            px,py,mapID=0.5,0.5,1412
            function CreateVector2D(x,y) return {x=x,y=y} end
            C_Map={GetBestMapForUnit=function() return mapID end,
                GetPlayerMapPosition=function() return {x=px,y=py} end,
                GetWorldPosFromMapPos=function(id,p)
                    return id==999 and 2 or 1,{x=p.x*1000,y=p.y*1000}
                end}
            records.Npc[10].spawns={[215]={{80,50},{51,50}}}
            records.Npc[11].spawns={[215]={{70,50}}}
            records.Npc[12].spawns={[99]={{50,50}}}
            reads=0
            local get=LibQuestieDB.Npc.Get
            LibQuestieDB.Npc.Get=function(id,key)
                if key=='spawns' then reads=reads+1 end
                return get(id,key)
            end
        ''')


    def test_spawn_projection_skips_other_continents_and_retries_after_travel(self):
        self.spatial()
        self.lua.execute('''
            local p = NS.Proximity
            local world = C_Map.GetWorldPosFromMapPos
            local foreign = 0
            C_Map.GetWorldPosFromMapPos=function(id,pos)
                if id==999 then foreign=foreign+1 end
                return world(id,pos)
            end
            records.Npc[10].spawns[99]={{51,50},{55,56},{65,52},{70,52}}
            p.Register(LibQuestieDB,10,'Waldwolf')
            p.Sample()
            assert(p.Distance('Waldwolf')==100)
            assert(foreign==1, 'only classify the other map once')
            mapID=999
            p.Sample()
            assert(p.Distance('Waldwolf')==100, 'project actual spawns after travel')
        ''')

    def test_guide_buttons_rank_stoley_ahead_of_mobs_and_resample_on_click(self):
        for provider in ('restedxp', 'polestar'):
            with self.subTest(provider=provider):
                self.setUp()
                self.spatial()
                self.lua.globals().testProvider = provider
                self.lua.execute("""
                    records.Npc[7881]={name='Stoley',spawns={[215]={{52,50}}}}
                    records.Npc[5616]={name='Dieb der Wüstenläufer',spawns={[215]={{80,50}}}}
                    LibQuestieDB.Npc.IdsByName=function(name)
                        if name=='Stoley' then return {7881} end
                        if name=='Dieb der Wüstenläufer' then return {5616} end
                    end
                    local rxp={RXPFrame={activeSteps={}},GetCreatureName=function(id) return id end,
                        targeting={GetCurrentTargets=function()
                            return {'Stoley'},{'Dieb der Wüstenläufer'},{}
                        end}}
                    local lib=LibStub
                    LibStub=function(name) if name=='AceAddon-3.0' then
                        return {GetAddon=function() return rxp end}
                    else return lib(name) end end
                    Polestar={Engine={GetStepIndex=function() return 1 end,GetStepView=function()
                        return {goals={
                            {t='kill',status='active',npc=5616,npcName='Dieb der Wüstenläufer'},
                            {t='turnin',status='pending',npc=7881,npcName='Stoley'},
                        }}
                    end}}
                    QuestTargetsDB={restedXPIntegration=testProvider=='restedxp',
                        polestarIntegration=testProvider=='polestar'}
                    quests={}
                    boot()
                    for _,button in ipairs({NS.UI.master,NS.RestedXP.button}) do
                        px=0.5
                        button.scripts.PreClick(button,'LeftButton',false)
                        local text=button.attributes.macrotext1
                        local stoley=text:find('/targetexact [noexists] Stoley',1,true)
                        local thief=text:find('/targetexact [noexists] Dieb der Wüstenläufer',1,true)
                        assert(stoley and thief and stoley < thief, 'Stoley must be tried first')
                        assert(button.entry.nameList[1]=='Stoley')
                        px=0.81
                        button.scripts.PreClick(button,'LeftButton',false)
                        assert(button.entry.nameList[1]=='Dieb der Wüstenläufer')
                        assert(#button.attributes.macrotext1 <= NS.Core.MACRO_BYTES)
                    end
                """)

    def test_master_merges_enabled_guide_item_and_rare_sources(self):
        self.spatial()
        self.lua.execute('''
            records.Npc[7881]={name='Stoley',spawns={[215]={{52,50}}}}
            LibQuestieDB.Npc.IdsByName=function(name)
                if name=='Stoley' then return {7881} end
            end
            local rxp={RXPFrame={activeSteps={}},GetCreatureName=function(id) return id end,
                targeting={GetCurrentTargets=function() return {'Stoley'},{},{} end}}
            local lib=LibStub
            LibStub=function(name) if name=='AceAddon-3.0' then
                return {GetAddon=function() return rxp end}
            else return lib(name) end end
            Polestar={Engine={GetStepIndex=function() return 1 end,GetStepView=function()
                return {goals={{t='kill',status='active',npcName='Guide Mob'}}}
            end}}
            QuestTargetsDB={restedXPIntegration=true,polestarIntegration=true}
            boot()
            NS.ItemTree.SearchEntry=function()
                return {nameList={'Item Mob','Stoley'}}
            end
            NS.RareScanner.SearchEntry=function()
                return {nameList={'Local Rare'},mapPoints={['Local Rare']={{continent=1,x=501,y=500}}}}
            end
            local master=NS.UI.master
            master.scripts.PreClick(master,'LeftButton',false)
            local entry=master.entry
            for _,name in ipairs({'Stoley','Guide Mob','Item Mob','Local Rare','Waldwolf'}) do
                assert(entry.names[name], name)
            end
            assert(entry.nameList[1]=='Local Rare' and entry.nameList[2]=='Waldwolf' and entry.nameList[3]=='Stoley')
            local stoley=0
            for _,name in ipairs(entry.nameList) do if name=='Stoley' then stoley=stoley+1 end end
            assert(stoley==1 and entry.finisherNames.Stoley)
            local blue=NS.RestedXP.button
            blue.scripts.PreClick(blue,'LeftButton',false)
            assert(#blue.entry.nameList==1 and blue.entry.name=='Stoley')
            NS.app.db.masterAllModules=false
            master.scripts.PreClick(master,'LeftButton',false)
            assert(master.entry.names.Waldwolf and not master.entry.names.Stoley)
            assert(not master.entry.names['Guide Mob'] and not master.entry.names['Local Rare'])
            assert(not master.entry.names['Item Mob'])
            blue.scripts.PreClick(blue,'LeftButton',false)
            assert(blue.entry.names.Stoley)
            NS.app.db.masterAllModules=true
            master.scripts.PreClick(master,'LeftButton',false)
            assert(master.entry.names.Stoley and master.entry.names['Local Rare'])

        ''')

    def test_serialized_maps_are_parsed_without_executing_lua(self):
        self.spatial()
        self.lua.execute("""
            local p=NS.Proximity
            loadstring=function() error('Database text must never execute') end
            LibQuestieDB.Support.Get=function() return {private={
                areaIdToUiMapId='return { [215] = 1, -- native zone\\n [99]=999; }',
                areaIdToUiMapIdOverride='return {[215]=1412}'}} end
            p.Register(LibQuestieDB,10,'Waldwolf'); p.Sample()
            assert(p.Distance('Waldwolf')==100)
            assert(p.maps[215]==1412 and p.maps[99]==999)
        """)

    def test_invalid_maps_fail_closed_and_table_maps_still_work(self):
        for value in ('return {[215]=1412}; injected=true',
                      'return {[215]=1412, [99]=unknown()}',
                      'return {[215]=1412 [99]=999}',
                      'return {[215]=-1}',
                      'return {[215]=0/0}'):
            with self.subTest(value=value):
                self.setUp()
                self.spatial()
                self.lua.globals().mapSource=value
                self.lua.execute("""
                    LibQuestieDB.Support.Get=function() return {private={
                        areaIdToUiMapId=mapSource,
                        areaIdToUiMapIdOverride={[99]=999}}} end
                    NS.Proximity.Register(LibQuestieDB,10,'Waldwolf')
                    NS.Proximity.Sample(); NS.Proximity.Distance('Waldwolf')
                    assert(NS.Proximity.maps[215]==nil, 'Accepted malformed map')
                    assert(NS.Proximity.maps[99]==999 and not injected)
                """)

    def test_classic_era_keeps_native_spawn_coordinates(self):
        self.spatial()
        self.lua.execute('''
            function GetBuildInfo() return '1.15.9','69722','',11509 end
            LibQuestieDB.flavor.name='Vanilla'
            LibQuestieDB.EraToForever=function() error('Classic must not convert coordinates to Forever') end
            NS.Proximity.Register(LibQuestieDB,10,'Local mob')
            NS.Proximity.Sample()
            assert(NS.Proximity.Distance('Local mob')==100)
        ''')

    def test_nearest_spawn_roles_unknown_and_cache(self):
        self.spatial()
        self.lua.execute('''
            local p=NS.Proximity
            for _,id in ipairs({10,11,12}) do p.Register(LibQuestieDB,id,records.Npc[id].name) end
            p.Sample()
            local e={name='x',names={},nameList={'Unknown','Junger Waldwolf','Waldwolf','Alter Waldwolf'},
                mobCount=3,finisherNames={['Alter Waldwolf']=true}}
            p.Order(e)
            assert(table.concat(e.nameList,'|')=='Waldwolf|Junger Waldwolf|Unknown|Alter Waldwolf')
            assert(p.Distance('Waldwolf')==100) -- nearest of both spawn points, squared yards
            assert(p.Distance('Alter Waldwolf')==nil) -- different continent
            local rev=p.revision
            assert(not p.Sample()); assert(p.revision==rev)
            px=0.7; assert(p.Sample()); p.Order(e)
            assert(e.nameList[1]=='Junger Waldwolf')
            for i=1,20 do p.Order(e); p.Register(LibQuestieDB,10,'Waldwolf') end
            assert(reads==3)
            C_Map.GetPlayerMapPosition=function() return nil end
            assert(p.Sample()); assert(p.Distance('Waldwolf')==nil)
            p.Order(e); assert(#e.nameList==4)
        ''')

    def test_unknown_and_distant_candidates_eventually_in_short_macros(self):
        self.spatial()
        self.lua.execute('''
            NS.Proximity.Register(LibQuestieDB,10,'Waldwolf')
            NS.Proximity.Sample()
            local e={name='x',refs={},names={Waldwolf=true},nameList={'Waldwolf'},mobCount=1,finisherNames={}}
            for i=1,15 do local name='Unbekanntes Questziel '..i
                e.names[name]=true; e.nameList[#e.nameList+1]=name; e.mobCount=e.mobCount+1 end
            local seen,state={},{}
            for i=1,30 do
                local macro=NS.Core.ClickMacro(e,{}, {autoMark=true,markerIcon=8},state)
                assert(#macro<=255)
                if i==1 then assert(macro:find('Waldwolf',1,true)) end
                for _,name in ipairs(e.nameList) do if macro:find(name..'\\n',1,true) then seen[name]=true end end
            end
            for _,name in ipairs(e.nameList) do assert(seen[name],name) end
        ''')

    def test_click_restarts_name_search_after_small_move_without_waiting_for_poll(self):
        self.spatial()
        self.lua.execute('''
            local p, core = NS.Proximity, NS.Core
            p.Register(LibQuestieDB,10,'Waldwolf')
            local entry={name='Waldwolf',refs={},names={Waldwolf=true},nameList={'Waldwolf'},mobCount=8}
            for i=1,7 do
                local name='Unbekanntes Questziel '..i
                entry.names[name]=true
                entry.nameList[#entry.nameList+1]=name
            end
            local state={}
            local first=core.ClickMacro(entry,{}, {},state)
            assert(first:find('Waldwolf',1,true), 'the closest target should be on the first page')
            assert(core.ClickMacro(entry,{}, {},state)~=first, 'stationary clicks should advance the page')
            px=.505
            assert(core.ClickMacro(entry,{}, {},state)==first, 'movement should restart the first page')
            assert(p.position.x==505, 'the click should read the current position')
        ''')

    def test_visible_target_beats_spawn_estimate_and_mob_beats_finisher(self):
        self.spatial()
        self.lua.execute('''
            NS.Proximity.Register(LibQuestieDB,10,'Waldwolf'); NS.Proximity.Sample()
            local e={name='Waldwolf',refs={},names={Waldwolf=true,NPC=true},nameList={'NPC','Waldwolf'},
                mobCount=1,finisherNames={NPC=true}}
            local unit=plate('NPC','Quest',''); unit.friendly=true
            local macro=NS.Core.ClickMacro(e,{}, {},{})
            assert(macro:find('/targetexact [nocombat] NPC',1,true))
            nameplates={}; units={}; currentGUID=nil
            macro=NS.Core.ClickMacro(e,{}, {},{})
            assert(macro:find('Waldwolf',1,true)<macro:find('NPC',1,true))
        ''')

    def test_forever_conversion_not_applied_twice_and_missing_mapping_safe(self):
        self.spatial()
        self.lua.execute('''
            local p=NS.Proximity
            LibQuestieDB.EraToForever=function() error('Forever data already converted') end
            p.Register(LibQuestieDB,10,'Waldwolf'); p.Sample()
            assert(p.Distance('Waldwolf')==100)
            LibQuestieDB.flavor={name='Vanilla'}
            LibQuestieDB.EraToForever=nil
            p.Register(LibQuestieDB,10,'Waldwolf'); p.Sample()
            assert(p.Distance('Waldwolf')==nil) -- old Mulgore frame cannot be trusted
            LibQuestieDB.Support=nil
            LibQuestieDB.flavor={name='Forever'}
            p.Register(LibQuestieDB,10,'Waldwolf'); p.Sample()
            assert(p.Distance('Waldwolf')==nil)
        ''')

    def test_long_names_do_not_starve_either_role(self):
        self.lua.execute('''
            local mob=string.rep('M',140)
            local npc=string.rep('N',140)
            local e={name=mob,refs={},names={[mob]=true,[npc]=true},nameList={mob,npc},
                mobCount=1,finisherNames={[npc]=true}}
            local state,seen={},{}
            for i=1,6 do
                local macro=NS.Core.ClickMacro(e,{}, {autoMark=true,markerIcon=8},state)
                assert(#macro<=255)
                if i==1 then assert(macro:find(mob,1,true)) end
                if macro:find(mob,1,true) then seen.mob=true end
                if macro:find(npc,1,true) then seen.npc=true end
            end
            assert(seen.mob and seen.npc)
        ''')

    def test_vanilla_converter_percentages_same_name_ids_and_sentinels(self):
        self.spatial()
        self.lua.execute('''
            local p=NS.Proximity
            LibQuestieDB.flavor.name='Vanilla'
            conversions=0
            LibQuestieDB.EraToForever=function(area,x,y)
                assert(area==215 and x>=0 and x<=100)
                conversions=conversions+1; return x+10,y
            end
            records.Npc[10].spawns={[215]={{-1,-1},{30,50},{50,50}}}
            records.Npc[11].spawns={[215]={{41,50}}}
            p.Register(LibQuestieDB,10,'Shared'); p.Register(LibQuestieDB,11,'Shared'); p.Sample()
            assert(math.abs(p.Distance('Shared')-100)<0.001)
            assert(conversions==3)
            for i=1,20 do p.Distance('Shared') end
            assert(conversions==3 and reads==2)
            px=0.6; p.Sample(); p.Distance('Shared')
            assert(conversions==3 and reads==2) -- no new projection or database reads
        ''')

    def test_only_targeting_clicks_sample_position_for_resolved_targets(self):
        self.spatial()
        self.lua.execute('''
            assert(NS.Database.Provider()==LibQuestieDB)
            quests[3]={questID=3,title='Abgabe',complete=true,objectives={}}
            records.Quest[3]={name='Abgabe',finishedBy={{12}}}
            local positionReads=0
            local getPosition=C_Map.GetPlayerMapPosition
            C_Map.GetPlayerMapPosition=function(...)
                positionReads=positionReads+1
                return getPosition(...)
            end
            boot()
            tick()
            NS.app:Refresh(false)
            assert(positionReads==0, 'startup, refresh and polling should not read player coordinates')
            local entry={name='Waldwolf',refs={},names={Waldwolf=true},nameList={'Waldwolf'},mobCount=1}
            NS.Core.ClickMacro(entry,{}, {},{})
            assert(NS.Proximity.Distance('Waldwolf')==100)
            tick()
            local e=NS.UI.master.entry
            assert(e.nameList[1]=='Waldwolf')
            px=0.7
            tick()
            assert(positionReads==1 and NS.UI.master.entry.nameList[1]=='Waldwolf',
                'movement without a click should not change the ranking')
            NS.Core.ClickMacro(entry,{}, {},{})
            tick()
            assert(positionReads==2, 'each targeting click should read player coordinates once')
            assert(NS.UI.master.entry.nameList[1]=='Junger Waldwolf')
        ''')
