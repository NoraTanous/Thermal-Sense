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
from tkinter import ttk

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
        
        
        #-------------------        Custom mode extention       ----------------------------------
        self.options_visible = True
        self.build_options_panel()
        #_________________________________________________________________________________________

        self.build_gui()
        self.thermal_sense = ThermalSenseRunner(external_ax=self.ax, external_canvas=self.canvas, root=self.root)
        #-------------------        Custom mode extention       ----------------------------------
        self.validation_labels = []

        
        
    def build_options_panel(self):
        # ───────────────── Frame ──────────────────
        self.options_frame = tk.Frame(self.root, bg="white", bd=2, relief="ridge")
        self.options_frame.grid(row=0, column=1, rowspan=3,
                                sticky="ns", padx=(5, 10), pady=10)

        # Give each column some weight so headers & fields line-up
        for i in range(7):
            self.options_frame.grid_columnconfigure(i, weight=1)

        # ──────────────── Title ────────────────────
        tk.Label(self.options_frame,
                 text="ThermalSense Options",
                 font=("Arial", 12, "bold"),
                 bg="white").grid(row=0, column=0, columnspan=4, pady=(0, 10))

        # ───────────── Default-mode checkbox ───────
        self.default_mode_var = tk.BooleanVar(value=True)
        self.default_mode_check = tk.Checkbutton(
            self.options_frame,
            text="Default Mode",
            variable=self.default_mode_var,
            command=self.toggle_custom_mode,
            bg="white"
        )
        self.default_mode_check.grid(row=1, column=0, columnspan=7,
                                     sticky="w", pady=(0, 10))

        # ───────────── Sample-rate row ─────────────
        tk.Label(self.options_frame, text="Sample Rate:",
                 bg="white").grid(row=2, column=0, sticky="e", padx=(0, 5))
        self.sample_rate_entry = tk.Entry(self.options_frame, width=10)
        self.sample_rate_entry.insert(0, "44100")
        self.sample_rate_entry.grid(row=2, column=1, sticky="w")

        # ───────────── Column headers ──────────────
        hdr_style = dict(bg="white", font=("Arial", 10, "bold"))
        tk.Label(self.options_frame, text="Name", **hdr_style).grid(row=3, column=1)
        tk.Label(self.options_frame, text="Low [C]", **hdr_style).grid(row=3, column=2)
        tk.Label(self.options_frame, text="High [C]", **hdr_style).grid(row=3, column=3)
        tk.Label(self.options_frame, text="Color", **hdr_style).grid(row=3, column=4)
        tk.Label(self.options_frame, text="Freq",  **hdr_style).grid(row=3, column=5)

        # ───────────── Range-input rows ────────────
        self.range_entries = []
        default_rows = 3            # show 3 rows only
        self.max_rows = 7           # guard for add-button
        self.add_row_btn = tk.Button(self.options_frame, text="Add Range",
                                    command=self._add_range_row, bg="#28a745", fg="white")

        self.add_row_btn.grid(row=4 + default_rows, column=0, columnspan=7, pady=(6,2))
        
        
        

        # ───────────── Image-save checkbox ─────────
        self.image_save_var = tk.BooleanVar(value=True)
        self.image_save_checkbox = tk.Checkbutton(self.options_frame, text="Enable Image Saving",
                       variable=self.image_save_var,
                       bg="white")

        # ───────────── Logging checkboxes ──────────
        self.csv_log_var   = tk.BooleanVar(value=True)
        self.frame_save_var = tk.BooleanVar(value=True)
        self.sound_save_var = tk.BooleanVar(value=True)

        self.csv_checkbox = tk.Checkbutton(self.options_frame, text="Enable CSV Log",
                       variable=self.csv_log_var, bg="white")
                       
        self.frame_checkbox = tk.Checkbutton(self.options_frame, text="Enable Frame Capture Save",
                       variable=self.frame_save_var, bg="white")
        self.sound_checkbox = tk.Checkbutton(self.options_frame, text="Enable Sound File Save",
                       variable=self.sound_save_var, bg="white")
                       
        # Added Visual real-time Control
        self.visual_display_var = tk.BooleanVar(value=True)
        self.visual_display_checkbox = tk.Checkbutton(
            self.options_frame,
            text="Enable Real-Time Visual Display",
            variable=self.visual_display_var,
            bg="white"
        )


        # ───────────── Validate + Hide buttons ─────
        self.validate_btn = tk.Button(self.options_frame, text="Validate Data",
                                      command=self.validate_inputs,
                                      bg="#007bff", fg="white")
        self.validate_btn.grid(row=13, column=0, columnspan=7, pady=10)

        self.toggle_btn = tk.Button(self.options_frame,
                                    text="Hide ThermalSense Options",
                                    command=self.toggle_options_panel,
                                    bg="#6c757d", fg="white")
        self.toggle_btn.grid(row=14, column=0, columnspan=7)
        

        # ───────────── Initial enable/disable sync ─
        for i in range(default_rows):
            self._add_range_row()
        self._reposition_static_controls()
        self.toggle_custom_mode()
        
        # Force visibility for all option widgets
        self.image_save_checkbox.grid()
        self.csv_checkbox.grid()
        self.frame_checkbox.grid()
        self.sound_checkbox.grid()


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
        
        # ThermalSound Button enable/Disable

    #    tso_icon = Image.open("Pictures/ThermalSoundResults.png").resize((40, 40))
     #   tso_icon_tk = ImageTk.PhotoImage(tso_icon)
      #  self.tso_icon_tk = tso_icon_tk

       # self.open_tso_results_btn = tk.Button(self.bottom_frame, text=" ThermalSound Results", image=tso_icon_tk, compound="left",
      #                                        command=self.open_thermal_sound_results, bg="#6c757d", fg="white", padx=10, pady=5)
      #  self.open_tso_results_btn.grid(row=0, column=1, padx=20)

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
                self.canvas.draw_idle()
                self.root.update_idletasks()
                time.sleep(0.02)  # 15 steps × 20ms = ~0.3s

        except Exception as e:
            print(f"[ERROR loading image with fade] {e}")




    def stop_all(self, show_stop_background=True):
        self.running = False

        if self.thermal_sense:
            self.thermal_sense.stop()
        if self.options_frame:
            self.options_frame.grid()
            self.options_visible = True
    
        self.start_btn.config(state=tk.NORMAL)


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
            
    # ----------------------------------    Custom Mode Helper methods      -------------------------------------------------
    
    def toggle_custom_mode(self):
        enable = not self.default_mode_var.get()
        for _, name, low, high, color, freq, _ in self.range_entries:
            name.config(state="normal" if enable else "disabled")
            low.config(state="normal" if enable else "disabled")
            high.config(state="normal" if enable else "disabled")
            color.config(state="normal" if enable else "disabled")
            freq.config(state="normal" if enable else "disabled")
        self.sample_rate_entry.config(state="normal" if enable else "disabled")
        
        
    def toggle_options_panel(self):
        if self.options_visible:
            self.options_frame.grid_remove()
            self.options_visible = False
            self.show_options_btn = tk.Button(self.top_frame, text="Show ThermalSense Options", command=self.toggle_options_panel, bg="#007bff", fg="white")
            self.show_options_btn.grid(row=0, column=3, padx=10)
        else:
            self.options_frame.grid()
            self.show_options_btn.destroy()
            self.options_visible = True
            
    def validate_inputs(self):
        # Skip all validation if Default Mode is selected
        if self.default_mode_var.get():
            return True
        valid = True
        self.custom_ranges = {}

        # Clear old validation labels
        for msg in self.validation_labels:
            msg.destroy()
        self.validation_labels.clear()

        for row, (label, name_e, low_e, high_e, color_e, freq_e, _) in enumerate(self.range_entries):
            row_offset = 4 + row
            errors = []
            valid_row = True

            # --- Name ---
            name = name_e.get().strip()
            if not name:
                errors.append("Name is required")
                valid_row = False

            # --- Low ---
            try:
                low = float(low_e.get())
            except:
                errors.append("Low must be a number")
                valid_row = False

            # --- High ---
            try:
                high = float(high_e.get())
                if 'low' in locals() and low >= high:
                    errors.append("High must be > Low")
                    valid_row = False
            except:
                errors.append("High must be a number")
                valid_row = False

            # --- Color ---
            try:
                self.options_frame.winfo_rgb(color_e.get().strip())
            except:
                errors.append("Invalid color name")
                valid_row = False

            # --- Frequency ---
            try:
                freq = int(freq_e.get())
                if freq < 0:
                    raise ValueError
            except:
                errors.append("Frequency must be int >= 0")
                valid_row = False

            # --- Display result ---
            if errors:
                msg_text = "X " + "; ".join(errors)
                msg_color = "red"
                valid = False
            else:
            
                #msg_text = "OK"
                #msg_color = "green"
                msg_text = "Valid Range"
                msg_color = "green"

                msg_label = tk.Label(
                    self.options_frame,
                    text=msg_text,
                    fg=msg_color,
                    bg="white",
                    font=("Arial", 7),
                    wraplength=180,
                    justify="left"
                )
               # msg_label.grid(row=row_offset, column=7, sticky="w", padx=5)
                self.validation_labels.append(msg_label)
                self.custom_ranges[name] = {
                    "low": low,
                    "high": high,
                    "color": color_e.get().strip(),
                    "freq": freq
                }

            msg_label = tk.Label(
                self.options_frame,
                text=msg_text,
                fg=msg_color,
                bg="white",
                font=("Arial", 7),
                wraplength=180,  # helpful if messages get too long
                justify="left"
            )
            msg_label.grid(row=row_offset, column=7, sticky="w", padx=5)
            self.validation_labels.append(msg_label)

        return valid


    def start_algorithm(self):

        mode = "default" if self.default_mode_var.get() else "custom"

        # Clean old validation labels always
        for msg in self.validation_labels:
            msg.destroy()
        self.validation_labels.clear()

        if mode == "custom":
            if not self.validate_inputs():
                return
            custom_ranges = self.custom_ranges
        else:
            # In Default Mode, ignore any previously validated custom ranges
            self.custom_ranges = {}
            custom_ranges = None

        self.stop_all(show_stop_background=False)
        print("Starting ThermalSense")


        sample_rate = int(self.sample_rate_entry.get())
        save_csv = self.csv_log_var.get()
        save_frame = self.frame_save_var.get()
        save_sound = self.sound_save_var.get()
        save_images = self.image_save_var.get()

        self.thermal_sense = ThermalSenseRunner(
            external_ax=self.ax,
            external_canvas=self.canvas,
            root=self.root,
            mode=mode,
            sample_rate=sample_rate,
            custom_ranges_dict=custom_ranges,
            save_csv=save_csv,
            save_frame=save_frame,
            save_sound=save_sound,
            save_images=save_images,
            display_enabled=self.visual_display_var.get() # Added Visual real-time control parameter ro tunner
        )

        self.thread = threading.Thread(target=self.thermal_sense.run)
        self.thread.start()

        # Hide options and disable button
        #self.options_frame.grid_remove()
        self.start_btn.config(state=tk.DISABLED)
        if self.options_visible:
            self.toggle_options_panel()


            
    def _add_range_row(self):
        if len(self.range_entries) >= self.max_rows:
            return

        idx = len(self.range_entries)
        row = 4 + idx

        # === Range label ===
        range_label = tk.Label(self.options_frame, text=f"Range {idx + 1}:", bg="white")
        range_label.grid(row=row, column=0, sticky="e")

        # === Entry fields ===
        name_e  = tk.Entry(self.options_frame, width=10)
        low_e   = tk.Entry(self.options_frame, width=5)
        high_e  = tk.Entry(self.options_frame, width=5)
        color_e = ttk.Combobox(self.options_frame, width=9,
                               values=["red", "lightcoral", "lime", "aqua", "green",
                                       "blue", "lightyellow", "yellow", "gold",
                                       "orange", "white", "gray", "cyan", "magenta"])
        freq_e  = tk.Entry(self.options_frame, width=6)

        widgets = (range_label, name_e, low_e, high_e, color_e, freq_e)

        for col, w in enumerate(widgets, start=0):  # start=0 to include the label
            w.grid(row=row, column=col, pady=1, padx=1, sticky="w")

        # === Delete button ===
        del_btn = tk.Button(self.options_frame, text="X",
                            command=lambda i=idx: self._del_row(i),
                            bg="#dc3545", fg="white", width=2)
        del_btn.grid(row=row, column=6)

        # === Store widgets ===
        self.range_entries.append((range_label, name_e, low_e, high_e, color_e, freq_e, del_btn))

        # Move the Add button one row down
        self.add_row_btn.grid(row=row + 1, column=0, columnspan=7, pady=(6, 2))

        self.toggle_custom_mode()
        self._reposition_static_controls()

    def _repack_rows(self):
        # refresh row indices and reposition widgets
        for i, widgets in enumerate(self.range_entries):
            row = 4 + i
            range_label, name_e, low_e, high_e, color_e, freq_e, del_btn = widgets

            range_label.config(text=f"Range {i + 1}:")
            range_label.grid_configure(row=row, column=0)
            name_e.grid_configure(row=row, column=1)
            low_e.grid_configure(row=row, column=2)
            high_e.grid_configure(row=row, column=3)
            color_e.grid_configure(row=row, column=4)
            freq_e.grid_configure(row=row, column=5)
            del_btn.config(command=lambda i=i: self._del_row(i))
            del_btn.grid_configure(row=row, column=6)
            

        # Move add button below last row
        self.add_row_btn.grid(row=4 + len(self.range_entries), column=0, columnspan=7, pady=(6, 2))
        self._reposition_static_controls()

    def _del_row(self, idx: int):
        widgets = self.range_entries[idx]
        for w in widgets:
            w.destroy()
        self.range_entries.pop(idx)
        self._repack_rows()
        
    def _reposition_static_controls(self):
        start_row = 4 + len(self.range_entries)
        self.add_row_btn.grid(row=start_row, column=0, columnspan=7, pady=(6,2))
        self.image_save_checkbox.grid(row=start_row + 1, column=0, columnspan=7, sticky="w", pady=(10, 0))
        self.csv_checkbox.grid(row=start_row + 2, column=0, columnspan=7, sticky="w")
        self.frame_checkbox.grid(row=start_row + 3, column=0, columnspan=7, sticky="w")
        self.sound_checkbox.grid(row=start_row + 4, column=0, columnspan=7, sticky="w")
        # Added visual real-time control
        self.visual_display_checkbox.grid(row=start_row + 5, column=0, columnspan=7, sticky="w", pady=(5, 0))
        
        self.validate_btn.grid(row=start_row + 6, column=0, columnspan=7, pady=10)
        self.toggle_btn.grid(row=start_row + 7, column=0, columnspan=7)



if __name__ == '__main__':
    root = tk.Tk()
    app = ThermalSenseGUI(root)
    root.mainloop()
