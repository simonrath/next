# Patchnotes für Quest Targets

Prüfe bei jeder Änderung, was WoW-Spieler davon sehen, anders bedienen oder
beim Update beachten müssen. Ergänze oder überarbeite den Eintrag der Zielversion
im selben Änderungssatz. Reine interne Änderungen brauchen keinen Spielereintrag,
solange sich Bedienung, Verhalten, Voraussetzungen und Leistung für Spieler
nicht merklich ändern.

## Was in einen Eintrag gehört

- **Beginne mit der Hauptänderung.** Nenne den Namen der Funktion oder des
  betroffenen Bedienelements zuerst. Beispiel: **RareScanner Button**.
- **Beschreibe die Wirkung.** Sag, was ein Spieler jetzt tun kann oder was sich
  nach dem Update anders verhält. Bei einer Korrektur nenne den Auslöser und
  das korrigierte Verhalten. Beispiel: „Die **Patchnotes** bleiben nach dem
  automatischen Öffnen sichtbar, bis du das Fenster schließt.“
- **Gib den nötigen Weg an.** Nenne den echten Menüpfad, Buttonnamen oder
  Befehl sowie Linksklick, Rechtsklick oder Tastenkombination, wenn sie für die
  Bedienung wichtig sind. Übernimm die Schreibweise aus dem Spiel.
- **Nenne Voraussetzungen und Grenzen dort, wo sie die Bedienung ändern.**
  Dazu gehören Client, benötigtes Addon, Standardzustand einer neuen Option,
  Verhalten ohne Daten und Einschränkungen im Kampf. Schreibe konkrete Folgen
  statt pauschaler Versprechen über Reichweite oder Kompatibilität.
- **Erkläre erforderliche Schritte beim Update.** Wenn Spieler eine Abhängigkeit
  separat installieren, eine Option einschalten oder eine Belegung anpassen
  müssen, muss das im Eintrag stehen. Beschreibe bei einer entfernten Funktion
  die Auswirkung und gegebenenfalls den Ersatz.
- **Halte die Liste kurz.** Ein Eintrag deckt eine Spielerwirkung ab und hat
  normalerweise ein oder zwei Sätze. Fasse zusammengehörige Änderungen zusammen.
  Ersetze überholte Einträge derselben Vorschau durch den aktuellen Zustand.
  Bereits veröffentlichte Versionen behalten ihre damaligen Angaben.

Lua-Funktionen, Commit-Hashes, Testzahlen und Ursachenanalysen gehören in
Entwicklernotizen. Berichte nur von bestätigten Auswirkungen. Automatisierte
Tests allein belegen kein Verhalten im laufenden WoW-Client.

## Nach Funktionen gruppieren

Verwende pro Version eine Überschrift pro betroffenem Funktionsbereich, zum
Beispiel **RareScanner**, **Zielleiste** oder **Patchnotes-Fenster**. Beginne mit
der wichtigsten Funktion der Version. Sammle alle Änderungen zu diesem Bereich
direkt unter seiner Überschrift. Dazu gehören auch Einstellungen, Tastenkürzel
und Korrekturen für dieselbe Funktion.

- Ordne einen Eintrag nach der betroffenen Funktion ein. Der RareScanner-Hotkey
  steht bei **RareScanner**, der Abstand zwischen den Leistenbuttons bei
  **Zielleiste**.
- Beschreibe neue Funktionen, Verbesserungen und Fehlerkorrekturen im selben
  Themenabschnitt. Benenne den sichtbaren Effekt im Listenpunkt.
- Führe jeden Punkt einmal auf. Bei Überschneidungen wähle den Bereich, in dem
  Spieler die Änderung am ehesten suchen.
- Behalte die Reihenfolge der Themen und die Zuordnung der Punkte in allen
  sechs Sprachen bei. Bereits veröffentlichte Einträge behalten ihre Struktur.

## Format und Ablage

| Ort | Inhalt |
| --- | --- |
| [`CHANGELOG.md`](../CHANGELOG.md) | Deutsche Spielerchronik und Ausgangsfassung für das Fenster im Spiel. |
| [`docs/changelog/`](changelog) | Vollständige Übersetzungen für Englisch (`enUS`), Spanisch (`esES`), Französisch (`frFR`), Türkisch (`trTR`) und vereinfachtes Chinesisch (`zhCN`). |
| `docs/curseforge/<version>.md` | Englische Spielerhinweise für die jeweilige Veröffentlichung. Inhalt und Einschränkungen mit der englischen Ingame-Fassung abgleichen. |
| `docs/releases/<version>.md` | Technischer Hintergrund und Verifikation der jeweiligen Veröffentlichung. |

