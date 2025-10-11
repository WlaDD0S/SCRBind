# -*- coding: utf-8 -*-
import re
import time
import traceback
from tkinter import Tk, Label, Entry, Text, END, StringVar, ttk
import pygetwindow as gw
import keyboard
import pytesseract
from PIL import ImageGrab
import os
import cv2
import numpy as np

class SCRBot:
    # [ИЗМЕНЕНО] Все настройки вынесены в один словарь для удобства
    CONFIG = {
        "tesseract_path": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        "game_window_title": "Roblox",
        "ocr_bbox": (1730, 450, 1840, 520),
        "intervals": {
            "main": 100,
            "ocr": 200,
        },
        "cooldowns": {
            "TRTS": 5.0, "CD": 5.0, "RA": 5.0,
            "Open LD": 4.5, "Open PD": 2.0, "Whistle": 4.0, "Close PD": 8.0, "Close LD": 4.5, "Torch": 2.0, "Buzzer (Guard)": 2.0,
            "AWS": 0.5, "SPAD": 2.0, "Close Doors": 2.0, "Buzzer (Driver)": 1.5, "Open Doors": 1.5
        },
        "pixel_checks": {
            "TRTS": (1710, 605, (232, 74, 182)), "CD": (1785, 605, (232, 74, 182)), "RA": (1860, 605, (232, 74, 182)),
            "Open LD": (143, 570, (246, 165, 2)), "Open PD": (120, 500, (234, 0, 0)), "Whistle": (1720, 595, (232, 74, 182)), "Close PD": (120, 600, (0, 86, 223)), "Torch": (1795, 595, (232, 74, 182)), "Close LD": (131, 725, (236, 244, 252)), "Buzzer (Guard)": (120, 405, (0, 233, 233)),
            "AWS": (1765, 850, (255, 170, 0)), "SPAD": (1670, 940, (255, 61, 61)), "Close Doors": (1400, 690, (232, 74, 182)), "Buzzer (Driver)": (350, 760, (232, 74, 182)), "Open Doors": (1400, 690, (45, 142, 249)),
        }
    }

    def __init__(self, root):
        self.root = root
        self.running = False
        self.role = "Off"
        self.last_seen_code = ""
        self.pixel_cooldowns = {}
        
        self._setup_tesseract()

        self.role_messages = {
            "Guarding": ["Someone need GD?", "Nearest station?", "[ST DS] Safe shift!"],
            "Dispatching": ["[HC] Safe trip!", "[HC & GD] Safe trip!"],
            "Driving": ["I need GD", "Nearest station - ST", "[ST DS] Safe shift!"],
            "Off": ["Выберите роль!"]
        }
        
        self.role_key_map = {
            "Guarding": ["Open LD", "Close LD", "Whistle", "Close PD", "Torch", "Open PD", "Buzzer (Guard)"],
            "Dispatching": ["TRTS", "CD", "RA"],
            "Driving": ["AWS", "SPAD", "Close Doors", "Buzzer (Driver)", "Open Doors"],
        }
        
        self.action_to_key_map = {
            "TRTS": "q", "CD": "t", "Open LD": "e", "Close LD": "e", "Whistle": "q",
            "Open PD": "t", "Close PD": "y", "Torch": "r", "AWS": "q", "Close Doors": "t",
            "Open Doors": "t", "Buzzer (Driver)": "t", "SPAD": "q"
        }

        self._build_gui()
        self._register_hotkeys()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_tesseract(self):
        try:
            tesseract_path = self.CONFIG["tesseract_path"]
            if not os.path.isfile(tesseract_path):
                self.log(f"⚠️ Tesseract не найден по пути: {tesseract_path}")
                self.log("Проверьте путь в CONFIG или установите Tesseract-OCR.")
                return
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        except Exception as e:
            self.log(f"⚠️ Критическая ошибка при настройке Tesseract: {e}")

    def _build_gui(self):
        r = self.root
        r.title("SCRBindv2.0")
        r.geometry("300x270")
        r.configure(bg="black")
        r.attributes("-topmost", True)

        Label(r, text="Режим", fg="white", bg="black", font=("Arial", 12, "bold")).place(x=10, y=10)
        self.role_var = StringVar(value="Off")
        role_box = ttk.Combobox(r, textvariable=self.role_var, values=list(self.role_messages.keys()), state="readonly")
        role_box.place(x=10, y=35, width=120)
        role_box.bind("<<ComboboxSelected>>", self._on_role_change)

        self.code_label = Label(r, text="HeadCode", fg="white", bg="black", font=("Arial", 12, "bold"))
        self.code_var = StringVar()
        self.code_edit = Entry(r, textvariable=self.code_var, width=10, justify="center", bg="white")

        def validate_code(new_value):
            if new_value == "": return True
            return bool(re.match(r"^[1-9]?[A-Z]?[0-9]{0,2}$", new_value.upper()))
        
        vcmd = (r.register(validate_code), "%P")
        self.code_edit.config(validate="key", validatecommand=vcmd)

        def on_code_change(*_):
            self.code_var.set(self.code_var.get().upper())
        self.code_var.trace_add("write", on_code_change)

        self.station_label = Label(r, text="Станция", fg="white", bg="black", font=("Arial", 12, "bold"))
        self.station_var = StringVar()
        self.station_box = ttk.Combobox(r, textvariable=self.station_var, values=["Stepford Central", "Newry Harbour", "Connolly", "..."], state="readonly")

        Label(r, text="Текст", fg="white", bg="black", font=("Arial", 12, "bold")).place(x=10, y=70)
        self.text_var = StringVar()
        self.text_box = ttk.Combobox(r, textvariable=self.text_var, values=[], state="readonly")
        self.text_box.place(x=10, y=95, width=180)

        Label(r, text="Лог", fg="white", bg="black", font=("Arial", 12, "bold")).place(x=10, y=130)
        self.log_box = Text(r, height=6, width=46, fg="white", bg="black", font=("Arial", 8, "bold"))
        self.log_box.place(x=10, y=155)

    def log(self, *args):
        msg = " ".join(str(a) for a in args)
        self.log_box.insert(END, f"{msg}\n")
        self.log_box.see(END)

    def _register_hotkeys(self):
        keyboard.add_hotkey("f6", self._toggle_visibility)
        keyboard.add_hotkey("f7", self.messages)
        self.log("[F6] скрыть/показать | [F7] отправить")

    def _toggle_visibility(self):
        if self.root.winfo_viewable():
            self.root.withdraw()
        else:
            self.root.deiconify()

    def _on_role_change(self, *_):
        self.role = self.role_var.get()
        vals = self.role_messages.get(self.role, [])
        self.text_box["values"] = vals
        if vals:
            self.text_box.current(0)
            self.text_var.set(vals[0])
        self._toggle_fields()
        if self.role == "Off":
            self.stop()
        else:
            self.start()

    def _toggle_fields(self):
        for w in [self.code_edit, self.code_label, self.station_box, self.station_label]:
            w.place_forget()
        if self.role == "Dispatching":
            self.code_label.place(x=160, y=10)
            self.code_edit.place(x=160, y=35)
        elif self.role in ["Guarding", "Driving"]:
            self.station_label.place(x=160, y=10)
            self.station_box.place(x=160, y=35, width=120)

    def is_game_focused(self):
        try:
            win = gw.getActiveWindow()
            return bool(win and self.CONFIG["game_window_title"].lower() in win.title.lower())
        except Exception:
            return False

    def send_key(self, key):
        if not self.is_game_focused():
            self.log("⛔ Roblox не в фокусе")
            return
        try:
            keyboard.press_and_release(key)
        except Exception as e:
            self.log(f"⚠️ Ошибка отправки клавиши {key}: {e}")

    def send_input(self, text):
        if not self.is_game_focused():
            self.log("⛔ Roblox не в фокусе")
            return
        keyboard.press('/')
        time.sleep(0.1)
        keyboard.release('/')
        time.sleep(0.1)
        keyboard.write(text)
        time.sleep(0.5)
        keyboard.press('Enter')
        time.sleep(0.1)
        keyboard.release('Enter')
        self.log(f"💬 {text}")

    # [ИЗМЕНЕНО] Полностью переработанная функция OCR
    def ocr_task(self):
        if not self.running or self.role != "Dispatching":
            return
        try:
            pil_img = ImageGrab.grab(bbox=self.CONFIG["ocr_bbox"])
            cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            inverted = cv2.bitwise_not(gray)
            _, thresh = cv2.threshold(inverted, 128, 255, cv2.THRESH_BINARY)
            custom_config = r'--psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            text = pytesseract.image_to_string(thresh, config=custom_config).strip()
            
            # Валидация и обновление
            if re.fullmatch(r"[1239][A-Z][0-9]{2}", text) and text != self.last_seen_code:
                self.log(f"✅ HeadCode: {text}")
                self.code_var.set(text)
                self.last_seen_code = text
        except Exception as e:
            self.log(f"OCR error: {e}")
        finally:
            if self.running:
                self.root.after(self.CONFIG["intervals"]["ocr"], self.ocr_task)


    def messages(self):
        if not self.is_game_focused():
            self.log("⛔ Roblox не в фокусе")
            return
        msg = self.text_var.get()
        station = self.station_var.get()
        headcode = self.code_var.get()
        
        if "[ST DS]" in msg and station:
            msg = msg.replace("[ST DS]", f"[{station} DS]")
        elif "[HC & GD]" in msg and headcode:
            msg = msg.replace("[HC & GD]", f"[{headcode} & GD]")
        elif "[HC]" in msg and headcode:
            msg = msg.replace("[HC]", f"[{headcode}]")
        elif "ST" in msg and station:
            msg = msg.replace("ST", station)
            
        if msg not in self.role_messages.get(self.role, []):
            self.send_input(msg)
        else:
            self.send_input(msg)


    def _clear_headcode(self):
        self.code_var.set("")
        self.last_seen_code = ""

    def main_task(self):
        if not self.running or not self.is_game_focused():
            if self.running:
                self.root.after(self.CONFIG["intervals"]["main"], self.main_task)
            return

        try:
            screenshot = ImageGrab.grab()
            now = time.time()
            
            keys_to_check = self.role_key_map.get(self.role, [])
            
            for action in keys_to_check:
                if action not in self.CONFIG["pixel_checks"]: continue
                
                x, y, target_color = self.CONFIG["pixel_checks"][action]
                
                if screenshot.getpixel((x, y)) == target_color:
                    last_time = self.pixel_cooldowns.get(action, 0)
                    cooldown = self.CONFIG["cooldowns"].get(action, 2.0)
                    
                    if now - last_time >= cooldown:
                        self.pixel_cooldowns[action] = now
                        
                        if action == "RA":
                            time.sleep(0.2)
                            self.send_key("r")
                            self.log("✅ RA — R")
                            self.root.after(2500, self.messages)
                            self.root.after(5000, self._clear_headcode)
                        elif action in self.action_to_key_map:
                            key_to_press = self.action_to_key_map[action]
                            time.sleep(1)
                            self.send_key(key_to_press)
                            self.log(f"✅ {action} — {key_to_press.upper()}")

        except Exception as e:
            self.log("Main loop error:")
            self.log(traceback.format_exc())
        finally:
            if self.running:
                self.root.after(self.CONFIG["intervals"]["main"], self.main_task)
    
    def start(self):
        if self.running: return
        self.running = True
        self.log(f"▶️ Запуск режима: {self.role}")
        self.root.after(self.CONFIG["intervals"]["main"], self.main_task)
        if self.role == "Dispatching":
            self.root.after(self.CONFIG["intervals"]["ocr"], self.ocr_task)

    def stop(self):
        if not self.running: return
        self.running = False
        self.log("⏹️ Стоп")

    def on_close(self):
        self.stop()
        keyboard.unhook_all_hotkeys()
        self.root.destroy()

if __name__ == "__main__":
    root = Tk()
    app = SCRBot(root)
    root.mainloop()