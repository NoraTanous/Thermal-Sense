# -*- coding: utf-8 -*-

import tkinter as tk
from PIL import Image, ImageTk
import os
import threading
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')
from io import BytesIO

from ThermalSenseInput import ThermalSenseInput
from ObjectThermalSenseRunner import ThermalSenseRunner
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ThermalSenseGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ThermalSense GUI")
        self.root.geometry("1366x768")
        self.root.configure(bg="#1e1e2f")

        self.running = False
        self.thread = None

        self.build_gui()
        self.thermal_sense = ThermalSenseRunner(external_ax=self.ax, external_canvas=self.canvas, root=self.root)

    def build_gui(self):
        # === Top Frame ===
        self.top_frame = tk.Frame(self.root, bg="#1e1e2f")
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.root.grid_columnconfigure(0, weight=1)

        self.start_btn = tk.Button(self.top_frame, text="Run", bg="green", fg="white", command=self.start_algorithm, width=10)
        self.start_btn.grid(row=0, column=0, padx=5)

        self.stop_btn = tk.Button(self.top_frame, text="Stop", bg="red", fg="white", command=self.stop_all, width=10)
        self.stop_btn.grid(row=0, column=1, padx=5)

        self.exit_btn = tk.Button(self.top_frame, text="Exit", command=self.root.quit, bg="#6a040f", fg="white", width=10)
        self.exit_btn.grid(row=0, column=2, padx=5)

        # === Middle Frame ===
        self.middle_frame = tk.Frame(self.root, bg="#1e1e2f")
        self.middle_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.root.grid_rowconfigure(1, weight=1)
        self.middle_frame.grid_columnconfigure(0, weight=1)

        self.fig = plt.Figure(figsize=(10, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.middle_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=0, column=0, sticky="nsew")

        self.load_image_on_canvas("Pictures/Welcome.png")

        # === Bottom Frame ===
        self.bottom_frame = tk.Frame(self.root, bg="#1e1e2f")
        self.bottom_frame.grid(row=2, column=0, pady=10)

        ts_icon = Image.open("Pictures/ThermalSenseResults.png").resize((40, 40))
        ts_icon_tk = ImageTk.PhotoImage(ts_icon)
        self.ts_icon_tk = ts_icon_tk

        self.open_ts_results_btn = tk.Button(self.bottom_frame, text=" ThermalSense Results", image=ts_icon_tk, compound="left",
                                             command=self.open_thermal_sense_results, bg="#6c757d", fg="white", padx=10, pady=5)
        self.open_ts_results_btn.grid(row=0, column=0, padx=20)

        tso_icon = Image.open("Pictures/ThermalSoundResults.png").resize((40, 40))
        tso_icon_tk = ImageTk.PhotoImage(tso_icon)
        self.tso_icon_tk = tso_icon_tk

        self.open_tso_results_btn = tk.Button(self.bottom_frame, text=" ThermalSound Results", image=tso_icon_tk, compound="left",
                                              command=self.open_thermal_sound_results, bg="#6c757d", fg="white", padx=10, pady=5)
        self.open_tso_results_btn.grid(row=0, column=1, padx=20)

    def load_image_on_canvas(self, path):
        try:
            # Remove colorbar if it exists
            if hasattr(self, 'colorbar'):
                self.colorbar.remove()
                del self.colorbar

            # Convert current canvas image to PIL image (if any)
            self.fig.canvas.draw()
            buf = self.fig.canvas.buffer_rgba()
            w, h = self.fig.canvas.get_width_height()
            current_img = Image.frombytes("RGBA", (w, h), buf.tobytes())

            # Load new image and resize to match
            target_img = Image.open(path).convert("RGBA").resize((w, h))

            # Create blend frames for smooth fade
            for alpha in np.linspace(0, 1, 15):
                blended = Image.blend(current_img, target_img, alpha)
                self.ax.clear()
                self.ax.imshow(blended)
                self.ax.axis('off')
                self.canvas.draw()
                self.root.update_idletasks()
                time.sleep(0.02)  # 15 steps × 20ms = ~0.3s

        except Exception as e:
            print(f"[ERROR loading image with fade] {e}")

    def start_algorithm(self):
        self.stop_all(show_stop_background=False)

        print("Starting ThermalSense...")
        # Freshly recreate the runner instance here
        self.thermal_sense = ThermalSenseRunner(external_ax=self.ax, external_canvas=self.canvas, root=self.root)
    
        self.thread = threading.Thread(target=self.thermal_sense.run)
        self.thread.start()



    def stop_all(self, show_stop_background=True):
        self.running = False

        if self.thermal_sense:
            self.thermal_sense.stop()

        def wait_thread():
            if self.thread and self.thread.is_alive():
                self.thread.join()
            self.thread = None
            if show_stop_background:
                self.load_image_on_canvas("Pictures/StopBackground.png")

        threading.Thread(target=wait_thread, daemon=True).start()

    def open_thermal_sense_results(self):
        self.open_latest_results_by_type("ThermalSense")

    def open_thermal_sound_results(self):
        self.open_latest_results_by_type("ThermalSound")

    def open_latest_results_by_type(self, algo_name):
        base_dir = os.path.join("Results", algo_name)
        latest_folder = self.get_latest_subfolder(base_dir)
        if latest_folder:
            os.system(f'xdg-open "{latest_folder}"')
        else:
            print(f"[WARNING] No result folders found for {algo_name}.")

    def get_latest_subfolder(self, base_path):
        try:
            full_path = os.path.join(os.getcwd(), base_path)
            subdirs = [os.path.join(full_path, d) for d in os.listdir(full_path)
                       if os.path.isdir(os.path.join(full_path, d))]
            if not subdirs:
                return None
            return max(subdirs, key=os.path.getmtime)
        except Exception as e:
            print(f"[ERROR] Could not get latest folder: {e}")
            return None


if __name__ == '__main__':
    root = tk.Tk()
    app = ThermalSenseGUI(root)
    root.mainloop()
