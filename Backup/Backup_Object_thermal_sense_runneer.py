import sys
import os
import time
import csv
import numpy as np
import matplotlib.pyplot as plt
import simpleaudio as sa
from datetime import datetime
from Dependencies.object_thermal_sound import ThermalSense
from ThermalSenseInput import ThermalSenseInput


class ThermalSenseRunner:
    def __init__(self, update_callback=None, external_ax=None, external_canvas=None, root=None):
        self.thermal_sensor = ThermalSenseInput()
        self.running = False

        self.update_callback = update_callback
        self.ax = external_ax
        self.canvas = external_canvas
        self.root = root

        self.start_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.result_path = os.path.join(self.base_path, "Results", "ThermalSense", f"ThermalSense-{self.start_time}")
        os.makedirs(self.result_path, exist_ok=True)
        print(f"[DEBUG] Results will be saved to: {self.result_path}")
        os.makedirs(os.path.join(self.result_path, "cleaned"), exist_ok=True)
        os.makedirs(os.path.join(self.result_path, "thermal"), exist_ok=True)


        # Create internal cleaned/thermal folders INSIDE result_path
        self.cleaned_dir = os.path.join(self.result_path, "cleaned")
        self.thermal_dir = os.path.join(self.result_path, "thermal")
        os.makedirs(self.cleaned_dir, exist_ok=True)
        os.makedirs(self.thermal_dir, exist_ok=True)

        self.processor = ThermalSense(output_dir=self.result_path)
        self.csv_file_path = os.path.join(self.result_path, f"ThermalSense-{self.start_time}.csv")
        self._init_csv()

    def _init_csv(self):
        self.csv_file = open(self.csv_file_path, mode='w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow([
            "frame_number",
            "mean_temperature",
            "heat_range",
            "image_filename",
            "wav_filename",
            "cleaned_image",
            "thermal_image",
            "detected_items_counter",
            "cold_items_counter",
            "hot_items_counter",
            "frame_result"
        ])

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
        while self.running:
            if self.ax and self.canvas:
                ax = self.ax
                fig = self.canvas.figure
                therm1 = ax.imshow(np.zeros((24, 32)), vmin=0, vmax=60, cmap='inferno', interpolation='bilinear')
                if not hasattr(self, 'colorbar'):
                    self.colorbar = fig.colorbar(therm1, ax=ax, fraction=0.046, pad=0.04)
                self.canvas.draw()
            else:
                fig, ax, therm1 = self.thermal_sensor.setup_plot()

            frame = np.zeros((24 * 32,))
            frame_number = 0
            t_array = []

            print("Starting ThermalSenseRunner real-time processing...(Press Ctrl+C to exit safely)")

            try:
                while self.running:
                    t1 = time.monotonic()
                    self.thermal_sensor.mlx.getFrame(frame)
                    data_array = np.reshape(frame, (24, 32))

                    if self.update_callback:
                        try:
                            self.update_callback(data_array)
                        except Exception as e:
                            print(f"[Live callback Error] {e}")

                    self.thermal_sensor.update_display(fig, ax, therm1, data_array)

                    if self.canvas and self.root:
                        self.root.after(0, self.canvas.draw)
                    else:
                        fig.tight_layout()
                        plt.pause(0.001)

                    t_array.append(time.monotonic() - t1)
                    print(f"Sample Rate: {len(t_array) / np.sum(t_array):.1f} fps")

                    mean_temperature = np.mean(data_array)
                    print(f"[Frame {frame_number}] Mean temperature: {mean_temperature:.2f} C")

                    cleaned, thermal_data, soundscape, detected_objects = self.processor.process_image(data_array)

                    wav_filename = f"frame_{frame_number:03d}.wav"
                    wav_path = os.path.join(self.result_path, wav_filename)
                    self.processor.save_audio(soundscape, wav_path)
                    self.play_audio(wav_path)

                    cold_items = [obj for obj in detected_objects if obj[0] == "cold"]
                    hot_items = [obj for obj in detected_objects if obj[0] == "hot"]
                    cold_str = '\n'.join([f"item{i+1}:({obj[1]}, {obj[2]})" for i, obj in enumerate(cold_items)])
                    hot_str = '\n'.join([f"item{i+1}:({obj[1]}, {obj[2]})" for i, obj in enumerate(hot_items)])

                    [txt.remove() for txt in ax.texts]
                    ax.text(0.01, -0.08, f"Cold items detected: {len(cold_items)}", color='blue', fontsize=10, transform=ax.transAxes)
                    ax.text(0.5, -0.08, f"Hot items detected: {len(hot_items)}", color='red', fontsize=10, transform=ax.transAxes)

                    fig.tight_layout()

                    frame_result = f"cold:\n{cold_str}\nhot:\n{hot_str}"

                    image_filename = f"frame_{frame_number:03d}.png"
                    image_path = os.path.join(self.result_path, image_filename)
                    fig.savefig(image_path)

                    cleaned_path = os.path.join(self.result_path, "cleaned", image_filename)
                    thermal_path = os.path.join(self.result_path, "thermal", image_filename)


                    if self.csv_writer and not self.csv_file.closed:
                        self.csv_writer.writerow([
                            frame_number,
                            mean_temperature,
                            self._get_heat_range(mean_temperature),
                            image_filename,
                            wav_filename,
                            cleaned_path,
                            thermal_path,
                            len(detected_objects),
                            len(cold_items),
                            len(hot_items),
                            frame_result
                        ])
                        self.csv_file.flush()

                    frame_number += 1
                    time.sleep(1)

            except KeyboardInterrupt:
                print("KeyboardInterrupt detected. Stopping safely...")
                self.stop()

        print("ThermalSense stopped.")

    def stop(self):
        self.running = False
        plt.close('all')
        if self.csv_file and not self.csv_file.closed:
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
