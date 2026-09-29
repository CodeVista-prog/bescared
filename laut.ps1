if (-not ("VolumeKeys" -as [type])) {
    Add-Type @'
using System;
using System.Runtime.InteropServices;

public static class VolumeKeys
{
    [DllImport("user32.dll", SetLastError = true)]
    private static extern void keybd_event(
        byte virtualKey, byte scanCode, uint flags, UIntPtr extraInfo);

    public static void SetMinimum()
    {
        const byte volumeDown = 0xAE;
        const uint keyUp = 0x0002;

        // Windows volume steps are normally 2 percent; 60 presses reaches 0%.
        for (var i = 0; i < 60; i++)
        {
            keybd_event(volumeDown, 0, 0, UIntPtr.Zero);
            keybd_event(volumeDown, 0, keyUp, UIntPtr.Zero);
        }
    }
}
'@
}

[VolumeKeys]::SetMinimum()
