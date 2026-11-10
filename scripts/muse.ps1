<#
.SYNOPSIS
  Delegates a task to Muse (OpenCode) and returns only a short summary.
  Opus = orchestrator, Muse = worker. Full logs: .muse/logs/<Name>.log

.EXAMPLE
  .\scripts\muse.ps1 -Name auth-null-fix -Brief .muse\briefs\auth-null-fix.md
  .\scripts\muse.ps1 -Name auth-null-fix -Message "Tests fail at X, fix it"   # continues the same session
  .\scripts\muse.ps1 -Name find-routes -ReadOnly -Message "Where are the API routes defined?"
#>
param(
  [Parameter(Mandatory)][string]$Name,
  [string]$Brief,
  [string]$Message,
  [string]$Model = $(if ($env:MUSE_MODEL) { $env:MUSE_MODEL } else { "opencode-go/muse-spark-1.3-contributor" }),
  [int]$Tail = 40,
  [switch]$ReadOnly,
  [switch]$NewSession
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not $Brief -and -not $Message) { throw "Provide -Brief <file> or -Message <text>." }
$body = if ($Brief) { Get-Content -Raw -Encoding utf8 $Brief } else { "" }
if ($Message) { $body = ($body + "`n`n" + $Message).Trim() }

$mode = if ($ReadOnly) {
  "MODE: READ-ONLY. Do NOT modify, create or delete any files. Investigate and answer only."
} else {
  "MODE: IMPLEMENT. Make the changes directly in the working tree. Do NOT commit, push or switch branches."
}

$footer = @"

---
$mode
When you finish, END your reply with exactly this section (max 25 lines):
REPORT:
- status: DONE | PARTIAL | BLOCKED
- files: <changed files, or none>
- summary: <what you did / what you found>
- checks: <commands you ran (tests/lint/build) and their result>
- questions: <open questions or risks, or none>
"@

$slug = ($Name.ToLower() -replace '[^a-z0-9]', '')
if (-not $slug) { throw "Name must contain letters or digits." }
$session = "ses_muse$slug"
if ($NewSession) { $session += (Get-Date -Format "HHmmss") }

$logDir = Join-Path $root ".muse\logs"
New-Item -ItemType Directory -Force $logDir | Out-Null
$log = Join-Path $logDir "$slug.log"

$ocArgs = @("run", "-m", $Model, "--session", $session, "--title", "muse:$Name", "--auto")
$started = Get-Date
"`n===== $(Get-Date -Format s) | $Name | $session =====`n$body$footer`n----- output -----" | Out-File -Append -Encoding utf8 $log

$prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
$out = & opencode @ocArgs ($body + $footer) 2>&1 | ForEach-Object { "$_" }
$exit = $LASTEXITCODE
$ErrorActionPreference = $prev
$esc = [char]27
$clean = @($out | ForEach-Object { $_ -replace "$esc\[[0-9;]*[A-Za-z]", "" })
$clean | Out-File -Append -Encoding utf8 $log

$secs = [int]((Get-Date) - $started).TotalSeconds
"### muse [$Name] exit=$exit time=${secs}s session=$session log=.muse/logs/$slug.log"
$idx = ($clean | Select-String -Pattern '^\s*REPORT:' | Select-Object -Last 1).LineNumber
if ($idx) { $clean[($idx - 1)..($clean.Count - 1)] | Select-Object -First $Tail }
else { "(no REPORT section - last $Tail lines)"; $clean | Select-Object -Last $Tail }

if (-not $ReadOnly) {
  "### git status"
  git status --short
  "### diff stat"
  git diff --stat
}
exit $exit

