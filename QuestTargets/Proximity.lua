local _, NS = ...
local P = {revision = 0}
NS.Proximity = P

local function number(value)
    return NS.Core.Readable(value) and type(value) == "number"
        and value == value and math.abs(value) < math.huge
end

local function reset(db)
    local flavor = db.flavor and db.flavor.name
    if P.provider == db and P.flavor == flavor and P.support == db.Support
        and P.converter == db.EraToForever then return end
    P.provider, P.flavor, P.support, P.converter = db, flavor, db.Support, db.EraToForever
    P.spawns, P.names, P.points, P.distances, P.maps, P.lookedUpNames = {}, {}, {}, {}, nil, nil
    P.revision = P.revision + 1
end

function P.Spawns(db, npcID)
    reset(db)
    if P.spawns[npcID] == nil then
        local ok, value = pcall(db.Npc.Get, npcID, "spawns")
        P.spawns[npcID] = ok and type(value) == "table" and value or false
    end
    return P.spawns[npcID] or nil
end

function P.Register(db, npcID, name)
    reset(db)
    if not P.names[name] then P.names[name] = {} end
    if P.names[name][npcID] then return end
    P.names[name][npcID] = true
    P.Spawns(db, npcID)
    P.distances[name] = nil
    P.revision = P.revision + 1
end

local function mapTable(value)
    if type(value) == "table" then return value end
    -- QuestieDB publishes numeric maps as "return { [area] = map, -- comment }".
    -- Read only that data grammar; never compile or execute provider text.
    if type(value) ~= "string" then return {} end
    local text = value:gsub("%-%-[^\r\n]*", "")
    local body = text:match("^%s*return%s*{(.-)}%s*$")
    if not body then return {} end
    local result = {}
    while not body:match("^%s*$") do
        local area, uiMap, nextIndex = body:match("^%s*%[%s*(%d+)%s*%]%s*=%s*(%d+)%s*()")
        area, uiMap = tonumber(area), tonumber(uiMap)
        -- Zero entries are intentional QuestieDB sentinels, including overrides.
        if not area or not uiMap
            or not number(area) or not number(uiMap) then return {} end
        result[area] = uiMap
        body = body:sub(nextIndex)
        if body ~= "" then
            if not body:match("^[,;]") then return {} end
            body = body:sub(2)
        end
    end
    return result
end

local function maps()
    if P.maps then return P.maps end
    P.maps = {}
    local support = P.support
    if not support or type(support.Get) ~= "function" then return P.maps end
    local ok, zone = pcall(support.Get, "ZoneDB")
    local data = ok and type(zone) == "table" and zone.private
    if type(data) ~= "table" then return P.maps end
    for area, uiMap in pairs(mapTable(data.areaIdToUiMapId)) do P.maps[area] = uiMap end
    for area, uiMap in pairs(mapTable(data.areaIdToUiMapIdOverride)) do P.maps[area] = uiMap end
    return P.maps
end

local function world(mapID, position)
    if not C_Map or type(C_Map.GetWorldPosFromMapPos) ~= "function" then return end
    local continent, point = C_Map.GetWorldPosFromMapPos(mapID, position)
    if number(continent) and point and number(point.x) and number(point.y) then
        return {continent = continent, x = point.x, y = point.y, mapID = mapID}
    end
end

function P.MapPoint(mapID, x, y)
    if not number(mapID) or mapID <= 0 or not number(x) or not number(y)
        or x < 0 or x > 1 or y < 0 or y > 1 or not CreateVector2D then return end
    local ok, point = pcall(function() return world(mapID, CreateVector2D(x, y)) end)
    if ok then return point end
end

local function playerPosition()
    if not C_Map or type(C_Map.GetBestMapForUnit) ~= "function"
        or type(C_Map.GetPlayerMapPosition) ~= "function" then return end
    local mapID = C_Map.GetBestMapForUnit("player")
    if not number(mapID) then return end
    local pos = C_Map.GetPlayerMapPosition(mapID, "player")
    if pos and number(pos.x) and number(pos.y) then return world(mapID, pos) end
end

local function moved(a, b)
    if not a or not b then return a ~= b end
    return a.mapID ~= b.mapID or a.continent ~= b.continent or a.x ~= b.x or a.y ~= b.y
end

function P.MovedFrom(position)
    return moved(position, P.position)
end

-- Only search clicks sample the player position.
function P.Sample()
    local ok, position = pcall(playerPosition)
    if not ok then position = nil end
    local previous = P.position
    if not moved(previous, position) then return false end
    if position and (not previous or position.mapID ~= previous.mapID
        or position.continent ~= previous.continent) then
        -- Retry unavailable map projections when the client enters a new map.
        P.points = {}
    end
    P.position, P.distances = position, {}
    P.revision = P.revision + 1
    return true
end

