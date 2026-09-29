import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import random
import threading
import tkinter as tk
from urllib.request import urlopen

try:
	import pygame
except ImportError:
	pygame = None

IP_API_URL = "http://ip-api.com/json/?fields=status,country,countryCode,lat,lon,query,city"
MUTEX_NAME = "Local\\MonitorMapApp.SingleInstance"
ERROR_ALREADY_EXISTS = 183
LAND_DATA_PATH = Path(__file__).with_name("world-land.geojson")
MAP_WIDTH = 520
MAP_HEIGHT = 245
MAP_MARGIN = 10
LOCATION_WINDOW_COUNT = 99999
BLACK_SCREEN_DURATION_MS = 20_000
MAP_COLORS = {
	"water": "#101b24",
	"grid": "#263741",
	"land": "#397f72",
	"coast": "#285e56",
	"marker": "#e34b42",
	"marker_outline": "#edf4f4",
}

# Windows API Events für Maus-Klicks
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004


def get_monitors():
	monitors = []

	@ctypes.WINFUNCTYPE(
		wintypes.BOOL,
		wintypes.HMONITOR,
		wintypes.HDC,
		ctypes.POINTER(wintypes.RECT),
		wintypes.LPARAM,
	)
	def callback(_monitor, _hdc, _rect, _data):
		rect = _rect.contents
		monitors.append((rect.left, rect.top, rect.right, rect.bottom))
		return True

	if not ctypes.windll.user32.EnumDisplayMonitors(None, None, callback, 0):
		raise ctypes.WinError()

	monitors.sort(key=lambda bounds: bounds[:2] != (0, 0))
	return monitors


def acquire_single_instance():
	kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
	create_mutex = kernel32.CreateMutexW
	create_mutex.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR)
	create_mutex.restype = wintypes.HANDLE
	kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
	kernel32.CloseHandle.restype = wintypes.BOOL

	ctypes.set_last_error(0)
	mutex_handle = create_mutex(None, False, MUTEX_NAME)
	if not mutex_handle:
		raise ctypes.WinError(ctypes.get_last_error())
	if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
		kernel32.CloseHandle(mutex_handle)
		return None
	return kernel32, mutex_handle


def get_ip_location():
	try:
		with urlopen(IP_API_URL, timeout=5) as response:
			location = json.load(response)
		if location.get("status") == "success":
			return location
	except (OSError, ValueError):
		pass
	return None


def play_startup_audio(stop_event):
	if pygame is None:
		return
	audio_paths = []
	for index in range(1, 4):
		audio_path = Path(__file__).with_name(f"s{index}.mp3")
		if audio_path.is_file():
			audio_paths.append(audio_path)
	if not audio_paths:
		return

	pygame.mixer.init()
	sounds = [pygame.mixer.Sound(str(audio_path)) for audio_path in audio_paths]
	try:
		while not stop_event.is_set():
			channels = [sound.play() for sound in sounds]
			while not stop_event.is_set() and any(
				channel is not None and channel.get_busy() for channel in channels
			):
				stop_event.wait(0.1)
			if stop_event.is_set():
				pygame.mixer.stop()
	finally:
		pygame.mixer.quit()


def draw_world_map(canvas, location):
	map_width = MAP_WIDTH - MAP_MARGIN * 2
	map_height = MAP_HEIGHT - MAP_MARGIN * 2
	canvas.configure(width=MAP_WIDTH, height=MAP_HEIGHT, bg=MAP_COLORS["water"], highlightthickness=0)

	def project(longitude, latitude):
		x = MAP_MARGIN + (longitude + 180) / 360 * map_width
		y = MAP_MARGIN + (90 - latitude) / 180 * map_height
		return x, y

	for longitude in (-120, -60, 0, 60, 120):
		x, _ = project(longitude, 0)
		canvas.create_line(x, MAP_MARGIN, x, MAP_HEIGHT - MAP_MARGIN, fill=MAP_COLORS["grid"])
	for latitude in (-60, -30, 0, 30, 60):
		_, y = project(0, latitude)
		canvas.create_line(MAP_MARGIN, y, MAP_WIDTH - MAP_MARGIN, y, fill=MAP_COLORS["grid"])

	if LAND_DATA_PATH.is_file():
		land_data = json.loads(LAND_DATA_PATH.read_text(encoding="utf-8"))
		for feature in land_data.get("features", []):
			for ring in feature["geometry"]["coordinates"]:
				segments = [[]]
				previous_longitude = None
				for longitude, latitude in ring:
					if previous_longitude is not None and abs(longitude - previous_longitude) > 180:
						segments.append([])
					segments[-1].extend(project(longitude, latitude))
					previous_longitude = longitude
				for points in segments:
					if len(points) >= 6:
						canvas.create_polygon(
							points,
							fill=MAP_COLORS["land"],
							outline=MAP_COLORS["coast"],
							width=1,
						)

	if location and "lon" in location and "lat" in location:
		marker_x, marker_y = project(location["lon"], location["lat"])
		canvas.create_oval(
			marker_x - 7,
			marker_y - 7,
			marker_x + 7,
			marker_y + 7,
			fill=MAP_COLORS["marker"],
			outline=MAP_COLORS["marker_outline"],
			width=2,
		)


