param(
    [switch]$Check,
    [string]$Version
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$output = Join-Path $root 'QuestTargets/PatchNotesData.lua'
$locales = @('deDE', 'enUS', 'esES', 'frFR', 'trTR', 'zhCN')
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('-- Generated from CHANGELOG.md and docs/changelog/*.md by tools/update_patch_notes.ps1.')
$lines.Add('local _, NS = ...')
$lines.Add('NS.PatchNotesData = {')

function LuaString([string]$value) {
    '"' + $value.Replace('\', '\\').Replace('"', '\"') + '"'
}

$referenceShape = $null
foreach ($locale in $locales) {
    $relativePath = if ($locale -eq 'deDE') { 'CHANGELOG.md' } else { "docs/changelog/$locale.md" }
    $versions = @{}
    $shape = [System.Collections.Generic.List[string]]::new()
    $previous = $null
    $sections = 0
    $items = 0
    $hasParagraph = $false
    $lines.Add("    $locale = {")
    foreach ($line in [IO.File]::ReadLines((Join-Path $root $relativePath))) {
        if ($line -match '^## (\d+\.\d+\.\d+) . (.+)$') {
            $number = $Matches[1]
            $date = $Matches[2]
            if ($null -ne $previous) {
                if ([version]$number -ge $previous -or $items -eq 0) {
                    throw "$($relativePath): expected a nonempty entry and descending versions near $line"
                }
                $lines.Add('                }},')
                $lines.Add('            }},')
                $shape.Add("items=$items")
            }
            $versions[$number] = $true
            $shape.Add("version=$number")
            $previous = [version]$number
            $lines.Add(('        {{ version = {0}, date = {1}, sections = {{' -f (LuaString $number), (LuaString $date)))
            $sections = 0
            $items = 0
            $hasParagraph = $false
        } elseif ($null -ne $previous -and $line -match '^### (.+)$') {
            if ($sections -gt 0) {
                if ($items -eq 0) { throw "$($relativePath): empty section before $line" }
                $lines.Add('                }},')
                $shape.Add("items=$items")
            }
            $lines.Add(('                {{ title = {0}, items = {{' -f (LuaString $Matches[1])))
            $sections += 1
            $items = 0
            $hasParagraph = $false
        } elseif ($sections -gt 0 -and $line -match '^- (.+)$') {
            if ($hasParagraph) { throw "$($relativePath): bullets must precede the section paragraph." }
            $lines.Add(('                    {0},' -f (LuaString $Matches[1])))
            $items += 1
        } elseif ($items -gt 0 -and -not $hasParagraph -and $line -match '^([^#\s-].*)$') {
            $lines.Add(('                    paragraph = {0},' -f (LuaString $Matches[1])))
            $hasParagraph = $true
            $shape.Add('paragraph')
        } elseif ($null -ne $previous -and $line.Trim()) {
            throw "$($relativePath): unexpected changelog line: $line"
        }
    }
    if (-not $versions.Count -or $items -eq 0) { throw "$($relativePath): no complete final entry." }
    $shape.Add("items=$items")
    $lines.Add('                }},')
    $lines.Add('            }},')
    $lines.Add('    },')
    $signature = $shape -join '|'
    if ($null -eq $referenceShape) { $referenceShape = $signature }
    elseif ($signature -cne $referenceShape) {
        throw "$($relativePath): versions, sections and bullet counts must match CHANGELOG.md."
    }
    if ($Version -and -not $versions.ContainsKey($Version.Split('-')[0])) {
        throw "No entry for $Version in $relativePath"
    }
}
$lines.Add('}')
$result = ($lines -join "`n") + "`n"
if ($Check) {
    if (-not (Test-Path -LiteralPath $output) -or [IO.File]::ReadAllText($output).Replace("`r`n", "`n") -cne $result) {
        throw 'PatchNotesData.lua is out of date. Run tools/update_patch_notes.ps1.'
    }
} else {
    [IO.File]::WriteAllText($output, $result, [Text.UTF8Encoding]::new($false))
}
