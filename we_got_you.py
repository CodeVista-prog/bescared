import io
import json
import math
import queue
import random
import threading
import urllib.request

import pygame
from PIL import Image, ImageDraw


PROFILES = [
    {
        "name": "Server-Tec",
        "handle": "@Server-Tec",
        "username": "Server-Tec",
        "color": "#75b9ed",
        "glow": "#315f87",
    },
    {
        "name": "CodeVista-prog",
        "handle": "@CodeVista-prog",
        "username": "CodeVista-prog",
        "color": "#a9c1d2",
        "glow": "#536c80",
    },
    {
        "name": "Rigmon840",
        "handle": "@Rigmon840",
        "username": "Rigmon840",
        "color": "#71e5a0",
        "glow": "#27714e",
    },
]

BACKGROUND = (8, 12, 17)
SCENE_DURATION = 7.8


def rgb(hex_color):
    return tuple(int(hex_color[index:index + 2], 16) for index in (1, 3, 5))


def load_avatar(profile, avatar_queue):
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
    except Exception:
        avatar_queue.put((profile["username"], None))


class WeGotYou:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("We got you")
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.width, self.height = self.screen.get_size()
        self.clock = pygame.time.Clock()
        self.phase = 0.0
        self.running = True
        self.avatars = {}
        self.avatar_queue = queue.Queue()
        self.fonts = {}
        self.stars = [
            [random.random(), random.random(), random.uniform(0.07, 0.22), random.random() * math.tau]
            for _ in range(85)
        ]
        for profile in PROFILES:
            threading.Thread(target=load_avatar, args=(profile, self.avatar_queue), daemon=True).start()

    def font(self, size, bold=False):
        key = (size, bold)
        if key not in self.fonts:
            self.fonts[key] = pygame.font.SysFont("segoeui", size, bold=bold)
        return self.fonts[key]

    def draw_text(self, text, center, size, color, bold=False):
        image = self.font(size, bold).render(text, True, color)
        self.screen.blit(image, image.get_rect(center=center))

    def collect_avatars(self):
        while True:
            try:
                username, pixels = self.avatar_queue.get_nowait()
            except queue.Empty:
                break
            if pixels is not None:
                avatar = pygame.image.fromstring(pixels, (256, 256), "RGBA").convert_alpha()
                self.avatars[username] = avatar

    def draw_background(self, delta, profile):
        accent = rgb(profile["color"])
        tint = rgb(profile["glow"])
        self.screen.fill((7, 10, 14))
        for band in range(12):
            offset = math.sin(self.phase * 0.24 + band * 0.65) * 52
            y = int((self.height * (band + 0.3) / 12 + offset) % self.height)
            color = tuple(int(channel * 0.2) for channel in tint)
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
            initials = "".join(part[0] for part in profile["name"].replace("-", " ").split()[:2]).upper()
            self.draw_text(initials, (avatar_x, avatar_y), max(28, avatar_radius // 2), accent, True)

        name_size = min(30, max(19, int(self.width * 0.021)))
        while self.font(name_size, True).size(profile["name"])[0] > self.width * 0.42 and name_size > 15:
            name_size -= 1
        name_y = avatar_y + avatar_radius + 42
        self.draw_text(profile["name"], (avatar_x, name_y), name_size, (230, 238, 244), True)
        self.draw_text(profile["handle"], (avatar_x, name_y + 31), 14, (132, 151, 165))
        self.draw_text(f"0{index + 1}  /  03", (avatar_x, name_y + 68), 11, accent, True)

    def scene_center(self, compact):
        x = self.width // 2 if compact else int(self.width * 0.69)
        y = int(self.height * (0.69 if compact else 0.56))
        return x, y

    def draw_server_scene(self, center):
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
            pygame.draw.line(self.screen, accent, (x + 12, top + 18), (x + rack_width - 12, top + 18), 2)
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
                    pygame.draw.circle(self.screen, led_color, (unit.left + 11 + led * 9, unit.centery), 2)
                bar_width = int((unit.width - 48) * (0.32 + 0.5 * abs(math.sin(self.phase + row + rack_index))))
                pygame.draw.line(self.screen, glow, (unit.left + 43, unit.centery),
                                 (unit.left + 43 + bar_width, unit.centery), 3)

        label_y = top - 45
        self.draw_text("SERVER", (center_x, label_y), 17, (208, 223, 234), True)
        self.draw_text("03 NODES  /  ALL SYSTEMS READY", (center_x, top + rack_height + 30),
                       11, accent, True)

    def draw_code_scene(self, center, scene_time):
        center_x, center_y = center
        accent = rgb(PROFILES[1]["color"])
        panel_width = min(int(self.width * 0.55), 850)
        panel_height = min(int(self.height * 0.52), 430)
        panel = pygame.Rect(0, 0, panel_width, panel_height)
        panel.center = (center_x, center_y)
        pygame.draw.rect(self.screen, (9, 14, 19), panel, border_radius=12)
        pygame.draw.rect(self.screen, (59, 78, 92), panel, width=1, border_radius=12)

        pygame.draw.line(self.screen, (37, 49, 59), (panel.left, panel.top + 48),
                         (panel.right, panel.top + 48), 1)
        for dot_index, color in enumerate(((108, 133, 148), (88, 117, 135), (79, 105, 121))):
            pygame.draw.circle(self.screen, color, (panel.left + 23 + dot_index * 19, panel.top + 24), 5)
        self.draw_text("CODEVISTA  /  SUPPORT.PY", (panel.centerx, panel.top + 24),
                       12, (135, 157, 172), True)

        code = 'print("We got you")'
        typed_count = min(len(code), max(0, int(max(0, scene_time - 0.8) * 8)))
        typed = code[:typed_count]
        code_x = panel.left + 48
        code_y = panel.top + 120
        mono = pygame.font.SysFont("consolas", max(22, min(34, int(panel_width * 0.042))))
        line_number = self.font(16).render("01", True, (83, 103, 116))
        self.screen.blit(line_number, (panel.left + 18, code_y + 5))

        prefix = 'print('
        typed_prefix = typed[:min(len(typed), len(prefix))]
        prefix_surface = mono.render(typed_prefix, True, (188, 208, 221))
        self.screen.blit(prefix_surface, (code_x, code_y))
        remainder = typed[len(prefix):] if len(typed) > len(prefix) else ""
        string_surface = mono.render(remainder, True, accent)
        self.screen.blit(string_surface, (code_x + prefix_surface.get_width(), code_y))

        if typed_count < len(code) and int(scene_time * 2.4) % 2 == 0:
            cursor_x = code_x + mono.size(typed)[0]
            pygame.draw.rect(self.screen, accent, (cursor_x + 2, code_y + 5, 2, mono.get_height() - 8))
        if typed_count == len(code):
            output_y = code_y + 76
            pygame.draw.circle(self.screen, accent, (code_x + 5, output_y + 12), 3)
            self.draw_text("We got you", (code_x + 105, output_y + 12), 20, (218, 231, 239))
        self.draw_text("BUILD SUCCESSFUL", (panel.left + 122, panel.bottom - 34),
                       11, accent, True)

    def draw_mascot(self, center, scale):
        x, y = center
        skin = (126, 221, 146)
        body = pygame.Rect(x - scale // 2, y - scale // 3, scale, int(scale * 1.15))
        pygame.draw.ellipse(self.screen, skin, body)
        for antenna_x in (x - scale // 4, x + scale // 4):
            pygame.draw.line(self.screen, skin, (antenna_x, body.top + 4),
                             (antenna_x + (antenna_x - x) // 2, body.top - scale // 4), 3)
            pygame.draw.circle(self.screen, (210, 248, 172),
                               (antenna_x + (antenna_x - x) // 2, body.top - scale // 4), 4)
        eye_y = y - scale // 8
        eye_spacing = scale // 4
        for eye_x in (x - eye_spacing, x, x + eye_spacing):
            pygame.draw.circle(self.screen, (232, 246, 224), (eye_x, eye_y), max(4, scale // 9))
            pygame.draw.circle(self.screen, (22, 48, 42), (eye_x + 1, eye_y), max(2, scale // 18))
        for leg_x in (x - scale // 4, x + scale // 4):
            pygame.draw.line(self.screen, skin, (leg_x, body.bottom - 5),
                             (leg_x - 5, body.bottom + scale // 4), 4)

    def draw_portal_scene(self, center):
        center_x, center_y = center
        radius = min(240, max(68, int(min(self.width * 0.17, self.height * 0.28))))
        outer = (45, 191, 113)
        inner = (13, 46, 39)
        pygame.draw.circle(self.screen, (12, 34, 30), (center_x, center_y), radius + 22)
        pygame.draw.circle(self.screen, outer, (center_x, center_y), radius + 14, 2)
        pygame.draw.circle(self.screen, (30, 117, 82), (center_x, center_y), radius + 5, 5)
        pygame.draw.circle(self.screen, inner, (center_x, center_y), radius)
        pygame.draw.circle(self.screen, (19, 77, 58), (center_x, center_y), int(radius * 0.73), 2)

        for ring in range(4):
            ring_radius = int(radius * (0.36 + ring * 0.14))
            rect = pygame.Rect(center_x - ring_radius, center_y - ring_radius,
                               ring_radius * 2, ring_radius * 2)
            start = self.phase * (0.7 + ring * 0.16) * (1 if ring % 2 else -1)
            pygame.draw.arc(self.screen, (55 + ring * 18, 205, 120 + ring * 13),
                            rect, start, start + 2.0, 2)

        for particle in range(18):
            angle = self.phase * 0.65 + particle * math.tau / 18
            distance = radius * (0.28 + 0.66 * ((particle * 7 % 18) / 18))
            px = int(center_x + math.cos(angle) * distance)
            py = int(center_y + math.sin(angle) * distance)
            pygame.draw.circle(self.screen, (100, 235, 145), (px, py), 2 + particle % 2)

        bob = math.sin(self.phase * 1.8) * radius * 0.08
        mascot_center = (int(center_x + radius * 0.93), int(center_y + radius * 0.48 + bob))
        self.draw_mascot(mascot_center, max(34, int(radius * 0.46)))
        self.draw_text("A LITTLE HELP FROM ANOTHER WORLD", (center_x, center_y + radius + 64),
                       11, (132, 215, 159), True)

    def draw(self, delta):
        scene_duration = SCENE_DURATION
        scene_index = int(self.phase / scene_duration) % len(PROFILES)
        scene_time = self.phase % scene_duration
        profile = PROFILES[scene_index]
        compact = self.width < 900
        self.draw_background(delta, profile)

        title_size = max(29, min(48, int(self.height * 0.058)))
        title_color = tuple(int(value * (0.72 + 0.28 * math.sin(self.phase * 1.4)))
                            for value in (220, 233, 241))
        self.draw_text("WE GOT YOU", (self.width // 2, int(self.height * 0.12)),
                       title_size, title_color, True)
        self.draw_identity(profile, scene_index, compact)
        center = self.scene_center(compact)

        if scene_index == 0:
            self.draw_server_scene(center)
        elif scene_index == 1:
            self.draw_code_scene(center, scene_time)
        else:
            self.draw_portal_scene(center)

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
            if self.phase >= SCENE_DURATION * len(PROFILES):
                self.running = False
        pygame.quit()


if __name__ == "__main__":
    WeGotYou().run()