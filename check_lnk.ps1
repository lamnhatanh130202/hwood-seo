$sh = New-Object -ComObject WScript.Shell
$sc = $sh.CreateShortcut("C:\Users\HOME CENTER GROUP\Desktop\HWOOD SEO AI.lnk")
"Target: " + $sc.TargetPath
"Arguments: " + $sc.Arguments
"WorkingDirectory: " + $sc.WorkingDirectory
"IconLocation: " + $sc.IconLocation
