# -*- coding: utf-8 -*-
import re
import time
import pytesseract
import keyboard
import threading
import traceback
import pygetwindow as gw
from tkinter import *
from tkinter import ttk
from PIL import ImageGrab, ImageOps, ImageEnhance, ImageFilter

# --- Настройка pytesseract ---
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class SCRBot:
    def __init__(self, root):
        self.root = root
        self.role = "Off"
        self.text_choice = ""
        self.station = ""
        self.headcode = ""
        self.last_seen_code = ""
        self.last_seen_time = 0.0
        self.pixel_cooldowns = {}

        # Настройки
        self.pixel_cooldown_time = 2.0
        self.pixel_cooldown_times = {
            "TRTS": 5.0, "CD": 5.0, "RA": 5.0, "Whistle": 3.5, "Buzzer (Guard)": 2.0,
            "AWS": 1.0, "Open LD": 4.5, "Close LD": 4.5, "Open PD": 2.0, "Close PD": 4.0,
            "Torch": 2.0, "Close Doors": 2.0, "Buzzer (Driver)": 1.5, "Open Doors": 1.5
        }

        self.running = False
        self.require_focus = True
        self.game_window_title = "Roblox"
        self.ocr_interval = 400
        self.main_interval = 100
        self.ocr_bbox = (1730, 450, 1840, 520)

        # Координаты пикселей
        self.pixel_checks = {
            "Open LD": (143, 570, (246, 165, 2)),
            "Whistle": (1720, 595, (232, 74, 182)),
            "Close PD": (120, 600, (0, 86, 223)),
            "Buzzer (Guard)": (120, 400, (0, 220, 220)),
            "Torch": (1795, 595, (232, 74, 182)),
            "Close LD": (102, 725, (237, 245, 253)),
            "Open PD": (120, 500, (234, 0, 0)),
            "TRTS": (1710, 605, (232, 74, 182)),
            "CD": (1785, 605, (232, 74, 182)),
            "RA": (1860, 605, (232, 74, 182)),
            "AWS": (1765, 850, (255, 170, 0)),
            "Close Doors": (1400, 690, (232, 74, 182)),
            "Buzzer (Driver)": (350, 760, (232, 74, 182)),
            "Open Doors": (1400, 690, (45, 142, 249)),
        }

        self.role_messages = {
            "Guarding": ["Someone need GD?", "Nearest station?", "[ST DS] Safe shift!"],
            "Dispatching": ["[HC] Safe trip!", "[HC & GD] Safe trip!"],
            "Driving": ["Free GD?", "Nearest station - ST", "[ST DS] Safe shift!"],
            "Off": ["Выберите роль!"]
        }

        self._build_gui()
        self._register_hotkeys()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------------- GUI ----------------
    def _build_gui(self):
        r = self.root
        r.title("SCRBind")
        r.geometry("300x260")
        r.configure(bg="black")
        r.attributes("-topmost", True)

        Label(r, text="Режим", fg="white", bg="black", font=("Arial", 12, "bold")).place(x=10, y=10)
        self.role_var = StringVar(value="Off")
        role_box = ttk.Combobox(r, textvariable=self.role_var, values=list(self.role_messages.keys()), state="readonly")
        role_box.place(x=10, y=35, width=120)
        role_box.bind("<<ComboboxSelected>>", self._on_role_change)

        self.code_text = Label(r, text="HeadCode", fg="white", bg="black", font=("Arial", 12, "bold"))
        self.code_var = StringVar()
        self.code_edit = Entry(r, textvariable=self.code_var, width=10, justify="center")


        self.text_text = Label(r, text="Текст", fg="white", bg="black", font=("Arial", 12, "bold"))
        self.text_var = StringVar()
        self.text_box = ttk.Combobox(r, textvariable=self.text_var, values=[], state="readonly")
        self.text_box.bind("<<ComboboxSelected>>", self._on_text_change)

        self.station_text = Label(r, text="Станция", fg="white", bg="black", font=("Arial", 12, "bold"))
        self.station_var = StringVar()
        self.station_box = ttk.Combobox(r, textvariable=self.station_var, values=[ "Stepford Central", "Newry Harbour", "Connolly", "Cambridge Street Parkway", "Esterfield", "Benton", "St Helens Bridge", "Stepford East", "Four Ways", "Stepford Victoria", "Airport Central", "Elsemere Junction", "Leighton City", "City Hospital", "Financial Quarter", "Beechley", "High Street", "Willowfield", "Hemdon Park", "Whitefield", "Whitefield Lido", "Stepford UFC", "Woodhead Lane", "Houghton Rake", "New Harrow", "Elsemere Pond", "Berrily", "East Berrily", "Beaulieu Park", "Morganstown", "Angel Pass", "Bodin", "Coxly", "Port Benton", "Benton Bridge", "Airport Parkway", "Hampton Hargate", "Upper Staploe", "Water Newton", "Rocket Parade", "Leighton Stepford Road", "Edgemead", "Faymere", "Westercoast", "Millcastle Racecourse", "Millcastle", "Westwyvern", "Northshore", "Llyn-by-the-Sea", "Newry", "Eden Quay", "Faraday Road", "West Benton", "Ashlan Park", "Airport West", "James Street", "Morganstown Docks", "Whitney Green", "Greenslade", "Terminal 1", "Terminal 2", "Terminal 3"])
        self.station_box.bind("<<ComboboxSelected>>", self._on_station_change)

        Label(r, text="Лог", fg="white", bg="black", font=("Arial", 12, "bold")).place(x=10, y=130)
        self.log_box = Text(r, height=6, width=46, fg="white", bg="black", font=("Arial", 8, "bold"))
        self.log_box.place(x=10, y=155)

    def log(self, *args):
        msg = " ".join(str(a) for a in args)
        self.log_box.insert(END, msg + "\n")
        self.log_box.see(END)

    # ---------------- Hotkeys ----------------
    def _register_hotkeys(self):
        try:
            keyboard.add_hotkey("f6", self._toggle_visibility)
            keyboard.add_hotkey("f7", lambda: self.root.after(0, self.messages))
            self.log("[F6] скрыть/показать  |  [F7] отправить сообщение")
        except Exception as e:
            self.log("Ошибка hotkeys:", e)

    def _toggle_visibility(self):
        if self.root.state() == "withdrawn":
            self.root.deiconify()
        else:
            self.root.withdraw()

    # ---------------- Выборы ----------------
    def _on_role_change(self, *_):
        self.role = self.role_var.get()
        vals = self.role_messages.get(self.role, [])
        self.text_box["values"] = vals
        if vals:
            self.text_box.current(0)
            self.text_choice = vals[0]

        # Скрыть всё по умолчанию
        self.station_box.place_forget()
        self.station_text.place_forget()
        self.code_edit.place_forget()
        self.code_text.place_forget()
        self.text_text.place_forget()
        self.text_box.place_forget()

        if self.role == "Off":
            self.stop()
        else:
            self.start()

        if self.role == "Dispatching":
            self.code_edit.place(x=160, y=35)
            self.code_text.place(x=160, y=10)
            self.text_text.place(x=10, y=70)
            self.text_box.place(x=10, y=95, width=120)
        elif self.role in ["Guarding", "Driving"]:
            self.station_box.place(x=160, y=35, width=120)
            self.station_text.place(x=160, y=10)
            self.text_text.place(x=10, y=70)
            self.text_box.place(x=10, y=95, width=120)

        

    def _on_text_change(self, *_):
        self.text_choice = self.text_var.get()

    def _on_station_change(self, *_):
        self.station = self.station_var.get()

    # ---------------- Roblox Focus ----------------
    def is_game_focused(self):
        try:
            win = gw.getActiveWindow()
            return bool(win and "roblox" in win.title.lower())
        except Exception:
            return False

    def pixel_ready(self, key, cooldown=None):
        cooldown = cooldown or self.pixel_cooldown_times.get(key, self.pixel_cooldown_time)
        now = time.time()
        last = self.pixel_cooldowns.get(key, 0)
        if now - last >= cooldown:
            self.pixel_cooldowns[key] = now
            return True
        return False

    # ---------------- Эмуляция клавиш ----------------
    def send_key(self, key):
        if not self.is_game_focused():
            self.log("⛔ Roblox не в фокусе")
            return
        try:
            keyboard.press(key)
            time.sleep(0.05)
            keyboard.release(key)
        except Exception as e:
            self.log("Keyboard error:", e)

    def send_message(self, msg):
        if not self.is_game_focused():
            self.log("❌ Roblox не в фокусе — сообщение не отправлено")
            return
        try:
            keyboard.press('/')
            time.sleep(0.05)
            keyboard.release('/')
            keyboard.write(msg)
            keyboard.press('enter')
            time.sleep(0.05)
            keyboard.release('enter')
            self.log("💬", msg)
        except Exception as e:
            self.log("Send message error:", e)

    # ---------------- OCR ----------------
    def ocr_task(self):
        if not self.running or self.role != "Dispatching":
            self.root.after(self.ocr_interval, self.ocr_task)
            return

        try:
            img = ImageGrab.grab(bbox=self.ocr_bbox)
            img = ImageOps.grayscale(img)
            img = ImageEnhance.Contrast(img).enhance(2.0)
            img = img.filter(ImageFilter.SHARPEN)

            raw_text = pytesseract.image_to_string(img, config="--psm 7").strip().upper()
            raw_text = raw_text.replace(" ", "").replace("\n", "")

            if re.fullmatch(r"[1239][A-Z][0-9]{2}", raw_text):
                if raw_text != self.last_seen_code:
                    self.log(f"✅ Новый HeadCode: {raw_text}")
                    self.code_var.set(raw_text)
                self.headcode = raw_text
                self.last_seen_code = raw_text
                self.last_seen_time = time.time()
            else:
                pass

        except Exception as e:
            self.log("OCR error:", e)
        finally:
            self.root.after(self.ocr_interval, self.ocr_task)

    # ---------------- Messages ----------------
    def messages(self):
        if not self.is_game_focused():
            self.log("Roblox не активно — отмена")
            return
        r, t = self.role, self.text_choice
        msg = ""
        if r == "Guarding":
            if t == "[ST DS] Safe shift!":
                msg = f"[{self.station} DS] Safe shift!"
            else:
                msg = t
        elif r == "Dispatching":
            if t == "[HC] Safe trip!":
                msg = f"[{self.headcode}] Safe trip!"
            elif t == "[HC & GD] Safe trip!":
                msg = f"[{self.headcode} & GD] Safe trip!"
        elif r == "Driving":
            if t == "Nearest station - ST":
                msg = f"Nearest station - {self.station}"
            elif t == "[ST DS] Safe shift!":
                msg = f"[{self.station} DS] Safe shift!"
            else:
                msg = t
        if msg:
            self.send_message(msg)

    # ---------------- Основной цикл ----------------
    def main_task(self):
        if not self.running:
            return
        if not self.is_game_focused():
            self.root.after(self.main_interval, self.main_task)
            return
        try:
            r = self.role
            if r == "Guarding":
                if self._pixel_is("Open LD") and self.pixel_ready("Open LD"):
                    self.log("✅ Open LD — E")
                    self.send_key("e")
                elif self._pixel_is("Close LD") and self.pixel_ready("Close LD"):
                    self.log("✅ Close LD — E")
                    self.send_key("e")
                elif self._pixel_is("Whistle") and self.pixel_ready("Whistle"):
                    self.log("✅ Whistle — Q")
                    self.send_key("q")
                elif self._pixel_is("Close PD") and self.pixel_ready("Close PD"):
                    self.log("✅ Close PD — Y")
                    self.send_key("y")
                elif self._pixel_is("Torch") and self.pixel_ready("Torch"):
                    self.log("✅ Torch — R")
                    self.send_key("r")
                elif self._pixel_is("Open PD") and self.pixel_ready("Open PD"):
                    self.log("✅ Open PD — T")
                    self.send_key("t")

            elif r == "Dispatching":
                if self._pixel_is("TRTS") and self.pixel_ready("TRTS"):
                    self.log("✅ TRTS — Q")
                    self.send_key("q")
                elif self._pixel_is("CD") and self.pixel_ready("CD"):
                    self.log("✅ CD — T")
                    self.send_key("t")
                elif self._pixel_is("RA") and self.pixel_ready("RA"):
                    self.log("✅ RA — R")
                    self.send_key("r")
                    threading.Timer(2.5, self.messages).start()

            elif r == "Driving":
                if self._pixel_is("AWS") and self.pixel_ready("AWS"):
                    self.log("✅ AWS — Q")
                    self.send_key("q")
                elif self._pixel_is("Close Doors") and self.pixel_ready("Close Doors"):
                    self.log("✅ Close Doors — T")
                    self.send_key("t")
                elif self._pixel_is("Buzzer (Driver)") and self.pixel_ready("Buzzer (Driver)"):
                    self.log("✅ Buzzer — T")
                    self.send_key("t")
                elif self._pixel_is("Open Doors") and self.pixel_ready("Open Doors"):
                    self.log("✅ Open Doors — T")
                    self.send_key("t")

        except Exception as e:
            self.log("Main loop error:", e)
            traceback.print_exc()
        finally:
            self.root.after(self.main_interval, self.main_task)

    def _pixel_is(self, key):
        try:
            import pyautogui
            x, y, color = self.pixel_checks[key]
            return pyautogui.pixel(x, y) == color
        except Exception:
            return False

    # ---------------- Управление ----------------
    def start(self):
        if self.running:
            return
        self.running = True
        self.log("▶️ Старт — режим:", self.role)
        self.root.after(0, self.ocr_task)
        self.root.after(0, self.main_task)

    def stop(self):
        if not self.running:
            return
        self.running = False
        self.log("⏹️ Стоп")

    def on_close(self):
        self.stop()
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        self.root.destroy()


# --- Запуск ---
if __name__ == "__main__":
    root = Tk()
    root.iconbitmap(r"C:\Users\WlaDD0S\Downloads\pip\SCR.ico")
    app = SCRBot(root)
    root.mainloop()