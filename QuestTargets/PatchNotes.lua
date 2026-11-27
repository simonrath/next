local addonName, NS = ...
local Notes = {}
NS.PatchNotes = Notes

local WIDTH, HEIGHT, CARD_WIDTH = 624, 498, 547
local SCROLL_TOP, SCROLL_BOTTOM = 112, 36
local GREETING_TEXTURE = "Interface\\AddOns\\" .. addonName .. "\\Textures\\PatchNotesGreetings"
local frame, pending

local function autoOpenEnabled()
    return type(QuestTargetsNewsDB) == "table" and QuestTargetsNewsDB.showAutomatic == true
end

local function version()
    local get = C_AddOns and C_AddOns.GetAddOnMetadata or GetAddOnMetadata
    local value = get and get(addonName, "Version")
    return type(value) == "string" and value ~= "" and value or nil
end

local function label(parent, font, x, y)
    local text = parent:CreateFontString(nil, "ARTWORK", font)
    text:SetPoint("TOPLEFT", x, y)
    text:SetJustifyH("LEFT")
    return text
end

local function scrollTo(window, offset)
    local range = window.scrollRange or 0
    offset = math.max(0, math.min(range, offset))
    window.scrollOffset = offset
    window.scroll:SetVerticalScroll(offset)
    if window.minimalScroll then
        window.scrollbar:SetScrollPercentage(range > 0 and offset / range or 0, true)
    else
        window.scrollbar:SetValue(offset)
    end
end

local function createScrollbar(window, scroll)
    local minimal = C_XMLUtil and C_XMLUtil.GetTemplateInfo
        and C_XMLUtil.GetTemplateInfo("MinimalScrollBar") ~= nil
    local bar
    if minimal then
        bar = CreateFrame("EventFrame", nil, window, "MinimalScrollBar")
        bar:SetPoint("TOPLEFT", scroll, "TOPRIGHT", 6, 0)
        bar:SetPoint("BOTTOMLEFT", scroll, "BOTTOMRIGHT", 6, 0)
        bar:RegisterCallback("OnScroll", function(_, position)
            local offset = position * (window.scrollRange or 0)
            window.scrollOffset = offset
            scroll:SetVerticalScroll(offset)
        end, window)
    else
        bar = CreateFrame("Slider", "QuestTargetsPatchNotesScrollBar", window, "UIPanelScrollBarTemplate")
        bar:SetPoint("TOPRIGHT", -24, -SCROLL_TOP - 16)
        bar:SetPoint("BOTTOMRIGHT", -24, SCROLL_BOTTOM + 16)
        bar:SetScript("OnValueChanged", function(_, offset)
            window.scrollOffset = offset
            scroll:SetVerticalScroll(offset)
        end)
        bar:SetValueStep(1)
    end
    window.scrollbar, window.minimalScroll = bar, minimal
    scroll:EnableMouseWheel(true)
    scroll:SetScript("OnMouseWheel", function(_, delta)
        scrollTo(window, (window.scrollOffset or 0) - delta * 44)
    end)
end

local function createGreeting(window, side, inward, left, right)
    local art = window:CreateTexture(nil, "ARTWORK")
    art:SetTexture(GREETING_TEXTURE)
    art:SetTexCoord(left, right, 0, 1)
    art:SetSize(144, 72)
    art:SetPoint(side, window, side, 22 * inward, -23)

    local caption = window:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    caption:SetPoint("CENTER", art, "TOP", 20 * inward, -25)
    caption:SetWidth(80)
    caption:SetJustifyH("CENTER")
    caption:SetTextColor(0.20, 0.09, 0.03)
    caption:SetShadowColor(0, 0, 0, 0)
    return caption
end

local function createWindow()
    local window = CreateFrame("Frame", "QuestTargetsPatchNotes", UIParent, "DefaultPanelFlatTemplate")
    window:SetSize(WIDTH, HEIGHT)
    window:SetPoint("CENTER")
    window:SetFrameStrata("DIALOG")
    window:EnableMouse(true)
    window:SetClampedToScreen(true)
    NineSliceUtil.ApplyLayoutByName(window.NineSlice, "ButtonFrameTemplateNoPortrait")
    window:Hide()
    if UISpecialFrames then table.insert(UISpecialFrames, "QuestTargetsPatchNotes") end

    window.dwarfGreeting = createGreeting(window, "TOPLEFT", 1, 0, 0.5)
    window.murlocGreeting = createGreeting(window, "TOPRIGHT", -1, 0.5, 1)
    window.subtitle = label(window, "GameFontHighlightSmall", 24, -96)

    local scroll = CreateFrame("ScrollFrame", nil, window)
    scroll:SetPoint("TOPLEFT", 24, -SCROLL_TOP)
    scroll:SetPoint("BOTTOMRIGHT", -45, SCROLL_BOTTOM)
    local content = CreateFrame("Frame", nil, scroll)
    content:SetSize(CARD_WIDTH, 1)
    scroll:SetScrollChild(content)
    window.scroll, window.content, window.cards = scroll, content, {}
    createScrollbar(window, scroll)

    local close = CreateFrame("Button", nil, window, "UIPanelCloseButtonNoScripts")
    close:SetSize(20, 20)
    close:SetPoint("TOPRIGHT", -6, -1)
    close:SetScript("OnClick", function() window:Hide() end)
    window.close = close
    window.footer = label(window, "GameFontDisableSmall", 24, -HEIGHT + 23)
    local check = CreateFrame("CheckButton", nil, window, "UICheckButtonTemplate")
    check:SetSize(22, 22)
    check:SetPoint("BOTTOMRIGHT", -19, 7)
    check:SetScript("OnClick", function(self)
        QuestTargetsNewsDB.showAutomatic = not not self:GetChecked()
        if not QuestTargetsNewsDB.showAutomatic then pending = nil end
    end)
    check.caption = check:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
    check.caption:SetPoint("RIGHT", check, "LEFT", -4, 0)
    window.autoOpenToggle = check
    return window
