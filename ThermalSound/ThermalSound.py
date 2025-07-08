import os
import csv
import time
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from ThermalSenseInput import ThermalSenseInput
from ThermalSoundOutput import ThermalSoundOutput

class ThermalSound:
    def __init__(self):
        self.thermal_sensor = ThermalSenseInput()
        self.voice = ThermalSoundOutput()
        self.running = False
        self.object_count = 0
        
        self.csv_writer = None
        self.csv_file = None
        self.start_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.base_path  = os.path.dirname(os.path.abspath(__file__))
        self.csv_path = os.path.join(self.base_path, "Results", "ThermalSound", "ThermalSound-{self.start_time}")
        
        os.makedirs(self.csv_path, exist_ok=True)
        self.csv_file_path = os.path.join(self.csv_path, f"ThermalSound-{self.start_time}.csv")

        self._init_csv()

    def _init_csv(self):
        self.csv_file = open(self.csv_file_path, mode='w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["object_count", "temperature", "heat_range", "detected_object"])

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
        t_array = []
        max_retries = 5

        print("Starting ThermalSound run...")

        while self.running:
            t1 = time.monotonic()
            retry_count = 0

            while retry_count < max_retries:
                try:
                    self.thermal_sensor.mlx.getFrame(frame)
                    data_array = np.reshape(frame, (24, 32))
                    self.thermal_sensor.update_display(fig, ax, therm1, data_array)
                    plt.pause(0.001)

                    t_array.append(time.monotonic() - t1)
                    print('Sample Rate: {0:2.1f}fps'.format(len(t_array) / np.sum(t_array)))

                    temperature_c = self.thermal_sensor.calculate_temperature()
                    print(f"Current temperature: {temperature_c} C")

                    self.voice.play_sound_by_temperature(temperature_c)
                    self.object_count += 1
                    heat_range = self._get_heat_range(temperature_c)
                    
                    #Save A snapshot of the current frame
                    image_filename = f"frame_{self.object_count:03d}.png"
                    image_path = os.path.join(self.csv_path, image_filename)
                    fig.savefig(image_path)

                    # Log everything to CSV
                    self.csv_writer.writerow([self.object_count, temperature_c, heat_range, image_filename])

                    time.sleep(2)
                    break

                except KeyboardInterrupt:
                    self.stop()
                    return
                except (ValueError, RuntimeError) as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        print(f"Failed after {max_retries} retries with error: {e}")
                        break

            time.sleep(0.1)

    def stop(self):
        print("Stopping ThermalSound...")
        self.running = False
        self.voice.quit()
        if self.csv_file:
            self.csv_file.close()
        print("CSV log saved to:", self.csv_file_path)
        
if __name__ == '__main__':
    
    ts = ThermalSound()
    ts.run()

