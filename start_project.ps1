# Start the local read-only status page, 3D browser app and resumable pipeline.
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$logDir = Join-Path $projectDir 'logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$pythonExe = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$nodeExe = (Get-Command node -ErrorAction Stop).Source

if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw "Python runtime not found: $pythonExe"
}

function Test-LocalPort([int]$port) {
    [bool](Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

if (-not (Test-LocalPort 8765)) {
    Start-Process -FilePath $pythonExe -ArgumentList @('download_status_server.py') `
        -WorkingDirectory $projectDir -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDir 'status.stdout.log') `
        -RedirectStandardError (Join-Path $logDir 'status.stderr.log') | Out-Null
}
if (-not (Test-LocalPort 4173)) {
    Start-Process -FilePath $nodeExe -ArgumentList @('app/server.mjs') `
        -WorkingDirectory $projectDir -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDir 'app.stdout.log') `
        -RedirectStandardError (Join-Path $logDir 'app.stderr.log') | Out-Null
}

$pipeline = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq 'python.exe' -and $_.CommandLine -match 'run_pipeline\.py'
}
$stateFile = Join-Path $logDir 'pipeline_state.json'
$done = (Test-Path -LiteralPath $stateFile) -and
    ((Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json).stage -eq 'complete')
if (-not $pipeline -and -not $done) {
    Start-Process -FilePath $pythonExe -ArgumentList @('-u', 'run_pipeline.py') `
        -WorkingDirectory $projectDir -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDir 'pipeline.stdout.log') `
        -RedirectStandardError (Join-Path $logDir 'pipeline.stderr.log') | Out-Null
}

Write-Output '3D: http://127.0.0.1:4173/'
Write-Output 'Download: http://127.0.0.1:8765/'
