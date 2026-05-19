#!/usr/bin/env pwsh
#Requires -Version 7.0
# coding: utf-8
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$Command,

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$KimiAgentFile = Join-Path $RepoRoot "kimi\agents\codex-worker.yaml"

function Show-Usage {
@"
Usage: kodeximi.ps1 <command> [args]

Commands:
  doctor                                  Check environment prerequisites
  init-project <path>                     Scaffold a project workspace
  enable <projectPath>                     Enable taskflow for a project
  disable <projectPath>                    Disable taskflow for a project
  mode <projectPath>                       Print ON/OFF taskflow mode
  new-task <name> [-Project <path>]       Create a task from template
  validate <taskDir>                      Check task folder without invoking Kimi
  run <taskDir> [-TimeoutSeconds <n>]      Execute a task via Kimi CLI
  status <taskDir>                        Read task status
  result <taskDir>                        Display RESULT.md
  review-check <taskDir> [-Project <path>] Summarize evidence and Git review state
  new-batch <name> [-Project <path>]      Create a batch from template
  run-batch <batchDir> [-MaxParallel <n>] Execute a batch
"@
}

function Test-CommandExists { param([string]$Name) $null -ne (Get-Command $Name -ErrorAction SilentlyContinue) }
function Get-NowIso { (Get-Date -Format "o") }
function Resolve-ExistingPathString {
    param([string]$Path, [string]$Kind)
    $resolved = Resolve-Path -LiteralPath $Path -ErrorAction SilentlyContinue
    if (-not $resolved) { throw "$Kind not found: $Path" }
    return $resolved.Path
}
function Save-Json { param($Object, [string]$Path) $Object | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $Path -Encoding UTF8 }
function Load-Json { param([string]$Path) Get-Content -Raw -LiteralPath $Path -Encoding UTF8 | ConvertFrom-Json }

function Invoke-Doctor {
    $issues = @()
    if (-not (Test-CommandExists "kimi")) { $issues += "kimi CLI not found in PATH." }
    if (-not (Test-CommandExists "pwsh")) { $issues += "PowerShell 7 (pwsh) not found in PATH." }
    if (-not (Test-Path -LiteralPath $KimiAgentFile)) { $issues += "Kimi agent file not found at $KimiAgentFile" }
    if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot "templates\task\TASK.md"))) { $issues += "Task template missing." }
    if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot "templates\batch\BATCH_MANIFEST.json"))) { $issues += "Batch template missing." }
    if ($OutputEncoding.WebName -ne "utf-8") { $issues += "OutputEncoding is not UTF-8 (current: $($OutputEncoding.WebName))." }

    if ($issues.Count -eq 0) { Write-Host "doctor: OK" -ForegroundColor Green; return 0 }
    Write-Host "doctor: ISSUES FOUND" -ForegroundColor Red
    foreach ($issue in $issues) { Write-Host "  - $issue" }
    return 1
}

function Invoke-InitProject {
    param([string]$Path)
    if (-not $Path) { Write-Error "init-project requires a path."; return 1 }
    New-Item -ItemType Directory -Path $Path -Force | Out-Null
    $abs = (Resolve-Path -LiteralPath $Path).Path
    New-Item -ItemType Directory -Path (Join-Path $abs "tasks") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $abs "batches") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $abs ".kodeximi") -Force | Out-Null
    Write-Host "init-project: created workspace at $abs" -ForegroundColor Green
    return 0
}

