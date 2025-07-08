import sys
import os
import time
import csv
import numpy as np
import matplotlib.pyplot as plt
import simpleaudio as sa
from datetime import datetime
from Dependencies.ThermalSense import ThermalSense
from ThermalSenseInput import ThermalSenseInput
import json

class ThermalSenseRunner:
    def __init__(self, update_callback=None, external_ax=None, external_canvas=None, root=None,
                 mode="default", custom_ranges_dict=None, sample_rate=44100,
                 save_csv=True, save_frame=True, save_sound=True, save_images=True, display_enabled=True):
        self.mode = mode
        self.custom_ranges_dict = custom_ranges_dict
        self.sample_rate = sample_rate
        self.save_csv = save_csv
        self.save_frames = save_frame
        self.save_sound = save_sound
        self.save_images = save_images 
        self.display_enabled = display_enabled
        
        self.thermal_sensor = ThermalSenseInput()
        self.running = False

        self.update_callback = update_callback
        self.ax = external_ax
        self.canvas = external_canvas
        self.root = root
        self.colorbar = None
        self.therm_img = None

        self.start_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.result_path = os.path.join(self.base_path, "Results", "ThermalSense", f"ThermalSense-{self.start_time}")
        os.makedirs(self.result_path, exist_ok=True)
        print(f"[DEBUG] Results will be saved to: {self.result_path}")
        if self.save_images:
            os.makedirs(os.path.join(self.result_path, "cleaned"), exist_ok=True)
            os.makedirs(os.path.join(self.result_path, "thermal"), exist_ok=True)


        # Create internal cleaned/thermal folders INSIDE result_path
        self.cleaned_dir = os.path.join(self.result_path, "cleaned")
        self.thermal_dir = os.path.join(self.result_path, "thermal")
        os.makedirs(self.cleaned_dir, exist_ok=True)
        os.makedirs(self.thermal_dir, exist_ok=True)

        self.processor = ThermalSense(
            output_dir=self.result_path,
            mode=self.mode,
            custom_ranges_dict=self.custom_ranges_dict,
            sample_rate=self.sample_rate,
            save_images=self.save_images
        )
        
        self.csv_file_path = os.path.join(self.result_path, f"ThermalSense-{self.start_time}.csv")
        if self.save_csv:
            self._init_csv()
        else:
            self.csv_writer = None
            self.csv_file = None
            

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
            "hot_item_count",
            "cold_item_count",
            "total_item_count"
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
        if self.running:
            print("[WARN] Already running. Ignoring duplicate Run request.")
            return
        self.running = True
        while self.running:
            fig, ax = None, None

            if self.ax and self.canvas:
                ax = self.ax
                fig = self.canvas.figure

                # Remove previous image if it exists
                if self.therm_img:
                    self.therm_img.remove()
                    self.therm_img = None

                # Remove previous colorbar if it exists
                # Correctly remove ALL non-main axes (i.e., any old colorbars)
                for ax_i in fig.axes[:]:
                    if ax_i is not self.ax:
                        fig.delaxes(ax_i)

                # Now re-add the colorbar to the current thermal image
               # self.colorbar = fig.colorbar(self.therm_img, ax=self.ax, fraction=0.046, pad=0.04)


            # Only setup image and colorbar if display is enabled
            if self.display_enabled:
                self.therm_img = ax.imshow(np.zeros((24, 32)), vmin=0, vmax=60, cmap='inferno', interpolation='bilinear')
                self.colorbar = fig.colorbar(self.therm_img, ax=ax, fraction=0.046, pad=0.04)
                self.canvas.draw()
            else:
                # Create dummy therm_img for backend processing (not for GUI)
                self.therm_img = None
                self.colorbar = None


            
            fig.subplots_adjust(bottom=0.2) # Ensure buttom margin for text overlays
            
            frame = np.zeros((24 * 32,))
            frame_number = 0
            t_array = []

            print("Starting ThermalSenseRunner real-time processing...(Press Ctrl+C to exit safely)")

            try:
                # MatplotLib fix errors block
                hot_label = ax.text(0.01, -0.08, '', color='red', transform=ax.transAxes)
                cold_label = ax.text(0.3, -0.08, '', color='blue', transform=ax.transAxes)
                total_label = ax.text(0.6, -0.08, '', color='white', transform=ax.transAxes)

                while self.running:
                    t1 = time.monotonic()
                    self.thermal_sensor.mlx.getFrame(frame)
                    data_array = np.reshape(frame, (24, 32))

                    if self.update_callback:
                        try:
                            self.update_callback(data_array)
                        except Exception as e:
                            print(f"[Live callback Error] {e}")

                    if not self.running:
                        break
                        
                    # Adding visual real-time control    
                    if self.display_enabled and self.therm_img is not None:
                        self.thermal_sensor.update_display(fig, ax, self.therm_img, data_array)
                        if self.canvas and self.root:
                            self.root.after(0, lambda: [fig.tight_layout(), self.canvas.draw_idle()])

                        else:
                            fig.tight_layout()
                        

                    t_array.append(time.monotonic() - t1)
                    print(f"Sample Rate: {len(t_array) / np.sum(t_array):.1f} fps")

                    mean_temperature = np.mean(data_array)
                    print(f"[Frame {frame_number}] Mean temperature: {mean_temperature:.2f} C")

                    # ------------------------------------------------------------------
                    # 1) Get cleaned frame and soundscape
                    # ------------------------------------------------------------------
                    cleaned, soundscape = self.processor.process_image(data_array)

                    # ------------------------------------------------------------------
                    # 2)  On the very first frame discover thresholds from the
                    #     active dictionary (default or the users custom one)
                    # ------------------------------------------------------------------
                    if frame_number == 0:
                        # collect every numeric edge in the range-dict
                        rngs   = list(self.processor.get_active_ranges().values())
                        edges  = sorted({lo for (lo, _), *_ in rngs} |
                                        {hi for (_, hi), *_ in rngs})
                        # choose the second-highest edge for hot, second-lowest for cold
                        self.hot_thr  = edges[-2] if len(edges) >= 2 else 30.0
                        self.cold_thr = edges[1]  if len(edges) >= 2 else 20.0
                        print(f"[DEBUG] hot_thr={self.hot_thr}  cold_thr={self.cold_thr}")

                    # ------------------------------------------------------------------
                    # 3) Count columns that contain =hot_thr  or =cold_thr pixels
                    # ------------------------------------------------------------------
                    hot_count, cold_count = self.processor.detect_hot_cold_regions(
                                                cleaned,
                                                self.hot_thr,
                                                self.cold_thr)
                    total_items = hot_count + cold_count

                    
                    frame_result = {
                                        "frame_number": frame_number,
                                        "hot_items": hot_count,
                                        "cold_items": cold_count,
                                        "total_items": total_items
                    }
                    
                    # GUI overlay - prints the counter indicator on the real-time frame
                    hot_label.set_text(f"Hot: {hot_count}")
                    cold_label.set_text(f"Cold: {cold_count}")
                    total_label.set_text(f"Total: {total_items}")


                    wav_filename = f"frame_{frame_number:03d}.wav"
                    wav_path = os.path.join(self.result_path, wav_filename)
                    if self.save_sound:
                        self.processor.save_audio(soundscape, wav_path)
                        self.play_audio(wav_path)



                    image_filename = f"frame_{frame_number:03d}.png"
                    image_path = os.path.join(self.result_path, image_filename)
                    
                    if self.save_frames:
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
                            hot_count,
                            cold_count,
                            total_items
                        ])
                        self.csv_file.flush()

                    frame_number += 1
                    time.sleep(1)

            except KeyboardInterrupt:
                print("KeyboardInterrupt detected. Stopping safely...")
                self.stop()

        print("ThermalSense stopped.")

    def stop(self):
        if not self.running:
            return
        self.colorbar = None
        self.therm_img = None
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
