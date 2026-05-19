#!/usr/bin/env pwsh
#Requires -Version 7.0
# coding: utf-8

<#
.SYNOPSIS
    Uninstall the KodeXimi from the user-level directory.
#>

$ErrorActionPreference = "Stop"

$Target = Join-Path $HOME ".kodeximi"

if (-not (Test-Path $Target)) {
    Write-Host "Nothing to uninstall at $Target"
    exit 0
}

$confirm = Read-Host "Remove $Target ? [y/N]"
if ($confirm -notin @("y","Y")) {
    Write-Host "Aborted."
    exit 1
}

Remove-Item -Recurse -Force $Target
Write-Host "Uninstalled." -ForegroundColor Green
exit 0



