#!/usr/bin/env pwsh
#Requires -Version 7.0
# coding: utf-8

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$KimiAgentFile = Join-Path $RepoRoot "kimi\agents\codex-worker.yaml"

function Test-CommandExists {
    param([string]$Name)
    $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

$issues = @()

if (-not (Test-CommandExists "kimi")) {
    $issues += "kimi CLI not found in PATH."
}
if (-not (Test-CommandExists "pwsh")) {
    $issues += "PowerShell 7 (pwsh) not found in PATH."
}
if (-not (Test-Path $KimiAgentFile)) {
    $issues += "Kimi agent file not found at $KimiAgentFile"
}

# Optional: check UTF-8 support
if ($OutputEncoding.WebName -ne "utf-8") {
    $issues += "OutputEncoding is not UTF-8 (current: $($OutputEncoding.WebName))."
}

if ($issues.Count -eq 0) {
    Write-Host "doctor: OK" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "doctor: ISSUES FOUND" -ForegroundColor Red
    foreach ($issue in $issues) {
        Write-Host "  - $issue"
    }
    exit 1
}


