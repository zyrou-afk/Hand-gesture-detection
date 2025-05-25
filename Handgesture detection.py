import tkinter as tk
from tkinter import filedialog, messagebox
import json
import threading
import time
import subprocess
import cv2
import mediapipe as mp
import os
import keyboard

SAVE_FILE = "gestures_config.json"

def normalize_key_name(key_name):
    mapping = {
        "control_l": "ctrl",
        "control_r": "ctrl",
        "shift_l": "shift",
        "shift_r": "shift",
        "alt_l": "alt",
        "alt_r": "alt",
        "windows": "win",
        "command": "cmd",
    }
    return mapping.get(key_name, key_name)

class GestureConfigurator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gesture Detection")
        self.geometry("460x650")
        self.configure(bg="#1e1e2f")

        self.configs = []
        self.load_configs()

        # Variables doigts
        self.finger_vars = {
            "Index": tk.BooleanVar(),
            "Middle": tk.BooleanVar(),
            "Ring": tk.BooleanVar(),
            "Pinky": tk.BooleanVar()
        }

        # Header
        tk.Label(self, text="Gesture Launcher", font=("Segoe UI", 16, "bold"), fg="#90caf9", bg="#1e1e2f").pack(pady=(10, 6))

        # Cadre doigts
        frame_fingers = tk.Frame(self, bg="#1e1e2f")
        frame_fingers.pack(padx=10, pady=5, fill="x")
        tk.Label(frame_fingers, text="Select Fingers:", fg="white", bg="#1e1e2f", font=("Segoe UI", 11)).pack(anchor="w")
        fingers_frame = tk.Frame(frame_fingers, bg="#1e1e2f")
        fingers_frame.pack(anchor="w", pady=3)
        for name, var in self.finger_vars.items():
            cb = tk.Checkbutton(fingers_frame, text=name, variable=var, fg="white", bg="#1e1e2f", selectcolor="#4caf50", font=("Segoe UI", 10))
            cb.pack(side="left", padx=6)

        # Chemin du programme
        frame_path = tk.Frame(self, bg="#1e1e2f")
        frame_path.pack(padx=10, pady=5, fill="x")
        tk.Label(frame_path, text="Program path (The program you want to be executed after the gesture):", fg="white", bg="#1e1e2f", font=("Segoe UI", 11)).pack(anchor="w")
        path_inner = tk.Frame(frame_path, bg="#1e1e2f")
        path_inner.pack(fill="x")
        self.path_entry = tk.Entry(path_inner, font=("Segoe UI", 11))
        self.path_entry.pack(side="left", fill="x", expand=True)
        tk.Button(path_inner, text="Browse", command=self.browse_file, bg="#3a3a5c", fg="white", font=("Segoe UI", 9), width=8).pack(side="left", padx=6)

        # Raccourci clavier
        frame_shortcut = tk.Frame(self, bg="#1e1e2f")
        frame_shortcut.pack(padx=10, pady=5, fill="x")
        tk.Label(frame_shortcut, text="Shortcut (The shortcut you want to be executed after the gesture):", fg="white", bg="#1e1e2f", font=("Segoe UI", 11)).pack(anchor="w")
        self.shortcut_entry = tk.Entry(frame_shortcut, font=("Segoe UI", 11))
        self.shortcut_entry.pack(fill="x", pady=3)
        self.shortcut_entry.insert(0, "Click here then type shortcut")
        self.shortcut_entry.config(state="readonly", fg="grey")
        self.recording_shortcut = False
        self.shortcut_keys = []
        self.shortcut_entry.bind("<Button-1>", self.start_recording_shortcut)

        # Ajouter geste
        tk.Button(self, text="Add Gesture", command=self.add_gesture, bg="#4caf50", fg="white", font=("Segoe UI", 12, "bold")).pack(pady=6)

        # Liste gestes
        frame_list = tk.Frame(self, bg="#1e1e2f")
        frame_list.pack(padx=10, pady=5, fill="both", expand=True)
        tk.Label(frame_list, text="Configured Gestures:", fg="white", bg="#1e1e2f", font=("Segoe UI", 11)).pack(anchor="w")
        self.listbox = tk.Listbox(frame_list, font=("Segoe UI", 10), bg="#2e2e44", fg="white", selectbackground="#4caf50", height=6)
        self.listbox.pack(fill="both", expand=True, pady=4)
        tk.Button(self, text="Delete Selected", command=self.delete_selected, bg="#f44336", fg="white", font=("Segoe UI", 10)).pack(pady=(0,10))

        # Boutons Start / Stop
        frame_buttons = tk.Frame(self, bg="#1e1e2f")
        frame_buttons.pack(pady=6)
        self.start_btn = tk.Button(frame_buttons, text="Start Detection", command=self.start_detection, bg="#2196f3", fg="white", font=("Segoe UI", 12, "bold"), width=15)
        self.start_btn.pack(side="left", padx=6)
        self.stop_btn = tk.Button(frame_buttons, text="Stop Detection", command=self.stop_detection, bg="#e91e63", fg="white", font=("Segoe UI", 12, "bold"), width=15, state="disabled")
        self.stop_btn.pack(side="left", padx=6)

        self.running = False

        keyboard.hook(self.on_key_event)

        self.refresh_listbox()

    def browse_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)

    def get_finger_pattern(self):
        return [var.get() for var in self.finger_vars.values()]

    def start_recording_shortcut(self, event):
        if not self.recording_shortcut:
            self.recording_shortcut = True
            self.shortcut_keys = []
            self.shortcut_entry.config(state="normal", fg="red")
            self.shortcut_entry.delete(0, tk.END)
            self.shortcut_entry.insert(0, "Recording... Press keys (Esc to finish)")

    def on_key_event(self, event):
        if not self.recording_shortcut:
            return
        if event.event_type == "down":
            key = normalize_key_name(event.name)
            if key == "esc":
                self.recording_shortcut = False
                shortcut_str = "+".join(self.shortcut_keys)
                if shortcut_str == "":
                    shortcut_str = "Click here then type shortcut"
                    self.shortcut_entry.config(fg="grey")
                else:
                    self.shortcut_entry.config(fg="white")
                self.shortcut_entry.delete(0, tk.END)
                self.shortcut_entry.insert(0, shortcut_str)
                self.shortcut_entry.config(state="readonly")
                return
            if key not in self.shortcut_keys:
                self.shortcut_keys.append(key)
                self.shortcut_entry.delete(0, tk.END)
                self.shortcut_entry.insert(0, "+".join(self.shortcut_keys))

    def add_gesture(self):
        pattern = self.get_finger_pattern()
        path = self.path_entry.get().strip()
        shortcut = self.shortcut_entry.get().strip()

        if (not path) and (shortcut == "" or shortcut == "Click here then type shortcut"):
            messagebox.showerror("Error", "Please provide a valid program path or shortcut command.")
            return

        self.configs.append({"pattern": pattern, "path": path, "shortcut": shortcut})
        self.save_configs()
        self.refresh_listbox()

        # Reset inputs
        self.path_entry.delete(0, tk.END)
        self.shortcut_entry.config(state="readonly")
        self.shortcut_entry.delete(0, tk.END)
        self.shortcut_entry.insert(0, "Click here then type shortcut")
        self.shortcut_entry.config(fg="grey")
        for var in self.finger_vars.values():
            var.set(False)

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for conf in self.configs:
            fingers = [name for name, val in zip(self.finger_vars.keys(), conf["pattern"]) if val]
            target = conf["path"] if conf["path"] else conf["shortcut"]
            self.listbox.insert(tk.END, f"{fingers} -> {target}")

    def delete_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        index = sel[0]
        del self.configs[index]
        self.save_configs()
        self.refresh_listbox()

    def save_configs(self):
        with open(SAVE_FILE, 'w') as f:
            json.dump(self.configs, f)

    def load_configs(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                self.configs = json.load(f)

    def start_detection(self):
        if self.running:
            return
        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        threading.Thread(target=self.run_detection, daemon=True).start()

    def stop_detection(self):
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    def run_detection(self):
        mp_hands = mp.solutions.hands
        cap = cv2.VideoCapture(0)
        last_trigger_time = {}
        DELAY = 2  # secondes

        with mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7
        ) as hands:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    continue

                img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(img_rgb)
                current_time = time.time()

                if results.multi_hand_landmarks:
                    lm = results.multi_hand_landmarks[0].landmark
                    fingers = [
                        lm[8].y < lm[6].y,
                        lm[12].y < lm[10].y,
                        lm[16].y < lm[14].y,
                        lm[20].y < lm[18].y
                    ]
                    for conf in self.configs:
                        if fingers == conf["pattern"]:
                            key = conf.get("path") or conf.get("shortcut")
                            if key not in last_trigger_time or (current_time - last_trigger_time[key]) > DELAY:
                                if conf.get("path"):
                                    subprocess.Popen(f'"{conf["path"]}"', shell=True)
                                elif conf.get("shortcut"):
                                    keys = conf["shortcut"].split('+')
                                    for k in keys:
                                        keyboard.press(k.strip())
                                    for k in reversed(keys):
                                        keyboard.release(k.strip())
                                last_trigger_time[key] = current_time

                time.sleep(0.1)

        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    app = GestureConfigurator()
    app.mainloop()