class MonitorApp(tk.Tk):
	def __init__(self, location, secondary_monitor=None):
		super().__init__()
		self.location = location or {}
		self.secondary_monitor = secondary_monitor
		self.black_screen = None
		self.black_screen_seconds = BLACK_SCREEN_DURATION_MS // 1000
		self.countdown_label = None
		self.location_window_blink_on = False
		self.black_screen_blink_on = False

		self.overrideredirect(True)
		self.configure(bg="#080f14")
		self.resizable(False, False)
		self.attributes("-topmost", True)
		self._center_window(560, 340)
		self._build_card()

		self.location_windows = []
		self.location_positions = []
		for window_index in range(LOCATION_WINDOW_COUNT):
			self._show_location_window(window_index)

		if self.secondary_monitor:
			self._show_black_screen(self.secondary_monitor)

		self.after(1000, self._update_black_screen_timer)
		
		# Loops für Zentrierung (alle 200ms) und Klick (alle 1000ms) starten
		self._center_mouse_loop()
		self._click_mouse_loop()

	def _center_window(self, width, height):
		x = (self.winfo_screenwidth() - width) // 2
		y = (self.winfo_screenheight() - height) // 2
		self.geometry(f"{width}x{height}+{x}+{y}")

	def _center_mouse_loop(self):
		"""Zentriert die Maus alle 0.2 Sekunden (200ms) in der Mitte der Karte."""
		if hasattr(self, "map_canvas") and self.map_canvas.winfo_exists():
			center_x = self.map_canvas.winfo_rootx() + self.map_canvas.winfo_width() // 2
			center_y = self.map_canvas.winfo_rooty() + self.map_canvas.winfo_height() // 2
			ctypes.windll.user32.SetCursorPos(center_x, center_y)
		self.after(200, self._center_mouse_loop)

	def _click_mouse_loop(self):
		"""Führt alle 1.0 Sekunde (1000ms) einen Linksklick aus."""
		if hasattr(self, "map_canvas") and self.map_canvas.winfo_exists():
			ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
			ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
		self.after(1000, self._click_mouse_loop)

	def _build_card(self):
		card = tk.Frame(self, bg="#101820", highlightbackground="#263741", highlightthickness=1)
		card.pack(fill="both", expand=True, padx=1, pady=1)

		header = tk.Frame(card, bg="#101820")
		header.pack(fill="x", padx=20, pady=(16, 12))
		tk.Label(header, text="Карта мира", bg="#101820", fg="#e7eef1", font=("Segoe UI", 12, "bold")).pack(side="left")
		
		place = ", ".join(part for part in (self.location.get("city"), self.location.get("country")) if part)
		if place:
			tk.Label(header, text=place, bg="#101820", fg="#a2b2ba", font=("Segoe UI", 9)).pack(side="left", padx=(12, 0))

		tk.Button(
			header,
			text="X",
			command=self.destroy,
			bg="#101820",
			fg="#bdc9ce",
			activebackground="#263741",
			borderwidth=0,
			font=("Segoe UI", 10),
			cursor="hand2",
		).pack(side="right")

		self.map_canvas = tk.Canvas(card)
		self.map_canvas.pack(fill="both", expand=True, padx=16, pady=(0, 12))
		draw_world_map(self.map_canvas, self.location)

		footer = tk.Frame(card, bg="#101820")
		footer.pack(fill="x", padx=20, pady=(0, 16))
		ip_address = self.location.get("query", "Nicht verfügbar")
		tk.Label(
			footer,
			text=f"IP-адрес: {ip_address}",
			bg="#101820",
			fg="#a2b2ba",
			font=("Segoe UI", 9),
		).pack(side="left")

		self.countdown_label = tk.Label(
			footer,
			text=f"Таймер: {self.black_screen_seconds} s",
			bg="#101820",
			fg="#a2b2ba",
			font=("Segoe UI", 9),
		)
		self.countdown_label.pack(side="right")

	def _show_location_window(self, window_index):
		width, height = 400, 220
		screen_width = self.winfo_screenwidth()
		screen_height = self.winfo_screenheight()
		max_x = max(0, screen_width - width - 10)
		max_y = max(0, screen_height - height - 10)

		x, y = 0, 0
		for _attempt in range(20):
			x = random.randint(0, max_x)
			y = random.randint(0, max_y)
			if (x, y) not in self.location_positions:
				break
		self.location_positions.append((x, y))

		location_window = tk.Toplevel(self)
		location_window.title("Твой аккаунт взломали")
		location_window.configure(bg="#000000", highlightbackground="#ff0000", highlightthickness=1)
		location_window.geometry(f"{width}x{height}+{x}+{y}")
		location_window.attributes("-topmost", True)

		location_window_label = tk.Label(
			location_window,
			text="Твой аккаунт взломали",
			bg="#000000",
			fg="#ff0000",
			font=("Segoe UI", 18, "bold"),
			anchor="center",
		)
		location_window_label.pack(fill="x", padx=18, pady=(16, 8))

		location_details = tk.Frame(location_window, bg="#000000")
		location_details.pack(side="bottom", anchor="w", padx=18, pady=14)

		place = ", ".join(part for part in (self.location.get("city"), self.location.get("country")) if part)
		if place:
			tk.Label(
				location_details,
				text=place,
				bg="#101820",
				fg="#a2b2ba",
				font=("Segoe UI", 9),
			).pack(anchor="w", pady=4)

		if self.location.get("lat") is not None and self.location.get("lon") is not None:
			tk.Label(
				location_details,
				text=f"{self.location['lat']:.4f}, {self.location['lon']:.4f}",
				bg="#000000",
				fg="#ff0000",
				font=("Segoe UI", 9),
			).pack(anchor="w", pady=4)

		self.location_windows.append((location_window, location_window_label))
		if len(self.location_windows) == LOCATION_WINDOW_COUNT:
			self._blink_location_windows()

	def _blink_location_windows(self):
		if not self.location_windows:
			return
		self.location_window_blink_on = not self.location_window_blink_on
		background = "#ff0000" if self.location_window_blink_on else "#000000"
		foreground = "#000000" if self.location_window_blink_on else "#ff0000"

		for location_window, location_window_label in self.location_windows:
			if not location_window.winfo_exists():
				continue
			location_window.configure(bg=background, highlightbackground=foreground)
			location_window_label.configure(bg=background, fg=foreground)
			for child in location_window.winfo_children():
				if child is not location_window_label:
					child.configure(bg=background)
					for detail in child.winfo_children():
						detail.configure(bg=background, fg=foreground)

		self.after(500, self._blink_location_windows)

	def _show_black_screen(self, bounds):
		left, top, right, bottom = bounds
		self.black_screen = tk.Toplevel(self)
		self.black_screen.overrideredirect(True)
		self.black_screen.configure(bg="#000000")

		width = min(560, right - left)
		height = min(340, bottom - top)
		x = left + (right - left - width) // 2
		y = top + (bottom - top - height) // 2

		self.black_screen.geometry(f"{width}x{height}{x:+d}{y:+d}")
		self.black_screen.attributes("-topmost", True)

		self.black_screen_label = tk.Label(
			self.black_screen,
			text="Твой аккаунт взломали",
			bg="#000000",
			fg="#ff0000",
			font=("Segoe UI", 32, "bold"),
		)
		self.black_screen_label.place(relx=0.5, rely=0.5, anchor="center")
		self._blink_black_screen()

	def _blink_black_screen(self):
		if not self.black_screen or not self.black_screen.winfo_exists():
			return
		self.black_screen_blink_on = not self.black_screen_blink_on
		bg_color = "#ff0000" if self.black_screen_blink_on else "#000000"
		fg_color = "#000000" if self.black_screen_blink_on else "#ff0000"

		self.black_screen.configure(bg=bg_color)
		self.black_screen_label.configure(bg=bg_color, fg=fg_color)
		self.after(500, self._blink_black_screen)

	def _update_black_screen_timer(self):
		self.black_screen_seconds -= 1
		if self.countdown_label and self.countdown_label.winfo_exists():
			self.countdown_label.configure(text=f"Таймер: {self.black_screen_seconds} s")
		if self.black_screen_seconds <= 0:
			self.destroy()
			return
		self.after(1000, self._update_black_screen_timer)

	def run(self):
		self.mainloop()


def main():
	mutex = acquire_single_instance()
	if mutex is None:
		return

	kernel32, mutex_handle = mutex
	audio_stop_event = threading.Event()
	try:
		threading.Thread(target=play_startup_audio, args=(audio_stop_event,), daemon=True).start()
		monitors = get_monitors()
		secondary_monitor = monitors[1] if len(monitors) > 1 else None
		MonitorApp(get_ip_location(), secondary_monitor).run()
	finally:
		audio_stop_event.set()
		kernel32.CloseHandle(mutex_handle)


if __name__ == "__main__":
	main()