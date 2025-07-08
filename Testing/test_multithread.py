import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import time
import os
from datetime import datetime
from ThermalSenseInput import ThermalSenseInput
from Dependencies.thermal_sound import ThermalSense  # Use your implementation

class ThermalSenseRunnerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ThermalSense Real-Time Display")

        # Init Thermal Components
        self.sensor = ThermalSenseInput()
        self.processor = ThermalSense()

        # Plot Figure
        self.fig, self.ax, self.therm1 = self.sensor.setup_plot()
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().grid(row=0, column=0, columnspan=3)

        # Control Buttons
        self.start_button = ttk.Button(root, text="Start", command=self.start)
        self.start_button.grid(row=1, column=0, padx=10, pady=10)

        self.stop_button = ttk.Button(root, text="Stop", command=self.stop)
        self.stop_button.grid(row=1, column=1, padx=10, pady=10)

        self.quit_button = ttk.Button(root, text="Quit", command=root.quit)
        self.quit_button.grid(row=1, column=2, padx=10, pady=10)

        # Status Label
        self.status_label = tk.Label(root, text="Frame: 0", font=("Arial", 12))
        self.status_label.grid(row=2, column=0, columnspan=3)

        # Frame Counters
        self.frame_number = 0
        self.running = False

        # Output Paths
        self.start_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.output_dir = os.path.join("Results", "ThermalSense", f"ThermalSense-{self.start_time}")
        os.makedirs(self.output_dir, exist_ok=True)

    def start(self):
        if not self.running:
            self.running = True
            self.update_loop()

    def stop(self):
        self.running = False

    def update_loop(self):
        if not self.running:
            return

        # Grab Frame
        frame = np.zeros((24 * 32,))
        self.sensor.mlx.getFrame(frame)
        data_array = np.reshape(frame, (24, 32))

        # Display
        self.sensor.update_display(self.fig, self.ax, self.therm1, data_array)
        self.canvas.draw()

        # Temp Info
        mean_temp = np.mean(data_array)
        self.status_label.config(text=f"Frame: {self.frame_number}  |  Mean Temp: {mean_temp:.2f}C")

        # Process with ThermalSense
        cleaned, colored, sound = self.processor.process_image(data_array)

        # Save outputs
        wav_path = os.path.join(self.output_dir, f"frame_{self.frame_number:03d}.wav")
        self.processor.save_audio(sound, wav_path)

        img_path = os.path.join(self.output_dir, f"frame_{self.frame_number:03d}.png")
        self.fig.savefig(img_path)

        self.frame_number += 1
        self.root.after(2500, self.update_loop)  # Schedule next update

if __name__ == "__main__":
    root = tk.Tk()
    app = ThermalSenseRunnerGUI(root)
    root.mainloop()
