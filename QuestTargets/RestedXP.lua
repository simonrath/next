local _, NS = ...
local Core, UI, Proximity = NS.Core, NS.UI, NS.Proximity
local Integration = {}
NS.RestedXP = Integration

local function restedXP()
    if not LibStub then return end
    local ok, ace = pcall(LibStub, "AceAddon-3.0", true)
    if not ok or not ace or type(ace.GetAddon) ~= "function" then return end
    local found, addon = pcall(ace.GetAddon, ace, "RXPGuides", true)
    if found and type(addon) == "table" and addon.RXPFrame
        and type(addon.RXPFrame.activeSteps) == "table"
        and type(addon.GetCreatureName) == "function" then return addon end
end

local function currentNames(rxp, validNames)
    local names, seen, guideFriendlyNames = {}, {}, {}
    local targeting = rxp.targeting
    if targeting and type(targeting.GetCurrentTargets) == "function" then
        local ok, targets, mobs, unitscan = pcall(targeting.GetCurrentTargets)
        if ok and type(targets) == "table" and type(mobs) == "table"
            and type(unitscan) == "table" then
            -- These are the effective lists after RestedXP filters completed or
            -- inactive guide elements. They already contain localized names.
            for _, list in ipairs({unitscan, mobs, targets}) do
                for _, raw in ipairs(list) do
                    local name = Core.SafeName(raw)
                    if name and not seen[name] then
                        seen[name] = true
                        names[#names + 1] = name
                    end
                    if list == targets and name and not validNames[name] then
                        guideFriendlyNames[name] = true
                    end
                end
            end
            return names, guideFriendlyNames
        end
    end
    -- Older RestedXP builds have no public target-list accessor.
    for _, step in ipairs(rxp.RXPFrame.activeSteps) do
        if step.active == true then
            for _, element in ipairs(step.elements or {}) do
                for _, key in ipairs({"unitscan", "mobs", "targets"}) do
                    for _, id in ipairs(element[key] or {}) do
                        local ok, raw = pcall(rxp.GetCreatureName, id)
                        if ok and type(raw) == "string" then
                            local name = Core.SafeName(raw:gsub("^%*", ""))
                            if name then
                                if key == "targets" and not validNames[name] then
                                    guideFriendlyNames[name] = true
                                end
                                if not seen[name] then
                                    seen[name] = true
                                    names[#names + 1] = name
                                end
                            end
                        end
                    end
                end
            end
        end
    end
    return names, guideFriendlyNames
end

-- Polestar's view includes applicability, completion and its chosen NPC.
local function polestarNames(validNames)
    local ps = _G.Polestar
    local engine = ps and ps.Engine
    if type(engine) ~= "table" or type(engine.GetStepIndex) ~= "function"
        or type(engine.GetStepView) ~= "function" then return end
    local ok, index = pcall(engine.GetStepIndex)
    if not ok or type(index) ~= "number" then return {}, {} end
    local got, view = pcall(engine.GetStepView, index, true)
    if not got or type(view) ~= "table" or type(view.goals) ~= "table" then return {}, {} end
    local raw = {}
    if type(engine.GetGuide) == "function" then
        local success, guide = pcall(engine.GetGuide)
        local step = success and type(guide) == "table" and type(guide.steps) == "table" and guide.steps[index]
        if type(step) == "table" and type(step.goals) == "table" then raw = step.goals end
    end
    local friendlyTypes = {accept=true, turnin=true, talk=true, train=true, vendor=true,
        buy=true, auction=true, sethome=true, getfp=true, learn=true}
    local names, friendly, seen, npcIDs, points = {}, {}, {}, {}, {}
    local function addName(raw, isFriendly, explicitFriendly)
        local name = Core.SafeName(raw)
        if name and not seen[name] then
            seen[name] = true
            names[#names + 1] = name
        end
        if name and isFriendly and (explicitFriendly or not validNames[name]) then friendly[name] = true end
    end
    for i, goal in ipairs(view.goals) do
        if type(goal) == "table" and (goal.status == "active" or goal.status == "pending") then
            local source = type(raw[i]) == "table" and raw[i] or {}
            local kind = goal.t
            if kind == "kill" or kind == "collect" or friendlyTypes[kind] then
                local chosen = goal.npc ~= nil or goal.npcName ~= nil
                local id, name
                if chosen then id, name = goal.npc, goal.npcName
                else id, name = source.npc, source.npcName end
                if id and ps.Names and type(ps.Names.Npc) == "function" then
                    local found, localized = pcall(ps.Names.Npc, id)
                    if found and localized then name = localized end
                end
                if not name and kind == "kill" then name = goal.subject or source.target end
                if not name and kind == "collect" and type(goal.source) == "table"
                    and goal.source.kind == "npc" then name = goal.source.name end
                local collectSource = kind == "collect" and type(goal.source) == "table"
                    and goal.source.kind == "npc" and goal.source or nil
                local sourceFriendly = collectSource and collectSource.enemy == false
                local isSource = collectSource and Core.SafeName(name) ~= nil
                    and Core.SafeName(name) == Core.SafeName(collectSource.name)
                addName(name, friendlyTypes[kind] or (sourceFriendly and isSource), sourceFriendly and isSource)
                local safe = Core.SafeName(name)
                if safe and type(id) == "number" and id > 0 then npcIDs[safe] = id end
                if safe and friendlyTypes[kind] and goal.f ~= "e"
                    and type(goal.x) == "number" and type(goal.y) == "number"
                    and (goal.x ~= 0 or goal.y ~= 0) then
                    local point = Proximity.MapPoint(goal.map, goal.x / 100, goal.y / 100)
                    if point then
                        local locations = points[safe] or {}
                        locations[#locations + 1] = point
                        points[safe] = locations
                    end
                end
                if kind == "collect" and type(goal.source) == "table" and goal.source.kind == "npc" then
                    addName(goal.source.also, sourceFriendly, sourceFriendly)
                end
            end
        end
    end
    return names, friendly, npcIDs, points
end

local function readGuide(provider, baseNames)
    if provider == "restedxp" then
        local rxp = restedXP()
        if rxp then return currentNames(rxp, baseNames) end
    elseif provider == "polestar" then
        return polestarNames(baseNames)
    end
end

local function rankedEntry(app, base)
    local db = NS.Database.Provider()
    local entry = {nameList={}, names={}, finisherNames={}, refs={}, mapPoints={}, distanceOrder=true,
        title=NS.L(base and "active" or "restedXPButton"), questID=0}
    local hasSources = false
    local function add(names, friendly, ids, points)
        if not names or #names == 0 then return end
        hasSources = true
        for _, name in ipairs(names) do
            if db and ids then
                if ids[name] then Proximity.Register(db, ids[name], name)
                else Proximity.RegisterName(db, name) end
            end
            if not entry.names[name] then
                entry.nameList[#entry.nameList + 1] = name
                entry.names[name] = true
            end
            if friendly and friendly[name] then entry.finisherNames[name] = true end
            if points and points[name] then
                local combined = entry.mapPoints[name] or {}
                for _, point in ipairs(points[name]) do combined[#combined + 1] = point end
                entry.mapPoints[name] = combined
            end
        end
    end
    local questEntry = UI.master.defaultEntry
    local baseNames = questEntry.names or {}
    local useModules = app.db.masterAllModules ~= false
    if app.db.restedXPIntegration and (not base or useModules) then
        local names, friendly = readGuide("restedxp", baseNames)
        for _, name in ipairs(names or {}) do
            if questEntry.finisherNames and questEntry.finisherNames[name] then friendly[name] = true end
        end
        add(names, friendly, {})
    end
    if base and useModules then
        if app.db.polestarIntegration then add(readGuide("polestar", baseNames)) end
        local itemTree = NS.ItemTree.SearchEntry(app)
        local rareScanner = NS.RareScanner.SearchEntry(app)
        if itemTree then add(itemTree.nameList, itemTree.finisherNames, {}, itemTree.mapPoints) end
        if rareScanner then add(rareScanner.nameList, rareScanner.finisherNames, nil, rareScanner.mapPoints) end
    end
    if base then
        local hasModules = hasSources
        add(base.nameList, base.finisherNames)
        if not hasModules then
            Proximity.Order(entry)
            if not entry.name or not Proximity.EntryDistance(entry, entry.name) then return base end
        end
    end
    if #entry.nameList == 0 then return end
    Proximity.Order(entry)
    return entry
end

local function prepareClick(app, button, base, setting)
    Proximity.Sample()
    local entry = rankedEntry(app, base)
    button.entry = entry
    local settings = Core.TargetFeedbackSettings(app.db, setting)
    Core.SetClickMacro(button, Core.ClickMacro(entry, {}, settings, button, nil, true), app.db)
end

local function prepareCombatMacro(app, button, setting)
    local settings = Core.TargetFeedbackSettings(app.db, setting)
    local entry = button.entry
    local macro
    if entry and Core.ValidCurrentTarget(entry) then
        macro = Core.MarkerMacro(settings, true, entry.finisherNames[Core.SafeName(UnitName("target"))])
    else
        macro = Core.EntryMacro(entry, settings)
    end
    if button:GetAttribute("macrotext1") ~= macro then button:SetAttribute("macrotext1", macro) end
end

local function createButton()
    local button = CreateFrame("Button", "QuestTargetsRestedXPTarget", UIParent, "SecureActionButtonTemplate")
    button:RegisterForClicks("LeftButtonUp")
    button:SetAttribute("type1", "macro")
    button:SetAttribute("useOnKeyDown", false)
    UI.StyleTargetButton(button, 0.28, 0.65, 1)
    button:SetScript("PreClick", function(self, mouseButton, down)
        if mouseButton ~= "LeftButton" or down then return end
        local app = NS.app
        if InCombatLockdown() then
            Core.PrepareDeadTargetSound(self:GetAttribute("macrotext1"), app.db)
        else
            prepareClick(app, self, nil, "restedXP")
        end
    end)
    button:SetScript("PostClick", function(self, mouseButton, down)
        if mouseButton ~= "LeftButton" or down or InCombatLockdown() then return end
        Core.RecordClickResult()
        prepareCombatMacro(NS.app, self, "restedXP")
    end)
    button:SetScript("OnEnter", function(self)
        if not NS.app.db.showTooltips then return end
        GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
        GameTooltip:SetText(NS.L("restedXPButton"))
        GameTooltip:AddLine(NS.L("restedXPSourceTip"), 1, 1, 1, true)
        if not self.entry then GameTooltip:AddLine(NS.L("restedXPNoTarget"), 1, 0.82, 0, true) end
        GameTooltip:Show()
    end)
    button:SetScript("OnLeave", function() GameTooltip:Hide() end)
    button:Hide()
    return button
end

function Integration.Sync(app)
    if InCombatLockdown() or not app.db or not UI.master then return end
    local rxp = app.db.restedXPIntegration and restedXP()
    Integration.active = rxp and true or false
    local polestar = app.db.polestarIntegration and _G.Polestar and type(_G.Polestar.Engine) == "table"
    if rxp or polestar or app.db.itemTreeButton then Proximity.PrepareNameIndex(NS.Database.Provider()) end
    UI.master.entry = rankedEntry(app, UI.master.defaultEntry)
    prepareCombatMacro(app, UI.master, "master")
    if rxp and not Integration.button then Integration.button = createButton() end
    if Integration.button then
        Integration.button.entry = rxp and rankedEntry(app) or nil
        prepareCombatMacro(app, Integration.button, "restedXP")
        if Integration.button:IsShown() ~= Integration.active then Integration.button:SetShown(Integration.active) end
    end
    UI.LayoutTargetButtons(app)
end

function Integration.PreClick(app, button)
    prepareClick(app, button, button.defaultEntry, "master")
end
