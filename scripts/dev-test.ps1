param(
  [switch]$VerboseTests
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'

$repo = Resolve-Path (Join-Path $PSScriptRoot "..")
$env:PYTHONPATH = Join-Path $repo "src"

$args = @("-m", "unittest", "discover", "-s", (Join-Path $repo "tests"))
if ($VerboseTests) {
  $args += "-v"
}

python @args

