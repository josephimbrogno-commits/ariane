# run_bnaif.ps1 — variante B-NAÏF : RAG natif avec des notes naïves (appartenance non datée, sorties
# jamais enregistrées, sources non étiquetées). Montre le « confidently wrong » que C évite par construction.
$ErrorActionPreference = "Continue"
$env:OLLAMA_API_KEY = "ollama-local"
$env:MEMOIRE_SERVICE_URL = "http://127.0.0.1:8077"
$ici = Split-Path -Parent $MyInvocation.MyCommand.Path
$wsMem = "$env:USERPROFILE\.openclaw\workspace\MEMORY.md"

openclaw config set plugins.slots.contextEngine legacy 2>&1 | Out-Null
Set-Content -Path $wsMem -Value (Get-Content "$ici\MEMORY_Bnaif.md" -Raw -Encoding utf8) -Encoding utf8

$qs = Get-Content "$ici\questions.json" -Raw -Encoding utf8 | ConvertFrom-Json
$cibles = @(1, 7, 8, 10, 12)
$res = @{}
foreach ($q in ($qs | Where-Object { $cibles -contains $_.id })) {
  $raw = openclaw agent --local --session-key "bnaif-$($q.id)" --message $q.q 2>&1 | Out-String
  $lignes = $raw -split "`n" | Where-Object {
    $_ -notmatch '^\[|node\.exe|tool policy|CategoryInfo|FullyQualifiedErrorId|^\s*\+|startup stages|trace:|memory\] sync|At line:|stages=|^\s*$'
  }
  $ans = (($lignes | ForEach-Object { $_.Trim() }) -join " ").Trim()
  $res["$($q.id)"] = $ans
  Write-Output "[Q$($q.id)] $ans"
}
openclaw config set plugins.slots.contextEngine memoire-qui-trie 2>&1 | Out-Null
@{ "Bnaif" = $res } | ConvertTo-Json -Depth 5 | Set-Content -Path "$ici\resultats_bnaif.json" -Encoding utf8
Write-Output "=> écrit resultats_bnaif.json"
