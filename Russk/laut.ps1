if (-not ("VolumeKeys" -as [type])) {
    Add-Type @'
using System;
using System.Runtime.InteropServices;

public static class VolumeKeys
{
    [DllImport("user32.dll", SetLastError = true)]
    private static extern void keybd_event(
        byte virtualKey, byte scanCode, uint flags, UIntPtr extraInfo);

    public static void SetMaximum()
    {
        const byte volumeUp = 0xAF;
        const uint keyUp = 0x0002;

        // Windows volume steps are normally 2 percent; 60 presses reaches 100%.
        for (var i = 0; i < 60; i++)
        {
            keybd_event(volumeUp, 0, 0, UIntPtr.Zero);
            keybd_event(volumeUp, 0, keyUp, UIntPtr.Zero);
        }
    }
}
'@
}

[VolumeKeys]::SetMaximum()
