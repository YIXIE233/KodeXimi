param(
  [switch]$WireSmoke
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'

$repo = Resolve-Path (Join-Path $PSScriptRoot "..")
$env:PYTHONPATH = Join-Path $repo "src"

$args = @("-m", "kodeximi", "doctor", "--cwd", $repo.Path)
if ($WireSmoke) {
  $args += "--wire-smoke"
}

python @args

