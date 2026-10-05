<#
.SYNOPSIS
    註冊 Windows 檔案總管右鍵選單：🥊 使用 auPunch 輕快開啟
    支援 .aup (直接以 2.4.2 開啟) 與 .aup3 (自動抽脂轉為 2.4.2++ 後開啟)
    寫入 HKCU，完全不需管理員 UAC 提權！
#>
param(
    [switch]$Uninstall
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$LauncherPy = Join-Path $ScriptDir "auPunchLauncher.py"
$PythonExe = (Get-Command python).Source
$CommandStr = "`"$PythonExe`" `"$LauncherPy`" `"%1`""

$Extensions = @(".aup", ".aup3")

if ($Uninstall) {
    foreach ($ext in $Extensions) {
        $keyPath = "HKCU:\Software\Classes\SystemFileAssociations\$ext\shell\auPunch"
        if (Test-Path $keyPath) {
            Remove-Item $keyPath -Recurse -Force
            Write-Host "[-] 已移除 $ext 右鍵選單關聯" -ForegroundColor Yellow
        }
    }
    Write-Host "[+] 右鍵選單解除完成。" -ForegroundColor Green
    return
}

foreach ($ext in $Extensions) {
    $keyPath = "HKCU:\Software\Classes\SystemFileAssociations\$ext\shell\auPunch"
    $cmdPath = "$keyPath\command"
    
    New-Item -Path $keyPath -Force | Out-Null
    Set-ItemProperty -Path $keyPath -Name "(Default)" -Value "🥊 使用 auPunch 輕快開啟 (Audacity 2.4.2)"
    Set-ItemProperty -Path $keyPath -Name "Icon" -Value "$ScriptDir\AudacityPortable\audacity.exe"
    
    New-Item -Path $cmdPath -Force | Out-Null
    Set-ItemProperty -Path $cmdPath -Name "(Default)" -Value $CommandStr
    
    Write-Host "[+] 已成功新增 $ext 右鍵關聯選單！" -ForegroundColor Green
}

Write-Host "`n🎉 設定完成！現在你在任何 .aup 或 .aup3 檔案上按右鍵，即可看到「🥊 使用 auPunch 輕快開啟」！" -ForegroundColor Cyan