function Invoke-NewTask {
    param([string]$Name, [string]$Project = ".")
    if (-not $Name) { Write-Error "new-task requires a name."; return 1 }
    $projectPath = Resolve-ExistingPathString -Path $Project -Kind "Project path"
    $tasksDir = Join-Path $projectPath "tasks"
    New-Item -ItemType Directory -Path $tasksDir -Force | Out-Null
    $taskDir = Join-Path $tasksDir $Name
    if (Test-Path -LiteralPath $taskDir) { Write-Error "Task already exists: $taskDir"; return 1 }
    New-Item -ItemType Directory -Path $taskDir | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $taskDir "logs") | Out-Null

    $templateDir = Join-Path $RepoRoot "templates\task"
    foreach ($f in @("TASK.md")) {
        $text = Get-Content -Raw -LiteralPath (Join-Path $templateDir $f) -Encoding UTF8
        $text = $text.Replace("{{TASK_NAME}}", $Name).Replace("{{TASK_DIR}}", $taskDir)
        Set-Content -LiteralPath (Join-Path $taskDir $f) -Value $text -Encoding UTF8
    }
    $timestamp = Get-NowIso
    $status = Get-Content -Raw -LiteralPath (Join-Path $templateDir "status.json") -Encoding UTF8
    $status = $status.Replace("{{TASK_NAME}}", $Name).Replace("{{TIMESTAMP}}", $timestamp).Replace("{{AGENT_FILE}}", $KimiAgentFile.Replace("\", "\\"))
    Set-Content -LiteralPath (Join-Path $taskDir "status.json") -Value $status -Encoding UTF8
    Write-Host "new-task: created $taskDir" -ForegroundColor Green
    return 0
}

function Update-TaskStatus {
    param([string]$StatusFile, [scriptblock]$Updater)
    if (-not (Test-Path -LiteralPath $StatusFile)) { return }
    $status = Load-Json -Path $StatusFile
    & $Updater $status
    $status.updated_at = Get-NowIso
    Save-Json -Object $status -Path $StatusFile
}



function Normalize-PathForCompare {
    param([string]$BaseDir, [string]$PathValue)
    if (-not $PathValue) { return $null }
    if ($PathValue -like "*`**" -or $PathValue -like "*?*") {
        # Keep wildcard paths conservative but normalize separators and casing.
        $raw = if ([System.IO.Path]::IsPathRooted($PathValue)) { $PathValue } else { Join-Path $BaseDir $PathValue }
        return $raw.Replace("/", "\").ToLowerInvariant()
    }
    $combined = if ([System.IO.Path]::IsPathRooted($PathValue)) { $PathValue } else { Join-Path $BaseDir $PathValue }
    try { return [System.IO.Path]::GetFullPath($combined).TrimEnd("\").ToLowerInvariant() }
    catch { return $combined.Replace("/", "\").ToLowerInvariant() }
}

function Test-PathInsideBase {
    param([string]$BaseDir, [string]$Candidate)
    $base = [System.IO.Path]::GetFullPath($BaseDir).TrimEnd("\").ToLowerInvariant()
    $cand = [System.IO.Path]::GetFullPath($Candidate).TrimEnd("\").ToLowerInvariant()
    return ($cand -eq $base -or $cand.StartsWith($base + "\"))
}

function Find-KodeXimiProjectRoot {
    param([string]$TaskDir)
    $cursor = Split-Path -Parent ((Resolve-Path -LiteralPath $TaskDir).Path)
    while ($cursor) {
        if (Test-Path -LiteralPath (Join-Path $cursor ".kodeximi")) { return $cursor }
        $parent = Split-Path -Parent $cursor
        if ($parent -eq $cursor) { break }
        $cursor = $parent
    }
    return $null
}

function Find-MisplacedEvidence {
    param(
        [string]$TaskDir,
        [string[]]$Names = @("RESULT.md", "VERIFY.md")
    )
    $hits = @()
    $taskPath = (Resolve-Path -LiteralPath $TaskDir).Path
    $projectRoot = Find-KodeXimiProjectRoot -TaskDir $taskPath
    $searchDirs = @()
    if ($projectRoot) {
        $cursor = Split-Path -Parent $taskPath
        while ($cursor -and $cursor.StartsWith($projectRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            $searchDirs += $cursor
            if ($cursor -eq $projectRoot) { break }
            $cursor = Split-Path -Parent $cursor
        }
    }
    else {
        # No project marker: avoid scanning unrelated repo roots; only inspect the direct parent.
        $searchDirs += (Split-Path -Parent $taskPath)
    }
    foreach ($dir in $searchDirs) {
        foreach ($name in $Names) {
            $candidate = Join-Path $dir $name
            if (Test-Path -LiteralPath $candidate) { $hits += $candidate }
        }
    }
    return @($hits | Sort-Object -Unique)
}


function Invoke-Validate {
    param([string]$TaskDir)
    if (-not $TaskDir) { Write-Error "validate requires a task directory."; return 1 }
    $taskDirResolved = Resolve-ExistingPathString -Path $TaskDir -Kind "Task directory"
    $issues = @()
    $taskFile = Join-Path $taskDirResolved "TASK.md"
    $statusFile = Join-Path $taskDirResolved "status.json"
    $reviewFile = Join-Path $taskDirResolved "CODEX_REVIEW.md"
    $reviewExistedBefore = Test-Path -LiteralPath $reviewFile
    $logsDir = Join-Path $taskDirResolved "logs"
    if (-not (Test-Path -LiteralPath $taskFile)) { $issues += "TASK.md missing." }
    if (-not (Test-Path -LiteralPath $statusFile)) { $issues += "status.json missing." }
    if (-not (Test-Path -LiteralPath $logsDir)) { $issues += "logs/ missing." }
    if (Test-Path -LiteralPath $taskFile) {
        $taskText = Get-Content -Raw -LiteralPath $taskFile -Encoding UTF8
        if ($taskText -notmatch [regex]::Escape($taskDirResolved) -and $taskText -notmatch "(?i)current task directory|task-local|task directory") { $issues += "TASK.md does not describe the current task directory or task-local evidence location." }
        if ($taskText -notmatch "RESULT\.md" -or $taskText -notmatch "VERIFY\.md") { $issues += "TASK.md does not mention RESULT.md / VERIFY.md evidence files." }
    }
    $reviewFile = Join-Path $taskDirResolved "CODEX_REVIEW.md"
    if (Test-Path -LiteralPath $reviewFile) {
        $state = $null
        if (Test-Path -LiteralPath $statusFile) { try { $state = (Load-Json -Path $statusFile).state } catch {} }
        if ($state -notin @("needs-review", "accepted")) {
            $issues += "CODEX_REVIEW.md exists before review state; this file is Codex-owned and should not be created by Kimi."
        }
    }
    $misplaced = Find-MisplacedEvidence -TaskDir $taskDirResolved
    foreach ($m in $misplaced) { $issues += "Possible misplaced evidence file: $m" }
    if ($issues.Count -eq 0) {
        Write-Host "validate: OK" -ForegroundColor Green
        return 0
    }
    Write-Host "validate: ISSUES FOUND" -ForegroundColor Yellow
    foreach ($issue in $issues) { Write-Host "  - $issue" }
    return 1
}

function Invoke-Run {
    param([string]$TaskDir, [int]$TimeoutSeconds = 600)
    if (-not $TaskDir) { Write-Error "run requires a task directory."; return 1 }
    $taskDirResolved = Resolve-ExistingPathString -Path $TaskDir -Kind "Task directory"
    $taskFile = Join-Path $taskDirResolved "TASK.md"
    if (-not (Test-Path -LiteralPath $taskFile)) { Write-Error "TASK.md not found in $taskDirResolved"; return 1 }
    if (-not (Test-Path -LiteralPath $KimiAgentFile)) { Write-Error "Kimi agent file not found: $KimiAgentFile"; return 1 }

    $statusFile = Join-Path $taskDirResolved "status.json"
    $reviewFile = Join-Path $taskDirResolved "CODEX_REVIEW.md"
    $reviewExistedBefore = Test-Path -LiteralPath $reviewFile
    $logsDir = Join-Path $taskDirResolved "logs"
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
    $stdoutLog = Join-Path $logsDir "kimi.stdout.log"
    $stderrLog = Join-Path $logsDir "kimi.stderr.log"
    $lockFile = Join-Path $taskDirResolved ".running.lock"
    if (Test-Path -LiteralPath $lockFile) {
        Write-Error "Task appears to be already running or a stale lock exists: $lockFile"
        return 1
    }
    @{ pid = $PID; started_at = (Get-NowIso); task_dir = $taskDirResolved } | ConvertTo-Json | Set-Content -LiteralPath $lockFile -Encoding UTF8

    Update-TaskStatus -StatusFile $statusFile -Updater { param($s) $s.state = "running"; $s.started_at = Get-NowIso; $s.agent_file = $KimiAgentFile }

    $prompt = "Read TASK.md in the working directory, follow it exactly, keep stdout short, write RESULT.md, and write VERIFY.md if required."
    $kimiArgs = @("--work-dir", $taskDirResolved, "--agent-file", $KimiAgentFile, "--yolo", "--print", "--final-message-only", "--prompt", $prompt)

    $exitCode = 1
    $job = $null
    try {
        $job = Start-Job -ScriptBlock {
            param($KimiArgsForJob, $StdoutLogForJob, $StderrLogForJob)
            & kimi @KimiArgsForJob 1> $StdoutLogForJob 2> $StderrLogForJob
            return $LASTEXITCODE
        } -ArgumentList (,$kimiArgs), $stdoutLog, $stderrLog
        $finished = Wait-Job -Job $job -Timeout $TimeoutSeconds
        if (-not $finished) {
            Stop-Job -Job $job -ErrorAction SilentlyContinue
            $exitCode = 124
            Write-Warning "Kimi timed out after $TimeoutSeconds seconds."
        }
        else {
            $received = Receive-Job -Job $job
            $exitCode = [int]($received | Select-Object -Last 1)
        }
    }
    catch {
        Write-Error "Failed to invoke kimi: $_"
        $exitCode = 1
    }
    finally {
        if ($job) { Remove-Job -Job $job -Force -ErrorAction SilentlyContinue }
        Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue
    }

    $resultPresent = Test-Path -LiteralPath (Join-Path $taskDirResolved "RESULT.md")
    $verifyPresent = Test-Path -LiteralPath (Join-Path $taskDirResolved "VERIFY.md")
    $reviewPresentAfter = Test-Path -LiteralPath $reviewFile
    $reviewCreatedByWorker = (-not $reviewExistedBefore) -and $reviewPresentAfter
    $verifyRequired = $false
    if (Test-Path -LiteralPath $statusFile) { $verifyRequired = [bool](Load-Json -Path $statusFile).verify_required }
    $misplaced = @()
    if (-not $resultPresent -or ($verifyRequired -and -not $verifyPresent)) {
        $misplaced = Find-MisplacedEvidence -TaskDir $taskDirResolved
    }
    $misplacedNote = ""
    if ($misplaced.Count -gt 0) {
        $misplacedNote = " Possible misplaced evidence found: " + ($misplaced -join "; ")
    }

    Update-TaskStatus -StatusFile $statusFile -Updater {
        param($s)
        $s.completed_at = Get-NowIso
        $s.result_present = $resultPresent
        $s.verify_present = $verifyPresent
        if ($exitCode -eq 124) { $s.state = "failed"; $s.notes = "kimi timed out after $TimeoutSeconds seconds.$misplacedNote" }
        elseif ($exitCode -ne 0) { $s.state = "failed"; $s.notes = "kimi exited with code $exitCode$misplacedNote" }
        elseif (-not $resultPresent) { $s.state = "failed"; $s.notes = "RESULT.md missing in task directory.$misplacedNote" }
        elseif ($verifyRequired -and -not $verifyPresent) { $s.state = "failed"; $s.notes = "VERIFY.md required but missing in task directory.$misplacedNote" }
        elseif ($reviewCreatedByWorker) { $s.state = "failed"; $s.notes = "CODEX_REVIEW.md was created during worker run; CODEX_REVIEW.md is Codex-owned." }
        else { $s.state = "needs-review"; $s.notes = "" }
    }

    if (-not $resultPresent) { Write-Warning "RESULT.md not found in task directory." }
    if ($verifyRequired -and -not $verifyPresent) { Write-Warning "VERIFY.md is required but missing in task directory." }
    foreach ($m in $misplaced) { Write-Warning "Possible misplaced evidence file: $m" }
    if ($reviewCreatedByWorker) { Write-Warning "CODEX_REVIEW.md was created during worker run. This is a protocol violation; Codex owns review files." }
    Write-Host "run: exit=$exitCode task=$taskDirResolved" -ForegroundColor Cyan
    return $exitCode
}

function Invoke-Status {
    param([string]$TaskDir)
    if (-not $TaskDir) { Write-Error "status requires a task directory."; return 1 }
    $taskDirResolved = Resolve-ExistingPathString -Path $TaskDir -Kind "Task directory"
    $statusFile = Join-Path $taskDirResolved "status.json"
    if (Test-Path -LiteralPath $statusFile) { Get-Content -Raw -LiteralPath $statusFile -Encoding UTF8 } else { Write-Warning "No status.json found." }
    return 0
}

function Invoke-Result {
    param([string]$TaskDir)
    if (-not $TaskDir) { Write-Error "result requires a task directory."; return 1 }
    $taskDirResolved = Resolve-ExistingPathString -Path $TaskDir -Kind "Task directory"
    $resultFile = Join-Path $taskDirResolved "RESULT.md"
    if (Test-Path -LiteralPath $resultFile) { Get-Content -Raw -LiteralPath $resultFile -Encoding UTF8 } else { Write-Warning "RESULT.md not found." }
    return 0
}


function Invoke-ReviewCheck {
    param([string]$TaskDir, [string]$Project)
    if (-not $TaskDir) { Write-Error "review-check requires a task directory."; return 1 }
    $taskDirResolved = Resolve-ExistingPathString -Path $TaskDir -Kind "Task directory"
    $projectRoot = $null
    if ($Project) { $projectRoot = Resolve-ExistingPathString -Path $Project -Kind "Project path" }
    else { $projectRoot = Find-KodeXimiProjectRoot -TaskDir $taskDirResolved }

    $statusFile = Join-Path $taskDirResolved "status.json"
    $resultFile = Join-Path $taskDirResolved "RESULT.md"
    $verifyFile = Join-Path $taskDirResolved "VERIFY.md"
    $reviewFile = Join-Path $taskDirResolved "CODEX_REVIEW.md"
    $stdoutLog = Join-Path $taskDirResolved "logs\kimi.stdout.log"
    $stderrLog = Join-Path $taskDirResolved "logs\kimi.stderr.log"

    Write-Host "# KodeXimi Review Check"
    Write-Host ""
    Write-Host "Task: $taskDirResolved"
    if ($projectRoot) { Write-Host "Project: $projectRoot" } else { Write-Host "Project: not found; pass -Project <path> for Git checks." }
    Write-Host ""
    Write-Host "## Evidence"
    Write-Host ("- TASK.md: " + (Test-Path -LiteralPath (Join-Path $taskDirResolved "TASK.md")))
    Write-Host ("- status.json: " + (Test-Path -LiteralPath $statusFile))
    if (Test-Path -LiteralPath $statusFile) {
        try {
            $st = Load-Json -Path $statusFile
            Write-Host "- state: $($st.state)"
            Write-Host "- result_present: $($st.result_present)"
            Write-Host "- verify_present: $($st.verify_present)"
            if ($st.notes) { Write-Host "- notes: $($st.notes)" }
        } catch { Write-Host "- status parse error: $_" }
    }
    Write-Host ("- RESULT.md: " + (Test-Path -LiteralPath $resultFile))
    Write-Host ("- VERIFY.md: " + (Test-Path -LiteralPath $verifyFile))
    Write-Host ("- CODEX_REVIEW.md: " + (Test-Path -LiteralPath $reviewFile) + " (Codex-owned)")
    Write-Host ("- stdout log: " + (Test-Path -LiteralPath $stdoutLog))
    Write-Host ("- stderr log: " + (Test-Path -LiteralPath $stderrLog))

    $misplaced = Find-MisplacedEvidence -TaskDir $taskDirResolved
    if ($misplaced.Count -gt 0) {
        Write-Host ""
        Write-Host "## Possible misplaced evidence"
        foreach ($m in $misplaced) { Write-Host "- $m" }
    }

    if ($projectRoot -and (Test-CommandExists "git")) {
        Write-Host ""
        Write-Host "## Git review state"
        $inside = & git -C $projectRoot rev-parse --is-inside-work-tree 2>$null
        if ($LASTEXITCODE -ne 0 -or $inside -ne "true") {
            Write-Host "- Git repo: not found at project path. Git diff review unavailable."
        }
        else {
            $gitRoot = & git -C $projectRoot rev-parse --show-toplevel
            $gitRootFull = [System.IO.Path]::GetFullPath($gitRoot).TrimEnd("\")
            $projectFull = [System.IO.Path]::GetFullPath($projectRoot).TrimEnd("\")
            Write-Host "- Git root: $gitRoot"
            if ($gitRootFull -ne $projectFull) {
                Write-Host "- Scope note: project path is inside a parent Git repository; Git output below is limited to the project path. For real work, prefer an independent project Git root."
            }
            Write-Host ""
            Write-Host "### git status --short"
            & git -C $gitRoot status --short -- $projectRoot
            Write-Host ""
            Write-Host "### git diff --stat"
            & git -C $gitRoot diff --stat -- $projectRoot
            Write-Host ""
            Write-Host "### git diff --cached --stat"
            & git -C $gitRoot diff --cached --stat -- $projectRoot
            Write-Host ""
            Write-Host "### untracked files"
            & git -C $gitRoot ls-files --others --exclude-standard -- $projectRoot
        }
    }
    elseif ($projectRoot) {
        Write-Host ""
        Write-Host "## Git review state"
        Write-Host "- git command not found."
    }
    return 0
}

function Invoke-NewBatch {
    param([string]$Name, [string]$Project = ".")
    if (-not $Name) { Write-Error "new-batch requires a name."; return 1 }
    $projectPath = Resolve-ExistingPathString -Path $Project -Kind "Project path"
    $batchesDir = Join-Path $projectPath "batches"
    New-Item -ItemType Directory -Path $batchesDir -Force | Out-Null
    $batchDir = Join-Path $batchesDir $Name
    if (Test-Path -LiteralPath $batchDir) { Write-Error "Batch already exists: $batchDir"; return 1 }
    New-Item -ItemType Directory -Path $batchDir | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $batchDir "tasks") | Out-Null

    $templateDir = Join-Path $RepoRoot "templates\batch"
    $timestamp = Get-NowIso
    foreach ($f in @("BATCH_TASK.md", "BATCH_REVIEW.md")) {
        $text = Get-Content -Raw -LiteralPath (Join-Path $templateDir $f) -Encoding UTF8
        $text = $text.Replace("{{BATCH_NAME}}", $Name)
        Set-Content -LiteralPath (Join-Path $batchDir $f) -Value $text -Encoding UTF8
    }
    foreach ($f in @("BATCH_MANIFEST.json", "BATCH_STATUS.json")) {
        $text = Get-Content -Raw -LiteralPath (Join-Path $templateDir $f) -Encoding UTF8
        $text = $text.Replace("{{BATCH_NAME}}", $Name).Replace("{{TIMESTAMP}}", $timestamp)
        Set-Content -LiteralPath (Join-Path $batchDir $f) -Value $text -Encoding UTF8
    }
    Write-Host "new-batch: created $batchDir" -ForegroundColor Green
    return 0
}

function Test-WriteSetConflicts {
    param($Tasks, [string]$BaseDir)
    $seen = @{}
    $conflicts = @()
    $forbidden = @(".env", "secrets", "credentials")
    foreach ($t in $Tasks) {
        foreach ($w in @($t.allowed_writes)) {
            if (-not $w) { continue }
            foreach ($bad in $forbidden) { if ($w -like "*$bad*") { $conflicts += "Forbidden write path in $($t.name): $w" } }
            $key = Normalize-PathForCompare -BaseDir $BaseDir -PathValue ([string]$w)
            if ($seen.ContainsKey($key)) { $conflicts += "Overlapping allowed_writes: '$w' in $($seen[$key]) and $($t.name)" }
            else { $seen[$key] = $t.name }
        }
    }
    return $conflicts
}

function Invoke-RunBatch {
    param([string]$BatchDir, [int]$MaxParallel = 1)
    if (-not $BatchDir) { Write-Error "run-batch requires a batch directory."; return 1 }
    $batchDirResolved = Resolve-ExistingPathString -Path $BatchDir -Kind "Batch directory"
    $manifestFile = Join-Path $batchDirResolved "BATCH_MANIFEST.json"
    $statusFile = Join-Path $batchDirResolved "BATCH_STATUS.json"
    if (-not (Test-Path -LiteralPath $manifestFile)) { Write-Error "BATCH_MANIFEST.json not found in $batchDirResolved"; return 1 }
    $manifest = Load-Json -Path $manifestFile
    $tasks = @($manifest.tasks)
    if ($tasks.Count -eq 0) { Write-Error "No tasks in batch manifest."; return 1 }

    $conflicts = Test-WriteSetConflicts -Tasks $tasks -BaseDir $batchDirResolved
    if ($conflicts.Count -gt 0) { foreach ($c in $conflicts) { Write-Error $c }; return 1 }

    if (Test-Path -LiteralPath $statusFile) {
        $st = Load-Json -Path $statusFile; $st.state = "running"; $st.started_at = Get-NowIso; $st.tasks_total = $tasks.Count; Save-Json -Object $st -Path $statusFile
    }

    $hasDependencies = $false
    foreach ($t in $tasks) { if (@($t.depends_on).Count -gt 0) { $hasDependencies = $true } }
    $maxParallel = if ($MaxParallel -gt 1) { $MaxParallel } elseif ($manifest.max_parallel -gt 1) { [int]$manifest.max_parallel } else { 1 }
    if ($hasDependencies -and $maxParallel -gt 1) { Write-Warning "depends_on is present; dependency-aware parallel execution is not implemented. Falling back to serial."; $maxParallel = 1 }
    $completed = 0; $failed = 0
    if ($maxParallel -eq 1) {
        foreach ($t in $tasks) {
            $td = Join-Path $batchDirResolved $t.dir
            Write-Host "Running task $($t.name) -> $td"
            $ec = Invoke-Run -TaskDir $td
            if ($ec -ne 0) { $failed++ } else { $completed++ }
        }
    }
    else {
        $results = $tasks | ForEach-Object -Parallel {
            $td = Join-Path $using:batchDirResolved $_.dir
            $cli = Join-Path $using:RepoRoot "cli\kodeximi.ps1"
            $proc = Start-Process -FilePath "pwsh" -ArgumentList @("-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $cli, "run", $td) -Wait -NoNewWindow -PassThru
            [PSCustomObject]@{ Name = $_.name; ExitCode = $proc.ExitCode }
        } -ThrottleLimit $maxParallel
        foreach ($r in $results) { if ($r.ExitCode -eq 0) { $completed++ } else { $failed++ } }
    }

    if (Test-Path -LiteralPath $statusFile) {
        $st = Load-Json -Path $statusFile
        $st.state = if ($failed -gt 0) { "failed" } else { "needs-review" }
        $st.completed_at = Get-NowIso; $st.tasks_completed = $completed; $st.tasks_failed = $failed
        Save-Json -Object $st -Path $statusFile
    }
    Write-Host "Batch complete. Completed: $completed, Failed: $failed"
    return $failed
}


function Get-KodeXimiEnabledPath {
    param([string]$ProjectPath)
    $projectResolved = Resolve-ExistingPathString -Path $ProjectPath -Kind "Project path"
    $stateDir = Join-Path $projectResolved ".kodeximi"
    return [PSCustomObject]@{
        Project = $projectResolved
        StateDir = $stateDir
        EnabledFile = Join-Path $stateDir "enabled"
    }
}

function Invoke-Enable {
    param([string]$ProjectPath)
    if (-not $ProjectPath) { Write-Error "enable requires a project path."; return 1 }
    $state = Get-KodeXimiEnabledPath -ProjectPath $ProjectPath
    New-Item -ItemType Directory -Path $state.StateDir -Force | Out-Null
    "enabled" | Set-Content -LiteralPath $state.EnabledFile -Encoding UTF8
    Write-Host "KodeXimi: ON" -ForegroundColor Green
    Write-Host "Project: $($state.Project)"
    return 0
}

function Invoke-Disable {
    param([string]$ProjectPath)
    if (-not $ProjectPath) { Write-Error "disable requires a project path."; return 1 }
    $state = Get-KodeXimiEnabledPath -ProjectPath $ProjectPath
    if (Test-Path -LiteralPath $state.EnabledFile) { Remove-Item -LiteralPath $state.EnabledFile -Force }
    Write-Host "KodeXimi: OFF" -ForegroundColor Yellow
    Write-Host "Project: $($state.Project)"
    return 0
}

function Invoke-Mode {
    param([string]$ProjectPath)
    if (-not $ProjectPath) { Write-Error "mode requires a project path."; return 1 }
    $state = Get-KodeXimiEnabledPath -ProjectPath $ProjectPath
    if (Test-Path -LiteralPath $state.EnabledFile) { Write-Host "ON"; return 0 }
    Write-Host "OFF"
    return 0
}

function Get-ArgValue { param([string[]]$ArgsList, [string]$Flag) for ($i=0; $i -lt $ArgsList.Count; $i++) { if ($ArgsList[$i] -eq $Flag -and ($i+1) -lt $ArgsList.Count) { return $ArgsList[$i+1] } }; return $null }

switch ($Command) {
    "doctor" { exit (Invoke-Doctor) }
    "init-project" { exit (Invoke-InitProject -Path $Arguments[0]) }
    "enable" { exit (Invoke-Enable -ProjectPath $Arguments[0]) }
    "disable" { exit (Invoke-Disable -ProjectPath $Arguments[0]) }
    "mode" { exit (Invoke-Mode -ProjectPath $Arguments[0]) }
    "new-task" { $proj = Get-ArgValue -ArgsList $Arguments -Flag "-Project"; if (-not $proj) { $proj = "." }; exit (Invoke-NewTask -Name $Arguments[0] -Project $proj) }
    "validate" { exit (Invoke-Validate -TaskDir $Arguments[0]) }
    "run" { $toStr = Get-ArgValue -ArgsList $Arguments -Flag "-TimeoutSeconds"; $to = if ($toStr) { [int]$toStr } else { 600 }; exit (Invoke-Run -TaskDir $Arguments[0] -TimeoutSeconds $to) }
    "status" { exit (Invoke-Status -TaskDir $Arguments[0]) }
    "result" { exit (Invoke-Result -TaskDir $Arguments[0]) }
    "review-check" { $proj = Get-ArgValue -ArgsList $Arguments -Flag "-Project"; exit (Invoke-ReviewCheck -TaskDir $Arguments[0] -Project $proj) }
    "new-batch" { $proj = Get-ArgValue -ArgsList $Arguments -Flag "-Project"; if (-not $proj) { $proj = "." }; exit (Invoke-NewBatch -Name $Arguments[0] -Project $proj) }
    "run-batch" { $mpStr = Get-ArgValue -ArgsList $Arguments -Flag "-MaxParallel"; $mp = if ($mpStr) { [int]$mpStr } else { 1 }; exit (Invoke-RunBatch -BatchDir $Arguments[0] -MaxParallel $mp) }
    default { Show-Usage; exit 1 }
}






