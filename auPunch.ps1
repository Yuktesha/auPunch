<#
.SYNOPSIS
    auPunch - Audacity 3.x 轉 2.4.2++ 滾動批次抽脂轉換器 (MVlab)
    “Punch your Audacity 3.x projects down to 2.4.2 & FLAC with zero hassle.”
#>
param(
    [string]$Source = "",
    [string]$Output = "",
    [string]$Target = "ardour",
    [switch]$Wav,
    [switch]$Edit,
    [switch]$GUI,
    [switch]$G,
    [int]$Limit,
    [switch]$Help
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PyScript = Join-Path $ScriptDir "auPunch.py"

# 無參數或要求說明
if ($Help -or ($PSBoundParameters.Count -eq 0)) {
    & python $PyScript -h
    return
}

if ($GUI -or $G) {
    & python $PyScript --gui
    return
}

$ArgsList = @($PyScript)
if ($Source) { $ArgsList += @("--source", $Source) }
if ($Output) { $ArgsList += @("--output", $Output) }
if ($Target) { $ArgsList += @("--target", $Target) }
if ($Wav) { $ArgsList += "--wav" }
if ($Edit) { $ArgsList += "--edit" }
if ($Limit -gt 0) { $ArgsList += @("--limit", $Limit.ToString()) }

& python @ArgsList
