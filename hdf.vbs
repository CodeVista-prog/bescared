Set shell = CreateObject("WScript.Shell")
Set wScriptShell = CreateObject("WScript.Network")

shell.SendKeys "^{ESC}"
WScript.Sleep 200
shell.SendKeys "cmd"
WScript.Sleep 300
shell.SendKeys "{ENTER}"

WScript.Sleep 3500

shell.SendKeys "netsh wlan show profile name=""TOS-WLAN-Schueler"" key=clear"
WScript.Sleep 200
shell.SendKeys "{ENTER}"

WScript.Sleep 1500

shell.SendKeys "^{ESC}"
WScript.Sleep 500

shell.SendKeys "Snipping Tool"
WScript.Sleep 500
shell.SendKeys "{ENTER}"

WScript.Sleep 2500

shell.SendKeys "{RIGHT}"
WScript.Sleep 500

shell.SendKeys "{RIGHT}"
WScript.Sleep 500

shell.SendKeys "{UP}"
WScript.Sleep 500

shell.SendKeys "{UP}"
WScript.Sleep 500

shell.SendKeys "{UP}"
WScript.Sleep 500

shell.SendKeys "{DOWN}"
WScript.Sleep 500

shell.SendKeys "{DOWN}"
WScript.Sleep 500

shell.SendKeys "{LEFT}"
WScript.Sleep 500

shell.SendKeys "{LEFT}"
WScript.Sleep 500

shell.SendKeys "{ENTER}"
WScript.Sleep 3000

shell.SendKeys "{TAB}"
WScript.Sleep 500

shell.SendKeys "{TAB}"
WScript.Sleep 500

shell.SendKeys "{TAB}"
WScript.Sleep 500

shell.SendKeys "{TAB}"
WScript.Sleep 500

shell.SendKeys "{TAB}"
WScript.Sleep 500

shell.SendKeys "{RIGHT}"
WScript.Sleep 500

shell.SendKeys "{ENTER}"
WScript.Sleep 500
