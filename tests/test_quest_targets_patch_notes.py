import unittest
import test_quest_targets as addon


class PatchNotesTests(unittest.TestCase):
    setUp = addon.QuestTargetsTests.setUp

    def test_skip_automatic_notes_persists_across_updates_and_can_be_reversed(self):
        self.lua.execute('''
            local version='1.7.3'
            GetAddOnMetadata=function() return version end
            boot()
            local panel=QuestTargetsPatchNotes
            local toggle=panel.autoOpenToggle
            assert(panel:IsShown() and not toggle:GetChecked())
            toggle:SetChecked(true); toggle.scripts.OnClick(toggle)
            panel:Hide()
            version='1.7.4'; NS.PatchNotes.OnLogin(); flush()
            assert(not panel:IsShown() and QuestTargetsNewsDB.seenVersion=='1.7.3')
            NS.PatchNotes.Open()
            assert(panel:IsShown() and toggle:GetChecked())
            toggle:SetChecked(false); toggle.scripts.OnClick(toggle)
            panel:Hide()
            version='1.7.5'; NS.PatchNotes.OnLogin(); flush()
            assert(panel:IsShown() and QuestTargetsNewsDB.seenVersion=='1.7.5')
        ''')

    def test_complete_history_updates_in_place_for_each_language(self):
        self.lua.execute('''
            GetAddOnMetadata=function() return '1.7.0' end
            boot()
            local panel=QuestTargetsPatchNotes
            local expected={
                enUS={'Targeting bar','Patch Notes window'},
                deDE={'Zielleiste','Patchnotes-Fenster'},
                esES={'Barra de objetivos','Ventana de notas del parche'},
                frFR={'Barre de ciblage','Fenêtre des notes de mise à jour'},
                trTR={'Hedef çubuğu','Yama notları penceresi'},
                zhCN={'目标按钮栏','更新说明窗口'},
            }
            local firstCard
            for _,locale in ipairs(NS.LANGUAGES) do
                NS.app.db.language=locale
                NS.UI.ApplyLanguage(NS.app)
                assert(panel:IsShown() and #panel.cards==26)
                assert(panel.cards[26].heading:GetText()=='1.0.11')
                firstCard=firstCard or panel.cards[1]
                assert(panel.cards[1]==firstCard)
                local sections=firstCard.sections
                assert(#sections==3 and sections[1].heading:GetText()=='RareScanner', locale)
                assert(sections[2].heading:GetText()==expected[locale][1], locale)
                assert(sections[3].heading:GetText()==expected[locale][2], locale)
                assert(sections[3].notes:GetText():find(' > ', 1, true), locale)
                assert(not sections[3].notes:GetText():find('→', 1, true), locale)
                for index, count in ipairs({7,3,1}) do
                    local notes=sections[index].notes:GetText()
                    local _, bullets=notes:gsub('• ', '')
                    assert(bullets==count and notes:find('|cffffd100',1,true), locale)
                    assert(not notes:find('**',1,true))
                end
            end
        ''')

    def test_uses_native_minimal_scrollbar_when_available(self):
        self.lua.execute('''
            C_XMLUtil={GetTemplateInfo=function(name) if name=='MinimalScrollBar' then return {} end end}
            NS.PatchNotes.Open()
            local panel=QuestTargetsPatchNotes
            assert(panel.scrollbar.template=='MinimalScrollBar')
            panel.scroll.scripts.OnMouseWheel(panel.scroll,-1)
            assert(panel.scroll.verticalScroll==44 and panel.scrollbar.percentage>0)
            panel.scrollbar.scrollCallback(1)
            assert(panel.scroll.verticalScroll==panel.scrollRange)
        ''')

    def test_update_opens_once_and_manual_view_stays_open(self):
        self.lua.execute('''
            local version='1.7.0-preview.20261119T010000Z'
            GetAddOnMetadata=function(_, key) if key=='Version' then return version end end
            boot()
            assert(NS.PatchNotes, 'missing patch notes')
            local panel=QuestTargetsPatchNotes
            assert(panel and panel:IsShown())
            assert(panel.template=='DefaultPanelFlatTemplate')
            assert(panel.close.template=='UIPanelCloseButtonNoScripts')
            assert(panel.cards[1].template=='InsetFrameTemplate')
            assert(QuestTargetsNewsDB.seenVersion==version)
            assert(panel.cards[1].heading:GetText()=='1.7.0')
            assert(panel.cards[#panel.cards].heading:GetText()=='1.0.11')
            panel.scroll.scripts.OnMouseWheel(panel.scroll,-1)
            assert(panel.scroll.verticalScroll>0)
            assert(panel.scripts.OnUpdate==nil, 'automatically opened notes must stay open')
            flush()
            assert(panel:IsShown())
            panel.close.scripts.OnClick()
            assert(not panel:IsShown())
            event('PLAYER_LOGIN')
            event('PLAYER_ENTERING_WORLD')
            flush()
            assert(not panel:IsShown())
            NS.UI.settings.patchNotesButton.scripts.OnClick()
            assert(panel:IsShown())
            assert(panel.scripts.OnUpdate==nil)
            assert(panel.scroll.verticalScroll==0)
        ''')

    def test_auto_open_waits_until_out_of_combat(self):
        self.lua.execute('''
            QuestTargetsNewsDB={seenVersion='1.7.0'}
            GetAddOnMetadata=function() return '1.7.1' end
            event('ADDON_LOADED','QuestTargets')
            combat=true
            event('PLAYER_LOGIN')
            flush()
            assert(not QuestTargetsPatchNotes and QuestTargetsNewsDB.seenVersion=='1.7.0')
            combat=false
            event('PLAYER_REGEN_ENABLED')
            local panel=QuestTargetsPatchNotes
            assert(panel and panel:IsShown() and QuestTargetsNewsDB.seenVersion=='1.7.1')
            assert(panel.cards[1].heading:GetText()=='1.7.1')
            assert(panel.scripts.OnUpdate==nil)
            assert(panel:IsShown())
        ''')
