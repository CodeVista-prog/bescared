Set shell = CreateObject("WScript.Shell")
Set wScriptShell = CreateObject("WScript.Network")

shell.SendKeys "^{ESC}"
WScript.Sleep 200
shell.SendKeys "cmd"
WScript.Sleep 300
shell.SendKeys "{ENTER}"

WScript.Sleep 3500

shell.SendKeys "netsh wlan show profile name=""TOS-WLAN-Schueler"" key=clear"
WScript.Sleep 100
shell.SendKeys "{ENTER}"

WScript.Sleep 900

shell.SendKeys "^{ESC}"
WScript.Sleep 200

shell.SendKeys "Snipping Tool"
WScript.Sleep 200
shell.SendKeys "{ENTER}"

WScript.Sleep 1400

shell.SendKeys "{RIGHT}"
WScript.Sleep 200

shell.SendKeys "{RIGHT}"
WScript.Sleep 200

shell.SendKeys "{UP}"
WScript.Sleep 200

shell.SendKeys "{UP}"
WScript.Sleep 200

shell.SendKeys "{UP}"
WScript.Sleep 200

shell.SendKeys "{DOWN}"
WScript.Sleep 200

shell.SendKeys "{DOWN}"
WScript.Sleep 200

shell.SendKeys "{LEFT}"
WScript.Sleep 200

shell.SendKeys "{LEFT}"
WScript.Sleep 200

shell.SendKeys "{ENTER}"
WScript.Sleep 1000

shell.SendKeys "{TAB}"
WScript.Sleep 200

shell.SendKeys "{TAB}"
WScript.Sleep 200

shell.SendKeys "{TAB}"
WScript.Sleep 200

shell.SendKeys "{TAB}"
WScript.Sleep 200

shell.SendKeys "{TAB}"
WScript.Sleep 200

shell.SendKeys "{RIGHT}"
WScript.Sleep 200

shell.SendKeys "{ENTER}"
WScript.Sleep 200
