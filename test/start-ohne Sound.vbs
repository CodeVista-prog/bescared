Set shell = CreateObject("WScript.Shell")
Set fileSystem = CreateObject("Scripting.FileSystemObject")
scriptDir = fileSystem.GetParentFolderName(WScript.ScriptFullName)

Sub RunHiddenPython(scriptPath)
    Dim command
    command = "py -3 """ & scriptPath & """"

    On Error Resume Next
    shell.Run command, 0, False
    If Err.Number <> 0 Then
        Err.Clear
        command = "python """ & scriptPath & """"
        shell.Run command, 0, False
    End If
    If Err.Number <> 0 Then
        Err.Clear
        command = """C:\Windows\py.exe"" -3 """ & scriptPath & """"
        shell.Run command, 0, False
    End If
    On Error GoTo 0
End Sub

Sub RunVisiblePython(scriptPath)
    Dim command
    command = "py -3 """ & scriptPath & """"

    On Error Resume Next
    shell.Run command, 1, False
    If Err.Number <> 0 Then
        Err.Clear
        command = "python """ & scriptPath & """"
        shell.Run command, 1, False
    End If
    If Err.Number <> 0 Then
        Err.Clear
        command = """C:\Windows\py.exe"" -3 """ & scriptPath & """"
        shell.Run command, 1, False
    End If
    On Error GoTo 0
End Sub

Sub RunHiddenPowerShell(scriptPath)
    Dim command
    command = "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File """ & scriptPath & """"
    shell.Run command, 0, False
End Sub

RunHiddenPython scriptDir & "\new.py"
WScript.Sleep 20000

RunVisiblePython scriptDir & "\Russk.py"