Im Changelog steht die neueste Version oben. Das Format bleibt mit dem
Ingame-Generator kompatibel. Nutze `## x.y.z – Vorschau` für die laufende
Vorschau und `## x.y.z – TT.MM.JJJJ` für Veröffentlichungen. Eine Themenüberschrift
steht als `### Funktionsbereich` direkt unter der Version.
Jeder Listenpunkt beginnt mit `- ` und steht im Quelltext auf einer Zeile.
Nutze `**Fettdruck**` sparsam für die Hauptfunktion, konkrete UI-Namen und
wichtige Menüpfade. Im Spiel erscheint diese Hervorhebung goldfarben.
Der Text soll auch ohne Farbe klar sein. Im Versionsblock funktionieren
Rubriken, einfache Listen, Fettdruck und ein eigener Absatz nach der Liste einer Rubrik funktionieren.
Setze einen Dank in diesen Absatz und trenne ihn mit einer Leerzeile von der Liste. Weitere Markdown-Formatierung wird
im Spiel nicht aufbereitet.

Pflege alle Sprachfassungen im selben Änderungssatz. Versionen, Reihenfolge,
Rubriken und Anzahl der Punkte pro Rubrik müssen übereinstimmen. Übersetze
Überschriften und Text für die jeweilige Sprache. Behalte Addon-Namen und
Slash-Befehle bei und verwende die tatsächlich angezeigten Namen aus
`QuestTargets/Locale.lua`. Übertrage auch Hinweise zu Voraussetzungen und
Grenzen. Der Generator prüft die Struktur. Ob die Aussagen übereinstimmen,
prüfst du beim Schreiben.

```markdown
## 1.7.0 – Vorschau

### RareScanner
- **Weltkarte:** Markiere einen Rare per Linksklick und suche ihn über den violetten **RareScanner Button**.
- Unter **Tastenkürzel → RareScanner-Rares anvisieren** kannst du zwei Tasten für die Suche belegen.

### Zielleiste
- Unter **Buttons → Zielleiste** kannst du **Bronzerahmen anzeigen** und **Trennlinien anzeigen** getrennt einschalten.

### Patchnotes-Fenster
- Das Fenster bleibt nach dem automatischen Öffnen sichtbar, bis du es schließt.
```

## Vor dem Abschluss einer Änderung

1. Prüfe den Eintrag gegen das tatsächliche Verhalten. Sind Nutzen, Bedienung
   und gegebenenfalls Client, Abhängigkeit oder Update-Schritt klar?
2. Stelle den wichtigsten Funktionsbereich an den Anfang. Prüfe, ob alle
   zusammengehörigen Punkte unter derselben Überschrift stehen. Entferne
   doppelte Punkte und überholte Zwischenstände derselben Version.
3. Gleiche alle sechs Fassungen ab und führe danach den Generator aus. Die erzeugte
   Datei `QuestTargets/PatchNotesData.lua` gehört zur selben Änderung.

   ```powershell
   ./tools/update_patch_notes.ps1
   ./tools/update_patch_notes.ps1 -Check -Version 1.7.0
   ```

   Setze bei `-Version` die jeweilige Zielversion ein. Der Paketbau prüft
   automatisch, ob diese Version vorhanden und die erzeugte Datei aktuell ist.
4. Gleiche vor dem Taggen die englischen CurseForge-Notizen mit der
   englischen Ingame-Fassung ab. Prüfe besonders Bezeichnungen, unterstützte
   Clients und nötige Installationsschritte.

## Grundlagen

- [Keep a Changelog](https://keepachangelog.com/en/2.0.0/) für eine nach Version
  geordnete Auswahl relevanter Änderungen. Quest Targets verwendet das eigene
  deutsche Format, das der Ingame-Generator liest.
- [Blizzards WoW-Patchnotes für 12.1.5](https://worldofwarcraft.blizzard.com/en-us/news/24304162/)
  als Beispiel für konkrete Bedienhinweise und nachvollziehbare Fehlerkorrekturen.
- [Google Developer Documentation Style Guide](https://developers.google.com/style/highlights)
  für aktive Sprache, klare Listen und Hervorhebung von UI-Elementen.
