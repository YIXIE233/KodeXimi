#!/usr/bin/env pwsh
#Requires -Version 7.0
# coding: utf-8

<#
.SYNOPSIS
    Install the KodeXimi to a user-level directory.

.DESCRIPTION
    Copies the taskflow files to $HOME\.kodeximi.
    Must be run explicitly by a human.
#>

$ErrorActionPreference = "Stop"

$Source = Split-Path -Parent $PSScriptRoot
$Target = Join-Path $HOME ".kodeximi"

Write-Host "Installing KodeXimi..." -ForegroundColor Cyan
Write-Host "Source: $Source"
Write-Host "Target: $Target"

if (Test-Path $Target) {
    Write-Warning "Target already exists. Remove it first if you want a clean install."
    $confirm = Read-Host "Overwrite? [y/N]"
    if ($confirm -notin @("y","Y")) {
        Write-Host "Aborted."
        exit 1
    }
    Remove-Item -Recurse -Force $Target
}

Copy-Item -Recurse -Path $Source -Destination $Target

Write-Host "Installed to $Target" -ForegroundColor Green
Write-Host "Add the following to your profile to use 'kodeximi' globally:"
Write-Host "  function kodeximi { & '$Target\cli\kodeximi.ps1' @args }"
exit 0