end

local function createCard(parent)
    local card = CreateFrame("Frame", nil, parent, "InsetFrameTemplate")
    card:SetWidth(CARD_WIDTH)
    card.heading = label(card, "GameFontNormalLarge", 16, -12)
    card.date = card:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
    card.date:SetPoint("TOPRIGHT", -16, -16)
    card.sections = {}
    return card
end

local function updateCard(card, entry)
    card.heading:SetText(entry.version)
    card.date:SetText(entry.date)
    local y = 41
    for index, section in ipairs(entry.sections) do
        local row = card.sections[index]
        if not row then
            row = {
                heading = card:CreateFontString(nil, "ARTWORK", "GameFontNormalSmall"),
                notes = card:CreateFontString(nil, "ARTWORK", "GameFontHighlight"),
            }
            row.notes:SetJustifyH("LEFT")
            row.notes:SetWidth(CARD_WIDTH - 32)
            row.notes:SetSpacing(3)
            card.sections[index] = row
        end
        row.heading:SetPoint("TOPLEFT", 16, -y)
        row.heading:SetText(section.title)
        row.heading:Show()
        local notes = row.notes
        notes:SetPoint("TOPLEFT", 16, -y - 17)
        local bullets = "• " .. table.concat(section.items, "\n• ")
        if section.items.paragraph then bullets = bullets .. "\n\n" .. section.items.paragraph end
        -- The native patch notes font may not contain the Unicode right arrow.
        local text = bullets:gsub("→", ">")
        notes:SetText((text:gsub("%*%*(.-)%*%*", "|cffffd100%1|r")))
        notes:Show()
        y = y + 17 + math.ceil(notes:GetStringHeight()) + 11
    end
    for index = #entry.sections + 1, #card.sections do
        card.sections[index].heading:Hide()
        card.sections[index].notes:Hide()
    end
    card:SetHeight(y + 3)
end

local function render(window, installedVersion)
    local locale = NS.LANGUAGES[NS.Language()]
    local base = installedVersion and installedVersion:match("^%d+%.%d+%.%d+")
    if window.locale == locale and window.release == base then return end
    window.locale, window.release = locale, base
    local entries = NS.PatchNotesData[locale] or NS.PatchNotesData.enUS
    local first = 1
    for index, entry in ipairs(entries) do
        if entry.version == base then first = index; break end
    end
    local y = 0
    for index = first, #entries do
        local slot = index - first + 1
        local card = window.cards[slot] or createCard(window.content)
        window.cards[slot] = card
        updateCard(card, entries[index])
        card:SetPoint("TOPLEFT", 0, -y)
        card:Show()
        y = y + card:GetHeight() + 10
    end
    for slot = #entries - first + 2, #window.cards do window.cards[slot]:Hide() end
    local height = math.max(1, y - 10)
    window.content:SetHeight(height)
    local viewport = HEIGHT - SCROLL_TOP - SCROLL_BOTTOM
    window.scrollRange = math.max(0, height - viewport)
    if window.minimalScroll then
        window.scrollbar:SetVisibleExtentPercentage(math.min(1, viewport / height))
        window.scrollbar:SetPanExtentPercentage(math.min(1, 44 / math.max(1, window.scrollRange)))
    else
        window.scrollbar:SetMinMaxValues(0, window.scrollRange)
    end
    window.scrollbar:SetShown(window.scrollRange > 0)
end

local function refreshText(installedVersion)
    frame.TitleContainer.TitleText:SetText(NS.L("title") .. " – " .. NS.L("patchNotes"))
    frame.subtitle:SetText(installedVersion and NS.L("patchNotesVersion"):format(installedVersion) or "")
    frame.dwarfGreeting:SetText(NS.L("patchNotesDwarfGreeting"))
    frame.murlocGreeting:SetText(NS.L("patchNotesMurlocGreeting"))
    frame.footer:SetText(NS.L("patchNotesFooter"))
    frame.autoOpenToggle.caption:SetText(NS.L("patchNotesShowAutomatic"))
    render(frame, installedVersion)
end

function Notes.RefreshLanguage()
    if not frame or not frame:IsShown() then return end
    refreshText(version())
    scrollTo(frame, frame.scrollOffset or 0)
end

function Notes.Open()
    if type(QuestTargetsNewsDB) ~= "table" then QuestTargetsNewsDB = {} end
    if not frame then frame = createWindow() end
    local installedVersion = version()
    frame:SetScale(math.min(1, UIParent:GetWidth() / (WIDTH + 24), UIParent:GetHeight() / (HEIGHT + 24)))
    refreshText(installedVersion)
    frame.autoOpenToggle:SetChecked(autoOpenEnabled())
    scrollTo(frame, 0)
    frame:Show()
    if installedVersion then QuestTargetsNewsDB.seenVersion = installedVersion end
    pending = nil
end

function Notes.TryPending()
    if not autoOpenEnabled() then pending = nil; return end
    if not pending or InCombatLockdown() then return end
    if type(QuestTargetsNewsDB) ~= "table" or QuestTargetsNewsDB.seenVersion ~= pending then
        Notes.Open()
    else
        pending = nil
    end
end

function Notes.OnLogin()
    if not autoOpenEnabled() then return end
    local installedVersion = version()
    if not installedVersion or (type(QuestTargetsNewsDB) == "table"
        and QuestTargetsNewsDB.seenVersion == installedVersion) then return end
    C_Timer.After(2, function()
        pending = installedVersion
        Notes.TryPending()
    end)
end