-- These four Era zone frames differ in Forever. Older providers cannot safely
-- rank their coordinates here without the additive conversion helper.
local changedFrames = {[215]=true, [139]=true, [44]=true, [1519]=true}
local function npcPoints(npcID)
    if P.points[npcID] then return P.points[npcID] end
    local result = {}
    local mapping = maps()
    local interface = GetBuildInfo and select(4, GetBuildInfo())
    local classicEra = type(interface) == "number" and interface >= 11500 and interface < 11600
    for areaID, coords in pairs(P.Spawns(P.provider, npcID) or {}) do
        local mapID = mapping[areaID]
        if number(mapID) and mapID > 0 and type(coords) == "table" and CreateVector2D then
            for _, coord in ipairs(coords) do
                local x, y = type(coord) == "table" and coord[1], type(coord) == "table" and coord[2]
                if number(x) and number(y) and x >= 0 and y >= 0 and x <= 100 and y <= 100 then
                    local ok, point = pcall(function()
                        if P.flavor == "Vanilla" and not classicEra then
                            if type(P.converter) == "function" then x, y = P.converter(areaID, x, y)
                            elseif changedFrames[areaID] then return end
                        end
                        if number(x) and number(y) then
                            return world(mapID, CreateVector2D(x / 100, y / 100))
                        end
                    end)
                    if ok and point then result[#result + 1] = point end
                end
            end
        end
    end
    P.points[npcID] = result
    return result
end

-- Squared world-yard distance; no sqrt and no assumed universal targeting radius.
function P.Distance(name)
    if not P.position or not P.names or not P.names[name] then return end
    if P.distances[name] ~= nil then return P.distances[name] or nil end
    local best, pos = nil, P.position
    for npcID in pairs(P.names[name]) do
        for _, point in ipairs(npcPoints(npcID)) do
            if point.continent == pos.continent then
                local distance = (point.x - pos.x)^2 + (point.y - pos.y)^2
                if not best or distance < best then best = distance end
            end
        end
    end
    P.distances[name] = best or false
    return best
end

local function distanceToPoints(points)
    local pos = P.position
    if not pos or not points then return end
    local best
    for _, point in ipairs(points) do
        if point.continent == pos.continent then
            local distance = (point.x - pos.x)^2 + (point.y - pos.y)^2
            if not best or distance < best then best = distance end
        end
    end
    return best
end

-- The first exact-name lookup can build QuestieDB's full NPC index. Warm
-- current providers in batches so clicking a guide button does not do that work.
local indexState = setmetatable({}, {__mode = "k"})
function P.PrepareNameIndex(db)
    if not db or type(db.Npc.IdsByName) ~= "function" then return end
    local build = db.Npc.BuildNameIndexAsync
    if type(build) ~= "function" or not C_Timer or not C_Timer.After then return true end
    if not indexState[db] then
        indexState[db] = "loading"
        local worker = coroutine.create(build)
        local function advance()
            local ok = coroutine.resume(worker)
            if not ok then indexState[db] = "failed"
            elseif coroutine.status(worker) == "dead" then indexState[db] = "ready"
            else C_Timer.After(0, advance) end
        end
        C_Timer.After(0, advance)
    end
    return indexState[db] == "ready"
end

function P.RegisterName(db, name)
    if not P.PrepareNameIndex(db) then return end
    reset(db)
    if not P.lookedUpNames then P.lookedUpNames = {} end
    if P.lookedUpNames[name] then return end
    local ok, ids = pcall(db.Npc.IdsByName, name)
    if not ok then return end
    P.lookedUpNames[name] = true
    if type(ids) ~= "table" then return end
    for _, npcID in ipairs(ids) do P.Register(db, npcID, name) end
end

function P.EntryDistance(entry, name)
    return distanceToPoints(entry.mapPoints and entry.mapPoints[name]) or P.Distance(name)
end

function P.Order(entry, force)
    if not entry or not entry.nameList or (not force and entry.proximityRevision == P.revision) then return end
    local distances, guideOrder = {}, {}
    for index, name in ipairs(entry.nameList) do
        guideOrder[name] = index
        distances[name] = P.EntryDistance(entry, name) or math.huge
    end
    table.sort(entry.nameList, function(a, b)
        if entry.distanceOrder then
            if distances[a] ~= distances[b] then return distances[a] < distances[b] end
            return guideOrder[a] < guideOrder[b]
        end
        local af = entry.finisherNames and entry.finisherNames[a] == true or false
        local bf = entry.finisherNames and entry.finisherNames[b] == true or false
        if af ~= bf then return not af end
        local az = entry.localNames and entry.localNames[a] == true or false
        local bz = entry.localNames and entry.localNames[b] == true or false
        if az ~= bz then return az end
        if distances[a] ~= distances[b] then return distances[a] < distances[b] end
        return a < b
    end)
    if entry.distanceOrder then entry.name = entry.nameList[1] end
    entry.proximityRevision = P.revision
    entry.proximityKey = table.concat(entry.nameList, "\n")
end
