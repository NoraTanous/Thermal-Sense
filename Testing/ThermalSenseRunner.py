import sys
import os
import time
import csv
import numpy as np
import matplotlib.pyplot as plt
import simpleaudio as sa
from datetime import datetime
from Dependencies.thermal_sound import ThermalSense
from ThermalSenseInput import ThermalSenseInput

class ThermalSenseRunner:
    def __init__(self):
        self.thermal_sensor = ThermalSenseInput()
        self.processor = ThermalSense()
        self.running = False

        self.start_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.result_path = os.path.join(self.base_path, "Results", "ThermalSense", f"ThermalSense-{self.start_time}")
        os.makedirs(self.result_path, exist_ok=True)

        self.csv_file_path = os.path.join(self.result_path, f"ThermalSense-{self.start_time}.csv")
        self._init_csv()

    def _init_csv(self):
        self.csv_file = open(self.csv_file_path, mode='w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["frame_number", "mean_temperature", "heat_range", "image_filename", "wav_filename"])

    def _get_heat_range(self, temperature):
        if temperature < 10:
            return "very cold"
        elif temperature < 20:
            return "cold"
        elif temperature < 30:
            return "neutral"
        elif temperature < 40:
            return "warm"
        elif temperature < 70:
            return "hot"
        else:
            return "out of range"

    def run(self):
        self.running = True
        fig, ax, therm1 = self.thermal_sensor.setup_plot()
        frame = np.zeros((24 * 32,))
        frame_number = 0
        t_array = []

        print("Starting ThermalSenseRunner real-time processing...\n(Press Ctrl+C to exit safely)")

        try:
            while self.running:
                t1 = time.monotonic()
                self.thermal_sensor.mlx.getFrame(frame)
                data_array = np.reshape(frame, (24, 32))
                self.thermal_sensor.update_display(fig, ax, therm1, data_array)
                plt.pause(0.001)

                t_array.append(time.monotonic() - t1)
                print(f"Sample Rate: {len(t_array) / np.sum(t_array):.1f} fps")

                mean_temperature = np.mean(data_array)
                print(f"[Frame {frame_number}] Mean temperature: {mean_temperature:.2f} C")

                # Process frame using ThermalSense algorithm
                cleaned, thermal_data, soundscape = self.processor.process_image(data_array)

                # Save WAV
                wav_filename = f"frame_{frame_number:03d}.wav"
                wav_path = os.path.join(self.result_path, wav_filename)
                self.processor.save_audio(soundscape, wav_path)

                # Play the sound live
                self.play_audio(wav_path)

                # Save Image
                image_filename = f"frame_{frame_number:03d}.png"
                image_path = os.path.join(self.result_path, image_filename)
                fig.savefig(image_path)

                # Log to CSV
                heat_range = self._get_heat_range(mean_temperature)
                self.csv_writer.writerow([frame_number, mean_temperature, heat_range, image_filename, wav_filename])
                self.csv_file.flush()

                frame_number += 1
                time.sleep(1)  # 1 second between frames (you can adjust)

        except KeyboardInterrupt:
            print("\nKeyboardInterrupt detected. Stopping safely...")
            self.stop()

    def stop(self):
        self.running = False
        plt.close('all')
        if self.csv_file:
            self.csv_file.close()
        print("CSV saved at:", self.csv_file_path)

    def play_audio(self, wav_path):
        try:
            wave_obj = sa.WaveObject.from_wave_file(wav_path)
            play_obj = wave_obj.play()
            play_obj.wait_done()
        except Exception as e:
            print(f"Error playing audio: {e}")

if __name__ == "__main__":
    runner = ThermalSenseRunner()
    runner.run()
