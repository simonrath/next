import unittest
import test_quest_targets as addon


class RareScannerTests(unittest.TestCase):
    def test_search_prioritizes_rarescanner_spawns_and_reorders_after_movement(self):
        addon.QuestTargetsTests.setUp(self)
        self.lua.execute('''
            GetBuildInfo=function() return '1.60.1','','',16001 end
            GetTime=function() return 0 end
            RegisterStateDriver=function() end
            RSOverlayMixin={OnAcquired=function() end}
            local names={[1]='A Far Rare',[2]='Z Near Rare',[3]='B Unknown Rare',[4]='Y Sighting'}
            local rs={db={char={overlayActive={}},global={rare_names={deDE=names},rares_found={
                [4]={coordX='2000',coordY='5000',mapID=20},
            }}}}
            local originalLibStub=LibStub
            LibStub=function(name,silent)
                if name=='AceAddon-3.0' then return {GetAddon=function() return rs end} end
                return originalLibStub(name,silent)
            end
            local playerX=.1
            CreateVector2D=function(x,y) return {x=x,y=y} end
            C_Map={
                GetBestMapForUnit=function() return 20 end,
                GetMapArtID=function() return 42 end,
                GetPlayerMapPosition=function() return CreateVector2D(playerX,.5) end,
                GetWorldPosFromMapPos=function(_,pos) return 1,CreateVector2D(pos.x*1000,pos.y*500) end,
            }
            DropdownButtonMixin={SetupMenu=function(self,generator) self.menuGenerator=generator end}
            RSWorldMapButtonMixin={SetupMenu=function(self)
                DropdownButtonMixin.SetupMenu(self,function(_,root)
                    local filter=root:CreateButton('NPCs'):CreateButton('Filter NPCs')
                    for id,name in pairs(names) do filter:CreateCheckbox(name..' ('..id..')') end
                end)
            end}
            local reads=0
            RSExplorerRareList={OnElementSelectionChanged=function(self,data,selected)
                assert(selected and self.mapID==20 and data.isNpc)
                local map=self:GetParent().RareInfo.Map
                assert(map.mapArtID==42 and map:GetWidth()==1)
                reads=reads+1
                if data.entityID==1 then map.iconsPool:Acquire():SetPoint('CENTER',map,'TOPLEFT',.8,-.5)
                elseif data.entityID==2 then
                    map.iconsPool:Acquire():SetPoint('CENTER',map,'TOPLEFT',.6,-.5)
                    map.overlayIconsPool:Acquire():SetPoint('CENTER',map,'TOPLEFT',.12,-.5)
                end
            end}
            QuestTargetsDB={rareScannerZone=true}
            boot()
            local button=NS.RareScanner.markButton
            GameTooltip:Hide()
            button.scripts.OnEnter(button)
            assert(not GameTooltip:IsShown(), 'RareScanner tooltip ignored the disabled setting')
            NS.app.db.showTooltips=true
            button.scripts.OnEnter(button)
            assert(GameTooltip:IsShown() and GameTooltip.text==NS.L('rareScannerButton'))
            button.scripts.OnLeave(button)
            assert(reads==4 and NS.Proximity.position==nil)
            button.scripts.PreClick(button,'LeftButton',false)
            assert(reads==4 and table.concat(button.markedNames,'|')==
                'Z Near Rare|Y Sighting|A Far Rare|B Unknown Rare')
            local macro=button:GetAttribute('macrotext1')
            assert(macro:find('Z Near Rare',1,true)<macro:find('A Far Rare',1,true))
            button.scripts.PreClick(button,'LeftButton',false)
            local nextPage=button:GetAttribute('macrotext1')
            assert(nextPage:find('/targetexact [noexists] Z Near Rare',1,true)
                < nextPage:find('/targetexact [noexists] B Unknown Rare',1,true))
            playerX=.105
            button.scripts.PreClick(button,'LeftButton',false)
            assert(not button:GetAttribute('macrotext1'):find('B Unknown Rare',1,true),
                'movement must restart the first page even when the same rare remains closest')
            playerX=.79
            button.scripts.PreClick(button,'LeftButton',false)
            assert(reads==4 and button.markedNames[1]=='A Far Rare')
            playerX=.696
            button.scripts.PreClick(button,'LeftButton',false)
            assert(button.markedNames[1]=='Z Near Rare')
            playerX=.704
            button.scripts.PreClick(button,'LeftButton',false)
            assert(button.markedNames[1]=='A Far Rare', 'a click must refresh the ranking after a short move')
            playerX=.79
            NS.app.db.rareScannerZone=false
            local function mark(id,x)
                rs.db.char.overlayActive[id]={}
                local poi={entityID=id,name=names[id],isNpc=true,mapID=20}
                RSOverlayMixin:OnAcquired(x,.5,0,0,0,{POI=poi})
            end
            mark(1,.8)
            mark(3,.79)
            tick()
            assert(button.markedNames[1]=='B Unknown Rare' and button.markedNames[2]=='A Far Rare')
            playerX=.1
            tick()
            assert(button.markedNames[1]=='B Unknown Rare')
            playerX=.78
            units.target={name='A Far Rare'}
            button.scripts.PreClick(button,'LeftButton',false)
            assert(button.markedNames[1]=='B Unknown Rare', 'a selected rare must not freeze the coordinate order')
            assert(button:GetAttribute('macrotext1')==nil, 'keep the selected rare')
            units.target=nil
            playerX=.1
            NS.app.db.rareScannerZone=true
            button.scripts.PreClick(button,'LeftButton',false)
            plate('Z Near Rare','','')
            button.scripts.PreClick(button,'LeftButton',false)
            assert(button:GetAttribute('macrotext1'):find('/targetexact [nocombat] Z Near Rare',1,true),
                'a readable nearby plate must bypass the already advanced page')

        ''')

    def test_cold_zone_spawn_queries_are_batched_without_hiding_targets(self):
        addon.QuestTargetsTests.setUp(self)
        self.lua.execute('''
            GetBuildInfo=function() return '1.60.1','','',16001 end
            local now=0
            GetTime=function() return now end
            RegisterStateDriver=function() end
            RSOverlayMixin={OnAcquired=function() end}
            local rs={db={char={overlayActive={}},global={}}}
            local originalLibStub=LibStub
            LibStub=function(name,silent)
                if name=='AceAddon-3.0' then return {GetAddon=function() return rs end} end
                return originalLibStub(name,silent)
            end
            local mapID=20
            C_Map={GetBestMapForUnit=function() return mapID end, GetMapArtID=function() return 42 end}
            DropdownButtonMixin={SetupMenu=function(self,generator) self.menuGenerator=generator end}
            RSWorldMapButtonMixin={SetupMenu=function(self)
                DropdownButtonMixin.SetupMenu(self,function(_,root)
                    local filter=root:CreateButton('NPCs'):CreateButton('Filter NPCs')
                    if mapID==20 then
                        for i=1,80 do filter:CreateCheckbox('Zone rare '..i..' ('..i..')') end
                    else
                        filter:CreateCheckbox('Other rare (81)')
                    end
                end)
            end}
            local reads, nextFrame=0,{}
            RSExplorerRareList={OnElementSelectionChanged=function(self)
                assert(not combat and self.mapID==mapID)
                reads=reads+1
            end}
            local after=C_Timer.After
            C_Timer.After=function(delay,fn)
                if delay==0 then nextFrame[#nextFrame+1]=fn else after(delay,fn) end
            end
            QuestTargetsDB={rareScannerZone=true}
            boot()
            local b=NS.RareScanner.markButton
            assert(#b.markedNames==80, 'every name must be available as soon as the list is built')
            assert(reads>0 and reads<=8 and #nextFrame==1, 'cold reads must be spread over frames')
            local first=reads
            combat=true
            table.remove(nextFrame,1)()
            assert(reads==first and #nextFrame==0)
            combat=false
            tick()
            while #nextFrame>0 do
                local before=reads
                table.remove(nextFrame,1)()
                assert(reads-before<=8)
            end
            assert(reads==80)
            now=16
            tick()
            assert(reads==80 and #nextFrame==0, 'a warm zone rebuild should reuse all spawn data')
            now=61
            tick()
            assert(reads==88 and #nextFrame==1, 'a cold rebuild should start one batch')
            mapID=21
            table.remove(nextFrame,1)()
            assert(reads==88 and #nextFrame==0, 'leaving the zone cancels the remaining work')
            b.scripts.PreClick(b,'LeftButton',false)
            assert(reads==89 and #b.markedNames==1 and b.markedNames[1]=='Other rare')
        ''')

    def test_opt_in_zone_search_uses_current_map_and_pages_all_zone_rares(self):
        addon.QuestTargetsTests.setUp(self)
        self.lua.execute('''
            GetBuildInfo=function() return '1.60.1','','',16001 end
            RegisterStateDriver=function() end
            RSOverlayMixin={OnAcquired=function() end}
            local rs={db={char={overlayActive={[11]={}}},global={
                rares_found={[11]=true},rare_names={deDE={[11]='Marked rare'}}
            }}}
            local originalLibStub=LibStub
            LibStub=function(name,silent)
                if name=='AceAddon-3.0' then return {GetAddon=function() return rs end} end
                return originalLibStub(name,silent)
            end
            local mapID, reads, now=20,0,0
            GetTime=function() return now end
            C_Map=C_Map or {}
            C_Map.GetBestMapForUnit=function(unit)
                assert(unit=='player')
                return mapID
            end
            DropdownButtonMixin={SetupMenu=function(self,generator)
                assert(not self:IsShown())
                self.menuGenerator=generator
            end}
            local expected={}
            for i=1,11 do expected[i]='Zone rare '..string.char(64+i)..string.rep('x',25) end
            RSWorldMapButtonMixin={SetupMenu=function(self)
                DropdownButtonMixin.SetupMenu(self,function(owner,root)
                    reads=reads+1
                    root:SetTag('MENU_WORLD_MAP_RARESCANNER')
                    local npcs=root:CreateButton('NPCs')
                    local filter=npcs:CreateButton('Filter NPCs')
                    local function action() error('Menu action was called') end
                    local function item(id,name)
                        filter:CreateCheckbox('|Ticon:18|t |A:atlas:18|a '..name..' ('..id..')',
                            action,action):SetEnabled(action)
                    end
                    local current=owner:GetParent():GetMapID()
                    if current==20 then
                        for id,name in ipairs(expected) do item(id,name) end
                        item(89,expected[1])
                        item(90,'Unsafe/Name')
                        filter:CreateCheckbox('|Ticon:18|t 91',action,action)
                    elseif current==21 then item(55,'Other zone rare')
                    elseif current==100001 then item(3586,'Miner Johnson')
                    elseif current==31 then item(101,'Upstairs rare')
                    elseif current==32 then item(102,'Downstairs rare')
                    elseif current==100011 then item(105,'Main gate rare')
                    elseif current==100036 then item(106,'Service entrance rare')
                    end
                    root:CreateButton('Containers'):CreateButton('Filter'):CreateCheckbox('Chest (44)',action,action)
                    root:CreateButton('Events'):CreateButton('Filter'):CreateCheckbox('Event (45)',action,action)
                end)
            end}
            boot()
            local b=NS.RareScanner.markButton
            local option=NS.UI.settings.rareScannerZoneToggle
            assert(not option:GetChecked() and reads==0 and b.attributes.macrotext1=='/targetexact Marked rare\\n/cleartarget [dead]')
            option.scripts.OnClick()
            assert(NS.app.db.rareScannerZone==true and reads==1 and b:GetAlpha()==1)
            assert(#b.markedNames==#expected)
            local searched={}
            for i=1,#expected do
                tick()
                b.scripts.PreClick(b,'LeftButton',false)
                local macro=b.attributes.macrotext1
                assert(#macro<=NS.Core.MACRO_BYTES and not macro:find('Marked rare',1,true))
                for _,name in ipairs(expected) do
                    if macro:find(name,1,true) then searched[name]=true end
                end
            end
            for _,name in ipairs(expected) do assert(searched[name], name) end
            assert(reads==1)
            mapID=21
            combat=true
            tick()
            assert(reads==1)
            combat=false
            tick()
            assert(reads==2 and b.attributes.macrotext1=='/targetexact Other zone rare\\n/cleartarget [dead]')
            mapID=22
            b.scripts.PreClick(b,'LeftButton',false)
            assert(b:IsShown() and b:GetAlpha()<1 and b.attributes.macrotext1==nil)
            now=16
            tick()
            assert(reads==4)
            option.scripts.OnClick()
            assert(NS.app.db.rareScannerZone==false and b.attributes.macrotext1=='/targetexact Marked rare\\n/cleartarget [dead]')

            local kind, instanceID='party',36
            GetInstanceInfo=function() return 'Dungeon',kind,1,'Normal',5,0,false,instanceID end
            Enum.UIMapType={Zone=3,Dungeon=4}
            C_Map.GetMapInfo=function(id)
                return {mapType=id==20 and Enum.UIMapType.Zone or Enum.UIMapType.Dungeon}
            end
            C_Map.GetMapGroupID=function(id) return (id==31 or id==32) and 8 or nil end
            C_Map.GetMapGroupMembersInfo=function(id)
                assert(id==8)
                return {{mapID=31},{mapID=32}}
            end
            mapID=nil
            option.scripts.OnClick()
            assert(b.attributes.macrotext1=='/targetexact Miner Johnson\\n/cleartarget [dead]')
            mapID=20
            tick()
            assert(b.attributes.macrotext1=='/targetexact Miner Johnson\\n/cleartarget [dead]')
            mapID=31
            tick()
            local names={}
            for _,name in ipairs(b.markedNames) do names[name]=true end
            assert(#b.markedNames==3 and names['Upstairs rare'] and names['Downstairs rare'] and names['Miner Johnson'])
            mapID=nil
            instanceID=329
            b.scripts.PreClick(b,'LeftButton',false)
            assert(#b.markedNames==2 and b.attributes.macrotext1:find('Main gate rare',1,true)
                and b.attributes.macrotext1:find('Service entrance rare',1,true))
            kind, mapID='none',21
            tick()
            assert(b.attributes.macrotext1=='/targetexact Other zone rare\\n/cleartarget [dead]')
        ''')

    def test_bar_button_tracks_active_world_map_rare_and_checks_again_on_click(self):
        addon.QuestTargetsTests.setUp(self)
        self.lua.execute('''
            GetBuildInfo=function() return '1.60.1','','',16001 end
            RegisterStateDriver=function(frame,state,condition)
                frame.stateDrivers=frame.stateDrivers or {}
                frame.stateDrivers[state]=condition
            end
            RSOverlayMixin={OnAcquired=function() end}
            local rs={db={char={overlayActive={}},global={}}}
            local ace={GetAddon=function(_,name) if name=='RareScanner' then return rs end end}
            local originalLibStub=LibStub
            LibStub=function(name, silent)
                if name=='AceAddon-3.0' then return ace end
                return originalLibStub(name, silent)
            end
            boot()
            local b=NS.RareScanner.markButton
            assert(b:IsShown() and b:GetAlpha()<1 and b.attributes.macrotext1==nil)
            assert(NS.UI.settings.rareScannerToggle.caption:GetText()=='Show RareScanner button')
            local panel=NS.UI.settings
            local command='CLICK QuestTargetsRareScannerMark:LeftButton'
            assert(GetBindingKey(command)==nil and b.clicks[1]=='AnyUp')
            assert(panel.rareScannerHotkey.enabled and panel.rareScannerHotkey2.enabled)
            panel.rareScannerHotkey.scripts.OnClick(panel.rareScannerHotkey)
            panel.rareScannerHotkey.scripts.OnKeyDown(panel.rareScannerHotkey,'R')
            panel.rareScannerHotkey2.scripts.OnClick(panel.rareScannerHotkey2)
            panel.rareScannerHotkey2.scripts.OnKeyDown(panel.rareScannerHotkey2,'T')
            local first,second=GetBindingKey(command)
            assert(first=='R' and second=='T' and GetBindingAction('T')==command)
            assert(panel.rareScannerHotkey:GetText()=='R' and panel.rareScannerHotkey2:GetText()=='T')
            local applyCombatState=assert(loadstring('return function(self,newstate) '
                .. b:GetAttribute('_onstate-qtcombat') .. ' end'))()
            assert(b.stateDrivers.qtcombat=='[combat] combat; ready')
            assert(not b.stateDrivers.visibility and b.parent==UIParent)
            local function macroHas(name)
                return (b.attributes.macrotext1 or ''):find(name,1,true)
            end
            local function mark(id, name, isNpc, group)
                rs.db.char.overlayActive[id]={timestamp=100}
                local poi={entityID=id,name=name,isNpc=isNpc}
                RSOverlayMixin:OnAcquired(0,0,0,0,0,
                    group and poi or {POI=poi}, group)
                tick()
            end
            mark(11,'Singer',true)
            assert(b:IsShown() and b:GetAlpha()==1 and macroHas('Singer'))
            assert(b.barAnchor==NS.UI.master)
            NS.UI.settings.rareScannerToggle.scripts.OnClick()
            assert(not b:IsShown() and b:GetAttribute('macrotext1')==nil and GetBindingAction('T')==command)
            NS.UI.settings.rareScannerToggle.scripts.OnClick()
            assert(b:IsShown())
            mark(5,'Other rare',true,{})
            mark(99,'A chest',false)
            assert(macroHas('Other rare') and macroHas('Singer') and not macroHas('A chest'))
            rs.db.char.overlayActive[5]=nil
            applyCombatState(b,'combat')
            combat=true
            b.scripts.PreClick(b,'LeftButton',false)
            assert(b:IsShown() and b.barAnchor==NS.UI.master)
            assert(not b:GetAttribute('type1') and macroHas('Other rare'))
            combat=false
            applyCombatState(b,'ready')
            b.scripts.PreClick(b,'LeftButton',false)
            assert(b:IsShown() and b:GetAttribute('type1')=='macro')
            assert(macroHas('Singer') and not macroHas('Other rare'))
            units.target={name='Singer'}
            b.scripts.PreClick(b,'LeftButton',false)
            assert(b.attributes.macrotext1==nil, 'a single-name list must also keep the target')
            units.target.player=true
            b.scripts.PreClick(b,'LeftButton',false)
            assert(macroHas('Singer'), 'a player with the same name must not block the search')
            units.target={name='Singer',dead=true}
            b.scripts.PreClick(b,'LeftButton',false)
            assert(b.attributes.macrotext1:find('/cleartarget [dead]',1,true),
                'a single unmarked target must also discard corpses')
            units.target=nil
            plate('Singer','','')
            C_Ping={SendMacroPing=function() end}
            local markers={[2]='/tm ', [3]='/ping '}
            for mode=1,3 do
                NS.app.db.targetFeedback={rare=mode}
                b.scripts.PreClick(b,'LeftButton',false)
                local macro=b.attributes.macrotext1
                assert(macro:find('/targetexact [nocombat] Singer',1,true))
                assert(macro:find('/cleartarget [dead]',1,true) and #macro<=NS.Core.MACRO_BYTES)
                if markers[mode] then assert(macro:find(markers[mode],1,true)) end
            end
            NS.app.db.targetFeedback=nil
            nameplates, units.nameplate1={}, nil
            rs.db.char.overlayActive[11]=nil
            b.scripts.PreClick(b,'LeftButton',false)
            assert(b.attributes.macrotext1==nil)
            tick()
            assert(b:IsShown() and b:GetAlpha()<1)
            local expected={}
            for i=1,11 do
                expected[i]='Marked rare '..string.char(64+i)..string.rep('x',25)
                mark(i,expected[i],true)
            end
            local attempted={}
            b.scripts.PreClick(b,'LeftButton',false)
            local nextPage=b.markIndex
            units.target={name=expected[1]}
            b.scripts.PreClick(b,'LeftButton',false)
            assert(b.attributes.macrotext1==nil and b.markIndex==nextPage, 'a repeat click must keep the selected rare')
            units.target.friendly=true
            b.scripts.PreClick(b,'LeftButton',false)
            assert(b.attributes.macrotext1==nil and b.markIndex==nextPage, 'a listed friendly NPC is also a valid rare')
            units.target.dead=true
            b.scripts.PreClick(b,'LeftButton',false)
            assert(b.attributes.macrotext1 and b.markIndex~=nextPage, 'a dead rare must not block the search')
            units.target=nil
            for i=1,11 do
                tick()
                b.scripts.PreClick(b,'LeftButton',false)
                assert(#b.attributes.macrotext1<=NS.Core.MACRO_BYTES)
                for _,name in ipairs(expected) do
                    if macroHas(name) then attempted[name]=true end
                end
            end
            for _,name in ipairs(expected) do assert(attempted[name], name) end
        ''')

    def setUp(self):
        addon.QuestTargetsTests.setUp(self)
        self.lua.execute('''
            GetBuildInfo=function() return '1.60.1','','',16001 end
            function RegisterStateDriver(frame, state, condition)
                frame.stateCondition=condition
            end
            local methods=getmetatable(Minimap).__index
            function methods:GetParent() return self.parent end
            function methods:GetChildren() return unpack(self.children or {}) end
            RSMinimapPinMixin={OnEnter=function(self) self.tooltipShown=true end}
            pins={AddMinimapIconMap=function() end}
            LibStub=function(name, silent) if name=='HereBeDragons-Pins-2.0' then return pins end end
            function rarePin(name, npc)
                local pin=CreateFrame('Frame',nil,Minimap)
                pin.POI={name=name,isNpc=npc,entityID=123}
                pin.OnEnter=RSMinimapPinMixin.OnEnter
                pin:SetScript('OnEnter',pin.OnEnter)
                pin:SetScript('OnLeave',function(self) self.tooltipShown=false end)
                return pin
            end
        ''')
        source = addon.ROOT / 'QuestTargets' / 'RareScanner.lua'
        self.assertTrue(source.exists(), 'RareScanner integration is missing')
        self.lua.execute('assert(loadstring(...))("QuestTargets", NS)', source.read_text(encoding='utf-8'))

    def test_hover_prepares_exact_target_and_recycled_pin_uses_new_name(self):
        self.lua.execute('''
            local pin=rarePin('Hogger',true)
            Minimap.children={pin}
            NS.RareScanner.Initialize()
            pin.scripts.OnEnter(pin)
            local b=NS.RareScanner.button
            assert(b:IsShown() and b.attributes.macrotext1=='/targetexact Hogger')
            assert(b.secure and b.parent~=pin and not pin.protected)
            assert(b.attributes['shift-type1']=='' and b.attributes['ctrl-type1']=='')
            pin.POI={name='Old Grizzlegut',isNpc=true,entityID=124}
            b.scripts.OnUpdate(b,0.1)
            assert(not b:IsShown())
            pin.scripts.OnEnter(pin)
            assert(b.attributes.macrotext1=='/targetexact Old Grizzlegut')
        ''')

    def test_ignores_treasure_unsafe_names_and_combat(self):
        self.lua.execute('''
            local pin=rarePin('Chest',false)
            Minimap.children={pin}
            NS.RareScanner.Initialize()
            local b=NS.RareScanner.button
            pin.scripts.OnEnter(pin)
            assert(not b:IsShown())
            pin.POI={isNpc=true,name='Hogger\\n/cast Fireball'}
            pin.scripts.OnEnter(pin)
            assert(not b:IsShown())
            combat=true
            pin.POI={isNpc=true,name='Hogger'}
            pin.scripts.OnEnter(pin)
            assert(not b:IsShown())
            combat=false
            pin.scripts.OnEnter(pin)
            assert(b:IsShown())
            assert(b.parent.stateCondition=='[combat] hide; show')
            pin:Hide()
            b.scripts.OnUpdate(b,0.1)
            assert(not b:IsShown())
        ''')

    def test_new_pins_are_hooked_and_other_addon_pins_are_ignored(self):
        self.lua.execute('''
            NS.RareScanner.Initialize()
            local pin=rarePin('Hogger',true)
            pins:AddMinimapIconMap({},pin)
            pin.scripts.OnEnter(pin)
            assert(NS.RareScanner.button:IsShown())
            NS.RareScanner.button.scripts.OnLeave(NS.RareScanner.button)
            local other=rarePin('Other',true)
            other.OnEnter=function() end
            other:SetScript('OnEnter',other.OnEnter)
            pins:AddMinimapIconMap({},other)
            other.scripts.OnEnter(other)
            assert(not NS.RareScanner.button:IsShown())
        ''')

    def test_combat_does_not_mutate_visible_button_or_protect_source_pin(self):
        self.lua.execute('''
            local pin=rarePin('Hogger',true)
            Minimap.children={pin}
            NS.RareScanner.Initialize()
            pin.scripts.OnEnter(pin)
            local b=NS.RareScanner.button
            combat=true
            pin.POI={isNpc=true,name='Different rare'}
            b.scripts.OnUpdate(b,0.1)
            b.scripts.OnLeave(b)
            pin:Hide()
            assert(b.attributes.macrotext1=='/targetexact Hogger')
            assert(not pin.protected and not Minimap.protected)
            combat=false
            for _, frame in ipairs(frames) do
                if frame.events.PLAYER_REGEN_ENABLED and frame.scripts.OnEvent then
                    frame.scripts.OnEvent(frame,'PLAYER_REGEN_ENABLED')
                end
            end
            assert(not b:IsShown() and b.attributes.macrotext1==nil)
        ''')

    def test_other_clients_and_missing_rarescanner_do_not_create_button(self):
        self.lua.execute('''
            GetBuildInfo=function() return '12.1.5','','',120105 end
            NS.RareScanner.Initialize()
            assert(NS.RareScanner.button==nil)
            GetBuildInfo=function() return '1.60.1','','',16001 end
            local mixin=RSMinimapPinMixin
            RSMinimapPinMixin=nil
            NS.RareScanner.Initialize()
            assert(NS.RareScanner.button==nil)
            RSMinimapPinMixin=mixin
            NS.RareScanner.Initialize()
            assert(NS.RareScanner.button)
        ''')

    def test_click_pulses_immediately_for_both_target_results_and_fades(self):
        self.lua.execute('''
            local pin=rarePin('Hogger',true)
            Minimap.children={pin}
            NS.RareScanner.Initialize()
            pin.scripts.OnEnter(pin)
            local button=NS.RareScanner.button
            local pulse=NS.RareScanner.feedback
            assert(not pulse:IsShown())
            units.target={name='Hogger'}
            button.scripts.PostClick(button,'LeftButton',false)
            assert(pulse:IsShown() and not pulse.text)
            local initialWidth, initialAlpha=pulse:GetWidth(), pulse:GetAlpha()
            pulse.scripts.OnUpdate(pulse,0.2)
            assert(pulse:GetWidth()>initialWidth and pulse:GetAlpha()<initialAlpha)
            units.target=nil
            button.scripts.PostClick(button,'LeftButton',false)
            assert(pulse:IsShown() and pulse:GetWidth()==initialWidth)
            button.scripts.OnLeave(button)
            pulse.scripts.OnUpdate(pulse,0.5)
            assert(not pulse:IsShown())
        ''')

    def test_native_minimap_click_can_pulse_on_a_rare_without_a_hover_event(self):
        self.lua.execute('''
            local pin=rarePin('Singer',true)
            local chest=rarePin('Chest',false)
            Minimap.children={pin,chest}
            local nativeClicks=0
            Minimap:SetScript('OnMouseUp',function() nativeClicks=nativeClicks+1 end)
            NS.RareScanner.Initialize()
            local pulse=NS.RareScanner.feedback
            Minimap.scripts.OnMouseUp(Minimap,'LeftButton')
            assert(not pulse:IsShown() and nativeClicks==1)
            chest.mouseOver=true
            Minimap.scripts.OnMouseUp(Minimap,'LeftButton')
            assert(not pulse:IsShown())
            chest.mouseOver=false
            pin.mouseOver=true
            Minimap.scripts.OnMouseUp(Minimap,'RightButton')
            assert(not pulse:IsShown())
            Minimap.scripts.OnMouseUp(Minimap,'LeftButton')
            assert(pulse:IsShown() and nativeClicks==4)
            assert(NS.RareScanner.button:GetAttribute('macrotext1')=='/targetexact Singer')
        ''')

    def test_modifier_right_down_and_combat_clicks_do_not_pulse(self):
        self.lua.execute('''
            local pin=rarePin('Hogger',true)
            Minimap.children={pin}
            NS.RareScanner.Initialize()
            pin.scripts.OnEnter(pin)
            local b=NS.RareScanner.button
            assert(b.scripts.PostClick, 'missing click result feedback')
            b.scripts.PostClick(b,'RightButton',false)
            b.scripts.PostClick(b,'LeftButton',true)
            shiftDown=true; b.scripts.PostClick(b,'LeftButton',false); shiftDown=false
            ctrlDown=true; b.scripts.PostClick(b,'LeftButton',false); ctrlDown=false
            altDown=true; b.scripts.PostClick(b,'LeftButton',false); altDown=false
            combat=true; b.scripts.PostClick(b,'LeftButton',false); combat=false
            flush()
            assert(not NS.RareScanner.feedback:IsShown())
        ''')


if __name__ == '__main__':
    unittest.main()
