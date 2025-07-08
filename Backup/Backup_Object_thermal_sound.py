
import cv2
import numpy as np
import soundfile as sf

class ThermalSense:
    def __init__(self, sample_rate=44100, output_dir="."):
        self.sample_rate = sample_rate
        self.sweep_duration = 2.0  # 2 seconds
        self.max_temp = 70 
        self.hot_threshold = 35
        self.cold_threshold = 25
        self.frame_index = 0
        self.output_dir = output_dir


    def image_acquisition(self, image):
        if isinstance(image, str):
            image = cv2.imread(image, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError("Invalid image source")
        return cv2.resize(image, (50, 30))

    def remove_non_thermal(self, image):
        if image.ndim == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        image = np.clip(image, 0, 255).astype(np.uint8)
        _, mask = cv2.threshold(image, 100, 255, cv2.THRESH_BINARY)
        kernel = np.ones((3,3), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)
        return cv2.inpaint(image, mask, 3, cv2.INPAINT_TELEA)

    def to_unified_format(self, image):
        min_temp, max_temp = 0, self.max_temp
        image = np.clip(image, min_temp, max_temp).astype(np.float32)
        height, width = image.shape
        color_image = np.zeros((height, width, 3), dtype=np.float32)
        black_mask = (image == 0)
        cold_mask = (image <= 20) & ~black_mask
        if np.any(cold_mask):
            color_image[cold_mask, 0] = 255 * (1 - (image[cold_mask] / 20))
        hot_mask = (image >= 30)
        if np.any(hot_mask):
            color_image[hot_mask, 2] = 255 * ((image[hot_mask] - 30) / 40)
        return color_image

    def process_image(self, image):
        try:
            processed_image = self.image_acquisition(image)
            cleaned = self.remove_non_thermal(processed_image)
            thermal_data = self.to_unified_format(cleaned)
            detected_objects = self.detect_objects_by_columns(cleaned)
            soundscape = self.create_soundscape(detected_objects, thermal_data.shape[1])
            # _____________________________ Adding the option of saving cleaned and thermal data ______________________________________
            import os
            # ~ os.makedirs("cleaned", exist_ok=True)
            # ~ os.makedirs("thermal", exist_ok=True)
            

            # Create subdirectories if not exist
            os.makedirs(os.path.join(self.output_dir, "cleaned"), exist_ok=True)
            os.makedirs(os.path.join(self.output_dir, "thermal"), exist_ok=True)

            # Save images
            filename = f"frame_{self.frame_index:03}.png"
            cv2.imwrite(os.path.join(self.output_dir, "cleaned", filename), cleaned)

            thermal_uint8 = np.clip(thermal_data, 0, 255).astype(np.uint8)
            cv2.imwrite(os.path.join(self.output_dir, "thermal", filename), thermal_uint8)
            self.frame_index += 1
            #_____________________________________________________________________________________________________________________________

            return cleaned, thermal_data, soundscape, detected_objects
        except Exception as e:
            print(f"Error in process_image: {str(e)}")
            raise

    def detect_objects_by_columns(self, thermal_data):
        height, width = thermal_data.shape
        column_labels = [None] * width
        for x in range(width):
            hot_found = False
            cold_found = False
            for y in range(height):
                temp = thermal_data[y, x]
                if temp >= self.hot_threshold:
                    hot_found = True
                elif temp <= self.cold_threshold:
                    cold_found = True
                if hot_found and cold_found:
                    break

            if hot_found and not cold_found:
                column_labels[x] = 'hot'
            elif cold_found and not hot_found:
                column_labels[x] = 'cold'
            elif hot_found and cold_found:
                column_labels[x] = 'hot'  # prioritize hot if both exist

        objects = []
        i = 0
        while i < width:
            if column_labels[i] in ('hot', 'cold'):
                obj_type = column_labels[i]
                start_col = i
                while i < width and column_labels[i] == obj_type:
                    i += 1
                end_col = i - 1
                instrument = 'hot' if obj_type == 'hot' else 'cold'
                objects.append((instrument, start_col, end_col))
            else:
                i += 1
        return objects

    def create_soundscape(self, detected_objects, width):
        time_per_col = self.sweep_duration / width
        samples = int(self.sweep_duration * self.sample_rate)
        soundscape = np.zeros((samples, 2), dtype=np.float32)

        for instrument, start_col, end_col in detected_objects:
            duration = (end_col - start_col + 1) * time_per_col
            center_col = (start_col + end_col) / 2.0
            pan = center_col / width
            freq = self.map_object_to_freq(instrument)
            tone = self.generate_tone(freq, duration)

            left = tone[:,0] * np.sqrt(1 - pan)
            right = tone[:,1] * np.sqrt(pan)
            
            start_index = int(start_col * time_per_col * self.sample_rate)
            end_index = start_index + len(tone)
            if end_index > samples:
                end_index = samples
            soundscape[start_index:end_index, 0] += left[:end_index - start_index]
            soundscape[start_index:end_index, 1] += right[:end_index - start_index]
        return soundscape

    def save_audio(self, soundscape, output_path):
        if soundscape.ndim == 1:
            soundscape = np.column_stack((soundscape, soundscape))
        if np.isnan(soundscape).any() or np.isinf(soundscape).any():
            raise ValueError("Soundscape contains invalid values")
        max_val = np.max(np.abs(soundscape))
        if max_val > 0:
            soundscape = soundscape / (max_val + 1e-6)
        sf.write(output_path, soundscape, self.sample_rate)

    def map_object_to_freq(self, obj_type):
        if obj_type == 'hot':
            return 880  # Hot object frequency
        else:
            return 440  # Cold object frequency

    def generate_tone(self, freq, duration=0.5):
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        wave = 0.3 * np.sin(2 * np.pi * freq * t)
        stereo_wave = np.column_stack((wave, wave)).astype(np.float32)
        return stereo_wave
