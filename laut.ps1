$Lautstaerke = 0 # Gewuenschte Lautstaerke von 0 bis 100 Prozent

if (-not ("VolumeKeys" -as [type])) {
    Add-Type @'
using System;
using System.Runtime.InteropServices;

public static class VolumeKeys
{
    [DllImport("user32.dll", SetLastError = true)]
    private static extern void keybd_event(
        byte virtualKey, byte scanCode, uint flags, UIntPtr extraInfo);

    public static void SetLevel(int percent)
    {
        const byte volumeDown = 0xAE;
        const byte volumeUp = 0xAF;
        const uint keyUp = 0x0002;

        for (var i = 0; i < 60; i++)
        {
            keybd_event(volumeDown, 0, 0, UIntPtr.Zero);
            keybd_event(volumeDown, 0, keyUp, UIntPtr.Zero);
        }

        for (var i = 0; i < percent / 2; i++)
        {
            keybd_event(volumeUp, 0, 0, UIntPtr.Zero);
            keybd_event(volumeUp, 0, keyUp, UIntPtr.Zero);
        }
    }
}
'@
}

if ($Lautstaerke -lt 0 -or $Lautstaerke -gt 100) {
    throw "Lautstaerke muss zwischen 0 und 100 liegen."
}

while ($true) {
    [VolumeKeys]::SetLevel($Lautstaerke)
    Start-Sleep -Seconds 2
}
