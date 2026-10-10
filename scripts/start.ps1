# ds-agent 一键启动（Windows PowerShell）
param(
  [switch]$Audit,
  [switch]$WithWeb,
  [switch]$WithAdmin,
  [string]$DsReadUrl = '',
  [string]$DsReadFile = ''
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$VenvPy = Join-Path $Root '.venv\Scripts\python.exe'
if (Test-Path $VenvPy) { $Py = $VenvPy } else { $Py = 'python' }

$env:PYTHONPATH = "$Root\src;$env:PYTHONPATH"

$Arguments = @('-m', 'ds_agent.launcher')
if ($Audit)     { $Arguments += '--audit' }
if ($WithWeb)   { $Arguments += '--with-web' }
if ($WithAdmin) { $Arguments += '--with-admin' }
if ($DsReadUrl)  { $Arguments += @('--ds-read-url', $DsReadUrl) }
if ($DsReadFile) { $Arguments += @('--ds-read-file', $DsReadFile) }

& $Py @Arguments
exit $LASTEXITCODE
