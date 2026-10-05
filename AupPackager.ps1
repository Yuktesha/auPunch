<#
.SYNOPSIS
    AupPackager - Audacity 2.4.2 專案封包整理小精靈 (MVlab)
#>
param(
    [Parameter(Position=0, ValueFromRemainingArguments=$true)]
    [string]$AupPath,
    [switch]$Move,
    [string]$Compress
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PyScript = Join-Path $ScriptDir "AupPackager.py"

if (-not $AupPath) {
    Write-Host "====================================================================" -ForegroundColor Cyan
    Write-Host "   Audacity 2.4.2 專案封包整理小精靈 (MVlab)" -ForegroundColor Cyan
    Write-Host "====================================================================" -ForegroundColor Cyan
    Write-Host "[提示] 請將 Audacity 2.x 的 .aup 專案檔案路徑作為參數傳入，或直接拖曳至此腳本！"
    Write-Host "範例:"
    Write-Host '    .\AupPackager.ps1 "C:\路徑\專案.aup"'
    Write-Host '    .\AupPackager.ps1 "C:\路徑\專案.aup" -Compress 7z'
    return
}

$ArgsList = @($PyScript, $AupPath)
if ($Move) { $ArgsList += "--move" }
if ($Compress) { $ArgsList += @("--compress", $Compress) }

& python @ArgsList
