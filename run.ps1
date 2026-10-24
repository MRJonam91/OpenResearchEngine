param(
    [string]$Workspace = (Join-Path $PSScriptRoot 'workspace'),
    [int]$Port = 8765,
    [string]$Model = $env:SOURCEPILOT_AI_MODEL,
    [string]$EmbeddingModel = $env:SOURCEPILOT_EMBEDDING_MODEL,
    [switch]$Reinstall
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $python)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
}

$installStamp = Join-Path $PSScriptRoot '.venv\sourcepilot-install.txt'
$dependencyFingerprint = '{0}:{1}' -f (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'pyproject.toml')).Hash, (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'requirements.lock')).Hash
$installedFingerprint = if (Test-Path -LiteralPath $installStamp) { (Get-Content -LiteralPath $installStamp -Raw).Trim() } else { '' }
if ($Reinstall -or $installedFingerprint -ne $dependencyFingerprint) {
    & $python -m pip install -c requirements.lock -e .
    if ($LASTEXITCODE -ne 0) { throw 'Could not install SourcePilot dependencies.' }
    Set-Content -LiteralPath $installStamp -Value $dependencyFingerprint
}

Write-Host "SourcePilot: http://127.0.0.1:$Port"
Write-Host "Workspace: $Workspace"
$launchArguments = @('-m', 'sourcepilot', 'serve', '--workspace', $Workspace, '--port', $Port)
if ($Model) { $launchArguments += @('--model', $Model) }
if ($EmbeddingModel) { $launchArguments += @('--embedding-model', $EmbeddingModel) }
& $python @launchArguments
exit $LASTEXITCODE
