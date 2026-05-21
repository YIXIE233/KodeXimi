param(
  [switch]$WireSmoke,
  [switch]$RepoOnly
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'

$repo = Resolve-Path (Join-Path $PSScriptRoot "..")
$env:PYTHONPATH = Join-Path $repo "src"

if ($RepoOnly) {
  $args = @("-m", "kodeximi", "doctor", "--cwd", $repo.Path)
  if ($WireSmoke) {
    $args += "--wire-smoke"
  }
  python @args
  exit $LASTEXITCODE
}

$tmp = Join-Path $env:TEMP ("kodeximi-doctor-" + [System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tmp | Out-Null
try {
  git -C $tmp init | Out-Null
  Set-Content -LiteralPath (Join-Path $tmp "README.md") -Value "# doctor smoke" -Encoding UTF8
  git -C $tmp add . | Out-Null
  git -C $tmp -c user.email=test@example.com -c user.name=Test commit -m init | Out-Null
  python -m kodeximi init --cwd $tmp | Out-Null
  $args = @("-m", "kodeximi", "doctor", "--cwd", $tmp)
  if ($WireSmoke) {
    $args += "--wire-smoke"
  }
  python @args
  exit $LASTEXITCODE
}
finally {
  Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
