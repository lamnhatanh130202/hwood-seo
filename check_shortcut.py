import os, subprocess

ps = """
$WshShell = New-Object -ComObject WScript.Shell
$sc = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\\HWOOD SEO AI.lnk')
Write-Output ("TargetPath: " + $sc.TargetPath)
Write-Output ("Arguments: " + $sc.Arguments)
Write-Output ("WorkingDirectory: " + $sc.WorkingDirectory)
Write-Output ("IconLocation: " + $sc.IconLocation)
"""
r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
print(r.stdout)
