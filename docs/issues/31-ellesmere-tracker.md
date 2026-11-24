# Issue #31 — EllesmereUI quest tracker

TheVaan_ requested Next buttons beside quests in EllesmereUI's tracker
in the [CurseForge comments](https://www.curseforge.com/wow/addons/questtargets/comments).
The implementation lives on `issue-fixes-1.6.1`.

Use **Show target buttons in EllesmereUI tracker** in Next's options.
It is enabled by default, and unavailable when EllesmereUI's public row API
is missing. The integration requires its Custom Quest Tracker on Forever.
Each quest with known targets gets a compass at the right end of its title.
Left-click uses the existing quest-specific search. Right-click toggles the
same focused quest used by Next and Questie.

The tracker toggles, both spacing controls, button tooltips and the minimap
button option are grouped under **Buttons** in both settings layouts.
Questie and EllesmereUI spacing range from -240 to +240 px and EllesmereUI defaults to 0, preserving
the reserved slot position. Positive values move right, negative values left.
It is disabled when the row API or the tracker-button toggle is unavailable.

The public callback supplies a slot and quest ID. Store those values and
queue a refresh outside combat. The existing one-second poll also follows
tracker movement, hidden rows and recycled quest IDs. Secure buttons stay
parented and anchored to UIParent, using coordinates copied from the slot.
No protected frame is attached to an EllesmereUI frame. A secure combat state
driver hides the overlays during combat; the normal regeneration event rebuilds
their positions and quest actions afterwards. This avoids targeting a previous
quest when the tracker reuses a slot in combat.

References

- [EllesmereUI public row API](https://github.com/EllesmereGaming/EllesmereUI/blob/1a2b149c86777860618dcd85a254097d91602e11/PLUGINS_API.md)
- [RunRowHooks and registration](https://github.com/EllesmereGaming/EllesmereUI/blob/1a2b149c86777860618dcd85a254097d91602e11/EllesmereUIQuestTracker/EllesmereUIQuestTracker_Custom.lua)
- Existing Next `QuestieTracker.Sync`, `Core.ClickMacro`,
  `UI.ToggleFocus`, and the optional tracker settings.

XERJ retrieval was attempted, but its reference corpus had no live index.
The public API and upstream source were read directly. No upstream code was
copied. WoW MCP lint reported no errors and flagged protected frame operations
for review. All addon entry points that mutate these buttons return in combat;
the combat hide itself runs through the secure state driver.

Automated coverage includes API absence, late addon load, registration once,
the setting, independent anchors, click behavior, shared focus, row reuse,
visibility and combat deferral. In-game verification with EllesmereUI remains
pending.
