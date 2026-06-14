# run_abc.ps1 — pose les questions aux 3 configs (A nu / B memory-core / C nous) et sauve les réponses.
# Usage : powershell run_abc.ps1 -Etages "1" -Sortie resultats_e1.json
param([string]$Etages = "1,2,3", [string]$Sortie = "resultats.json")

$ErrorActionPreference = "Continue"
$env:OLLAMA_API_KEY = "ollama-local"
$env:MEMOIRE_SERVICE_URL = "http://127.0.0.1:8077"
$ici = Split-Path -Parent $MyInvocation.MyCommand.Path
$wsMem = "$env:USERPROFILE\.openclaw\workspace\MEMORY.md"
$memB = Get-Content "$ici\MEMORY_B.md" -Raw -Encoding utf8
$etagesArr = $Etages.Split(",") | ForEach-Object { [int]$_.Trim() }

# questions (chargées depuis le JSON gelé exporté par verite_terrain)
$questions = Get-Content "$ici\questions.json" -Raw -Encoding utf8 | ConvertFrom-Json
$questions = $questions | Where-Object { $etagesArr -contains $_.etage }

function Set-Config($slot, $memContent) {
  openclaw config set plugins.slots.contextEngine $slot 2>&1 | Out-Null
  Set-Content -Path $wsMem -Value $memContent -Encoding utf8
}

function Get-Answer($question, $sid) {
  $raw = openclaw agent --local --session-key $sid --message $question 2>&1 | Out-String
  $lignes = $raw -split "`n" | Where-Object {
    $_ -notmatch '^\[|node\.exe|tool policy|CategoryInfo|FullyQualifiedErrorId|^\s*\+|startup stages|trace:|memory\] sync|At line:|^\s*$'
  }
  return (($lignes | ForEach-Object { $_.Trim() }) -join " ").Trim()
}

$configs = @(
  @{ nom = "A"; slot = "legacy";            mem = "" },
  @{ nom = "B"; slot = "legacy";            mem = $memB },
  @{ nom = "C"; slot = "memoire-qui-trie";  mem = "" }
)

$resultats = @{}
foreach ($cfg in $configs) {
  Write-Output ">>> CONFIG $($cfg.nom) (contextEngine=$($cfg.slot))"
  Set-Config $cfg.slot $cfg.mem
  $resultats[$cfg.nom] = @{}
  foreach ($q in $questions) {
    $sid = "abc-$($cfg.nom)-$($q.id)"
    $ans = Get-Answer $q.q $sid
    $resultats[$cfg.nom]["$($q.id)"] = $ans
    Write-Output "  [Q$($q.id)] $ans"
  }
}
# restaurer la config par défaut (notre moteur)
Set-Config "memoire-qui-trie" ""
$resultats | ConvertTo-Json -Depth 5 | Set-Content -Path "$ici\$Sortie" -Encoding utf8
Write-Output "=> écrit : $ici\$Sortie"
