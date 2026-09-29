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
            [random.random(), random.random(), random.uniform(0.025, 0.11), random.random() * math.tau]
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

    def draw_background(self, delta):
        self.screen.fill(BACKGROUND)
        for band in range(9):
            offset = math.sin(self.phase * 0.25 + band * 0.8) * 24
            y = int((self.height * (band + 0.4) / 9 + offset) % self.height)
            pygame.draw.line(self.screen, (16, 26, 36), (0, y), (self.width, y - self.height // 9), 1)

        for star in self.stars:
            star[1] = (star[1] - star[2] * delta) % 1.0
            x = int(star[0] * self.width + math.sin(self.phase + star[3]) * 13)
            y = int(star[1] * self.height)
            brightness = 0.45 + 0.55 * abs(math.sin(self.phase * 1.6 + star[3]))
            color = tuple(int(channel * brightness) for channel in (69, 100, 122))
            pygame.draw.circle(self.screen, color, (x, y), 1 if brightness < 0.8 else 2)

        for index, profile in enumerate(PROFILES):
            tint = rgb(profile["glow"])
            x = int(self.width * (0.2 + index * 0.3) + math.sin(self.phase * 0.3 + index) * 90)
            y = int(self.height * 0.52 + math.cos(self.phase * 0.24 + index) * 95)
            glow = pygame.Surface((260, 260), pygame.SRCALPHA)
            for radius, alpha in ((126, 5), (96, 7), (66, 9)):
                pygame.draw.circle(glow, (*tint, alpha), (130, 130), radius)
            self.screen.blit(glow, (x - 130, y - 130), special_flags=pygame.BLEND_RGBA_ADD)

    def draw_profile(self, profile, center_x, card_width, card_height, card_top, index):
        accent = rgb(profile["color"])
        glow = rgb(profile["glow"])
        card = pygame.Rect(0, 0, card_width, card_height)
        card.center = (center_x, int(card_top + card_height / 2))
        pygame.draw.rect(self.screen, (15, 23, 31), card, border_radius=22)
        pygame.draw.rect(self.screen, (33, 46, 58), card, width=1, border_radius=22)
        pygame.draw.line(self.screen, glow, (card.left + 24, card.top + 2),
                         (card.right - 24, card.top + 2), 2)

        pulse = 0.5 + 0.5 * math.sin(self.phase * 2.0 + index * 1.7)
        avatar_radius = min(96, max(58, int(min(self.width / 10.5, self.height / 5.5))))
        avatar_x = center_x
        avatar_y = int(card.top + card_height * 0.39 + math.sin(self.phase * 1.2 + index) * 4)

        ring_layer = pygame.Surface((avatar_radius * 4, avatar_radius * 4), pygame.SRCALPHA)
        ring_center = (avatar_radius * 2, avatar_radius * 2)
        for radius, alpha in ((int(avatar_radius * (1.34 + pulse * 0.07)), 24),
                              (int(avatar_radius * 1.2), 58)):
            pygame.draw.circle(ring_layer, (*glow, alpha), ring_center, radius, 2)
        pygame.draw.circle(ring_layer, (*accent, 225), ring_center, avatar_radius + 4, 2)
        self.screen.blit(ring_layer, (avatar_x - avatar_radius * 2, avatar_y - avatar_radius * 2))

        orbit_radius = int(avatar_radius * 1.47)
        orbit_rect = pygame.Rect(avatar_x - orbit_radius, avatar_y - orbit_radius,
                                 orbit_radius * 2, orbit_radius * 2)
        start_angle = self.phase * 0.9 + index * 2.1
        pygame.draw.arc(self.screen, accent, orbit_rect, start_angle, start_angle + 1.15, 2)
        pygame.draw.arc(self.screen, glow, orbit_rect, start_angle + math.pi,
                        start_angle + math.pi + 0.75, 2)
        dot_angle = -self.phase * 1.7 + index * 2.0
        dot = (int(avatar_x + math.cos(dot_angle) * orbit_radius),
               int(avatar_y + math.sin(dot_angle) * orbit_radius))
        pygame.draw.circle(self.screen, accent, dot, 4)

        avatar = self.avatars.get(profile["username"])
        if avatar:
            image = pygame.transform.smoothscale(avatar, (avatar_radius * 2, avatar_radius * 2))
            self.screen.blit(image, image.get_rect(center=(avatar_x, avatar_y)))
        else:
            pygame.draw.circle(self.screen, (23, 35, 45), (avatar_x, avatar_y), avatar_radius)
            initials = "".join(part[0] for part in profile["name"].replace("-", " ").split()[:2]).upper()
            self.draw_text(initials, (avatar_x, avatar_y), max(30, avatar_radius // 2), accent, True)

        name_size = min(21, max(14, int(card_width * 0.064)))
        while self.font(name_size, True).size(profile["name"])[0] > card_width - 28 and name_size > 13:
            name_size -= 1
        name_y = int(card.top + card_height * 0.75)
        self.draw_text(profile["name"], (center_x, name_y), name_size, (229, 237, 243), True)
        self.draw_text(profile["handle"], (center_x, name_y + 29), 12, (133, 151, 165))

        status_y = card.bottom - 27
        pygame.draw.circle(self.screen, accent, (center_x - 43, status_y), 3)
        self.draw_text("HERE FOR YOU", (center_x + 12, status_y), 10, accent, True)

    def draw(self, delta):
        self.draw_background(delta)
        title_size = max(32, min(54, int(self.height * 0.065)))
        title_glow = 0.55 + 0.45 * math.sin(self.phase * 1.5)
        title_color = tuple(int(value * title_glow) for value in (222, 235, 244))
        self.draw_text("WE GOT YOU", (self.width // 2, int(self.height * 0.19)), title_size,
                       title_color, True)
        line_y = int(self.height * 0.19) + title_size
        pygame.draw.line(self.screen, (62, 91, 111), (self.width * 0.43, line_y),
                         (self.width * 0.57, line_y), 1)

        spacing = min(self.width * 0.29, 390)
        centers = (self.width / 2 - spacing, self.width / 2, self.width / 2 + spacing)
        card_width = int(min(self.width * 0.27, 340))
        card_height = int(min(self.height * 0.49, 405))
        card_top = int(self.height * 0.34)
        for index, (profile, center_x) in enumerate(zip(PROFILES, centers)):
            self.draw_profile(profile, int(center_x), card_width, card_height, card_top, index)

        self.phase += delta

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
        pygame.quit()


if __name__ == "__main__":
    WeGotYou().run()