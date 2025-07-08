import cv2
import numpy as np
from scipy.signal import butter, lfilter
import soundfile as sf

class ThermalSense:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.sweep_duration = 2.0  # 2 seconds
        self.very_cold_range = (0, 20)
        self.neutral_range = (21, 29)
        self.hot_range = (30, 70)
        self.max_temp = 70 

        base_freq = 110  # A2 as base
        self.pentatonic_freqs = []
        intervals = [0, 3, 5, 7, 10]
        for octave in range(6):
            for interval in intervals:
                self.pentatonic_freqs.append(base_freq * (2 ** (octave + interval / 12)))

    def image_acquisition(self, image):
     # 1. If image is a path string, read it as grayscale
     if isinstance(image, str):
        image = cv2.imread(image, cv2.IMREAD_GRAYSCALE)

     # 2. Validate the loaded image
     if image is None:
        raise ValueError("Invalid image source")

      # 3. Resize to a fixed resolution (50 x 30)
     return cv2.resize(image, (50, 30))


    def remove_non_thermal(self, image):
     # Convert to grayscale if needed
     if image.ndim == 3:
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
     image = np.clip(image, 0, 255).astype(np.uint8)

     # Lower threshold to catch mid-level gray
     _, mask = cv2.threshold(image, 100, 255, cv2.THRESH_BINARY)

     # (Optional) Dilation to expand the mask so partial edges are caught
     kernel = np.ones((3,3), np.uint8)
     mask = cv2.dilate(mask, kernel, iterations=1)

     # Inpaint
     cleaned = cv2.inpaint(image, mask, 3, cv2.INPAINT_TELEA)
     return cleaned





    def to_unified_format(self, image):
     min_temp, max_temp = 0, 70
     # Clip grayscale to [0..70], cast to float
     image = np.clip(image, min_temp, max_temp).astype(np.float32)
     height, width = image.shape

     # Prepare an output color image (H x W x 3) in BGR order
     color_image = np.zeros((height, width, 3), dtype=np.float32)

     # "Black" (zero values remain black)
     black_mask = (image == 0)

     # Normalized range 0..1 in [0..70]
     normalized = (image - min_temp) / (max_temp - min_temp + 1e-6)

     # Cold range: 1..20 => map to some shade of blue (B channel = index 0)
     cold_mask = (image <= 20) & ~black_mask
     if np.any(cold_mask):
        color_image[cold_mask, 0] = 255 * (1 - (image[cold_mask] / 20))

     # Hot range: 30..70 => map to some shade of red (R channel = index 2)
     hot_mask = (image >= 30)
     if np.any(hot_mask):
        color_image[hot_mask, 2] = 255 * ((image[hot_mask] - 30) / 40)

     # 21..29 => neutral/no color (remains black)

     return color_image







   
   

    def generate_reed_tone(self, frequency, duration, intensity):
        samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, samples)
        
        # Adjusted vibrato and dynamic breath modulation for realism
        vibrato_rate = 5.0
        vibrato_depth = 6
        vibrato = vibrato_depth * np.sin(2 * np.pi * vibrato_rate * t)
        
        # Add dynamic breath modulation
        breath_modulation = 0.02 * np.sin(2 * np.pi * 1.5 * t)  # Slow oscillation
        
        wave = (
            1.0 * np.sin(2 * np.pi * (frequency + vibrato + breath_modulation) * t) +
            0.5 * np.sin(2 * np.pi * (frequency * 3 + vibrato) * t) +
            0.3 * np.sin(2 * np.pi * (frequency * 5 + vibrato) * t)
        )
        
        # Faster but still smooth attack
        attack_time = int(0.02 * samples)
        envelope = np.ones(samples)
        envelope[:attack_time] = np.linspace(0, 1, attack_time) ** 3  # Softer exponential rise
        wave *= envelope
        
        # More natural breath noise with dynamic changes
        breath = np.random.normal(0, 0.015, samples) * np.exp(-t * 4)
        breath *= (1 + 0.3 * np.sin(2 * np.pi * 0.5 * t))  # Modulated breathiness
        wave += breath
        
        # Adjusted harmonic balance
        wave = self.notch_filter(wave, 800, 0.6)  # Reduce nasal resonance
        wave = self.boost_frequency(wave, 3500, 1.3)  # Add warmth and presence
        wave = self.boost_frequency(wave, 5000, 1.2)  # Enhance breathiness
        wave = self.highpass_filter(wave, 200)  # Ensure clarity in low-end
        
        return wave * intensity * 0.85

    def generate_brass_tone(self, frequency, duration, intensity):
        samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, samples)
        
        # Slightly reduced nonlinearity for smoother brass timbre
        wave = (
            1.0 * np.sin(2 * np.pi * frequency * t) +
            0.6 * np.sin(2 * np.pi * (frequency * 2) * t) +
            0.4 * np.sin(2 * np.pi * (frequency * 3) * t) +
            0.3 * np.sin(2 * np.pi * (frequency * 4) * t)
        )
        
        # Reduce harshness in attack
        attack_time = int(0.01 * samples)  # Softer but controlled attack
        envelope = np.ones(samples)
        envelope[:attack_time] = np.linspace(0, 1, attack_time) ** 4  # Gradual rise
        wave *= envelope
        
        # Introduce subtle airflow fluctuations for brass realism
        air_variation = 0.02 * np.sin(2 * np.pi * 1.2 * t)
        wave += air_variation
        
        # Balanced nonlinearity for brass growl
        wave = np.tanh(1.7 * wave)
        
        # Adjusted harmonic balance
        wave = self.notch_filter(wave, 700, 0.6)  # Reduce muddiness
        wave = self.boost_frequency(wave, 3000, 1.4)  # Boost brass presence
        wave = self.boost_frequency(wave, 4500, 1.3)  # Enhance high-end clarity
        wave = self.high_shelf_filter(wave, 3500, -1.2)  # Remove excessive brightness
        wave = self.highpass_filter(wave, 400)  # Clean up low-end
        
        return wave * intensity * 0.9





    def boost_frequency(self, data, freq, gain):
        nyq = 0.5 * self.sample_rate
        low = (freq - 20) / nyq
        high = (freq + 20) / nyq
        b, a = butter(2, [low, high], btype='band')
        boosted = lfilter(b, a, data)
        return data + (boosted * (gain - 1) * 0.3)
    
    def high_shelf_filter(self, data, cutoff, gain_db):
        nyq = 0.5 * self.sample_rate
        normal_cutoff = cutoff / nyq
        b, a = butter(2, normal_cutoff, btype='high')
        filtered = lfilter(b, a, data)
        gain = 10 ** (gain_db / 20.0)
        return data * (1 - gain) + filtered * gain

    def notch_filter(self, data, freq, Q=30):
        nyq = 0.5 * self.sample_rate
        if freq <= 0 or freq >= nyq:
            return data  # Skip filtering if frequency is out of range
        
        normalized_freq = freq / nyq
        b, a = butter(2, [max(0.01, normalized_freq - 0.01), min(0.99, normalized_freq + 0.01)], btype='bandstop')
        return lfilter(b, a, data)



    def process_objects_separately(self, thermal_data):
     """Detect and process multiple hot and cold objects in exact left-to-right order."""
     height, width, _ = thermal_data.shape
     detected_objects = []

     for x in range(width):  # Left-to-right processing
        for y in range(height):
            pixel = thermal_data[y, x]
            red, _, blue = pixel

            if red > 100 and blue < 30:  # Hot Object (Brass)
              detected_objects.append(('brass', x))
            elif blue > 100 and red < 30:  # Cold Object (Reed)
              detected_objects.append(('reed', x))


     # Ensure objects are in the exact order they appeared in the image
     return detected_objects  # Keeps exact sequence without deduplication
    
    
    def create_soundscape(self, thermal_data):
     # thermal_data is in BGR
     height, width, _ = thermal_data.shape
     duration = self.sweep_duration
     samples = int(duration * self.sample_rate)
     soundscape = np.zeros((samples, 2))
     time_per_col = duration / width

     # Detected objects
     detected_objects = []

     # Scan the image left to right
     for x in range(width):
        for y in range(height):
            b, g, r = thermal_data[y, x]  # BGR
            if r > 100 and b < 30:  
                # hot object => brass 
                detected_objects.append(("brass", x))
            elif b > 100 and r < 30:  
                # cold object => reed
                detected_objects.append(("reed", x))

     # Sort objects by x position
     detected_objects.sort(key=lambda obj: obj[1])

     # Generate tones
     for obj, x_pos in detected_objects:
        col_start = int(x_pos * time_per_col * self.sample_rate)
        col_start = max(0, col_start)

        column = thermal_data[:, x_pos, :]  # BGR for this column

        for y in range(height):
            b, g, r = column[y]  # BGR
            if obj == "brass" and r > 100 and b < 30:
                mapped_y = y
                # pick frequency from pentatonic
                frequency = self.pentatonic_freqs[
                    int((height - mapped_y - 1) / height * len(self.pentatonic_freqs))
                ] * 5
                intensity = min(r / 255, 1.0)
                tone = self.generate_brass_tone(frequency, time_per_col, intensity)

            elif obj == "reed" and b > 100 and r < 30:
                mapped_y = y
                frequency = self.pentatonic_freqs[
                    int((height - mapped_y - 1) / height * len(self.pentatonic_freqs))
                ]
                intensity = min(b / 255, 0.7)
                tone = self.generate_reed_tone(frequency, time_per_col, intensity)

            else:
                continue

            # panning
            pan = x_pos / width
            left = tone * np.sqrt(1 - pan)
            right = tone * np.sqrt(pan)

            end_idx = min(col_start + len(tone), samples)
            soundscape[col_start:end_idx, 0] += left[:end_idx - col_start]
            soundscape[col_start:end_idx, 1] += right[:end_idx - col_start]

     # Normalize
     max_val = np.max(np.abs(soundscape))
     if max_val > 0:
        soundscape = soundscape / max_val * 0.6

     return soundscape






    def boost_frequency(self, data, freq, gain):
     """Minimal frequency boost."""
     nyq = 0.5 * self.sample_rate
     low = (freq - 20) / nyq
     high = (freq + 20) / nyq
     b, a = butter(2, [low, high], btype='band')
     boosted = lfilter(b, a, data)
     return data + (boosted * (gain - 1) * 0.3)
    
    
    






 
   




   
 

   
 


    

    def lowpass_filter(self, data, cutoff):
        """Apply lowpass filter"""
        nyq = 0.5 * self.sample_rate
        normal_cutoff = cutoff / nyq
        b, a = butter(4, normal_cutoff, btype='low')
        return lfilter(b, a, data)
        
    def highpass_filter(self, data, cutoff):
        """Apply highpass filter"""
        nyq = 0.5 * self.sample_rate
        normal_cutoff = cutoff / nyq
        b, a = butter(4, normal_cutoff, btype='high')
        return lfilter(b, a, data)
        
    def boost_frequency(self, data, freq, gain):
        """Boost specific frequency range"""
        nyq = 0.5 * self.sample_rate
        low = (freq - freq/4) / nyq
        high = (freq + freq/4) / nyq
        b, a = butter(2, [low, high], btype='band')
        boosted = lfilter(b, a, data)
        return data + (boosted * (gain - 1))
        
    def compress_signal(self, data, threshold, ratio):
        """Apply compression to the signal"""
        data_abs = np.abs(data)
        mask = data_abs > threshold
        compressed = np.copy(data)
        compressed[mask] = threshold + (data_abs[mask] - threshold) / ratio
        compressed *= np.sign(data)
        return compressed
    
    


    def process_image(self, image):
     try:
        # Stage 1: Acquire and resize
        processed_image = self.image_acquisition(image)

        # Stage 2: Remove non-thermal artifacts
        cleaned = self.remove_non_thermal(processed_image)

        # Stage 3: Convert to color-coded thermal
        thermal_data = self.to_unified_format(cleaned)

        # Stage 4: Generate soundscape
        soundscape = self.create_soundscape(thermal_data)

        # Return all intermediate results if you want them
        return cleaned, thermal_data, soundscape

     except Exception as e:
        print(f"Error in process_image: {str(e)}")
        raise


    def save_audio(self, soundscape, output_path):
        """Save the generated soundscape to a WAV file"""
        try:
            # Type checking
            if not isinstance(soundscape, np.ndarray):
                raise TypeError(f"Expected numpy array for soundscape, got {type(soundscape)}")
            
            if not isinstance(output_path, str):
                raise TypeError(f"Expected string for output_path, got {type(output_path)}")
            
            # Shape checking
            if soundscape.ndim == 1:
                print("Converting mono to stereo...")
                soundscape = np.column_stack((soundscape, soundscape))
            elif soundscape.ndim > 2:
                raise ValueError(f"Soundscape must be 1D or 2D array, got {soundscape.ndim}D")
            
            # Data validation
            if np.isnan(soundscape).any():
                raise ValueError("Soundscape contains NaN values")
            
            if np.isinf(soundscape).any():
                raise ValueError("Soundscape contains infinite values")
            
            # Normalize audio
            max_val = np.max(np.abs(soundscape))
            if max_val > 0:
                soundscape = soundscape / (max_val + 1e-6)
            
            # Ensure float32 format
            soundscape = soundscape.astype(np.float32)
            
            print(f"Saving audio:")
            print(f"  Shape: {soundscape.shape}")
            print(f"  dtype: {soundscape.dtype}")
            print(f"  Range: [{np.min(soundscape)}, {np.max(soundscape)}]")
            print(f"  Output: {output_path}")
            
            # Write the file
            sf.write(output_path, soundscape, self.sample_rate)
            
            return True
            
        except Exception as e:
            print(f"Error in save_audio: {str(e)}")