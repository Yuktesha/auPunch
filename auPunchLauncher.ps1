<#
.SYNOPSIS
    auPunchLauncher - Audacity 智能前導開啟器 (MVlab)
    傳入 .aup (2.x) ➔ 直接以 2.4.2 開啟
    傳入 .aup3 (3.x) ➔ 自動抽脂轉為 2.4.2++ 並開啟
    無參數 ➔ 直接開啟乾淨的 Audacity 2.4.2
#>
param(
    [Parameter(Position=0, ValueFromRemainingArguments=$true)]
    [string]$FilePath
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PyScript = Join-Path $ScriptDir "auPunchLauncher.py"

$ArgsList = @($PyScript)
if ($FilePath) {
    $ArgsList += $FilePath
}

& python @ArgsList
