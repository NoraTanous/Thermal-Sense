# -*- coding: utf-8 -*-
"""
Dependencies/object_thermal_sound.py  â cleaned for pure UTFâ8 / ASCII
---------------------------------------------------------------------
This module contains the `ThermalSense` class used by the GUI frontâend
and the runner.  All curly quotes, long dashes, arrows, and other nonâ
ASCII glyphs have been replaced so the file can be imported without any
Unicodeâdecode errors on systems that expect strict UTFâ8 source files.
"""

import os
import cv2
import numpy as np
import soundfile as sf
import matplotlib.colors as mcolors


class ThermalSense:
    """Convert thermal frames to colour images and soundscapes."""

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    def __init__(
        self,
        sample_rate: int = 44_100,
        sweep_duration: float = 2.0,
        output_dir: str = ".",
        mode: str = "default",  # "default" or "custom"
        custom_ranges_dict: dict | None = None,
        save_images: bool = True,
    ) -> None:
        self.sample_rate = sample_rate
        self.sweep_duration = sweep_duration
        self.output_dir = output_dir
        self.mode = mode
        
        # Normalize custom ranges if provided
        """
        This converts the input format from

        "hot": {"low": 40, "high": 70, "color": "red", "freq": 650}
        
        To:


        "hot": [[40, 70], "red", 650]
        """
        self.custom_ranges = {}
        if custom_ranges_dict:
            for name, params in custom_ranges_dict.items():
                rng   = [params["low"], params["high"]]
                color = params["color"]
                freq  = params["freq"]
                self.custom_ranges[name] = [rng, color, freq]
        
        self.save_images = save_images
        self.frame_index = 0
        self._neutral_rgb = np.array([0,0,0], dtype=np.uint8)
        self._neutral_tone = 0

        # ---------------- default ranges ----------------
        # Each entry:  name : [[lo, hi],  colour_name,  tone_freq]
        self.default_ranges: dict[str, list] = {
            "Cold":     [[0, 20], "blue", 200],
            "Neutral":  [[21, 29], "black", 0],   # 0 Hz = silence
            "Hot":     [[30, 70], "red", 500],
        }

        # Create subâfolders only if we will actually write images/audio
        if self.save_images:
            for sub in ("cleaned", "thermal", "audio"):
                os.makedirs(os.path.join(self.output_dir, sub), exist_ok=True)

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    def get_active_ranges(self) -> dict:
        """Return the currently active rangeâdictionary."""
        if self.mode == "custom" and self.custom_ranges:
            return self.custom_ranges
        return self.default_ranges

    # Keep the previous missâspelt names alive so other files do not crash
    get_activate_ranges = get_active_ranges  # legacy alias
    _active_ranges = get_active_ranges       # internal alias

    @staticmethod
    def _color_to_rgb(col: str) -> np.ndarray:
        """Convert colour name / hex string to an RGB uint8 triplet."""
        try:
            return (np.array(mcolors.to_rgb(col)) * 255).astype(np.uint8)
        except ValueError:
            # Fallback to white if Matplotlib does not recognise the colour.
            return np.array([255, 255, 255], dtype=np.uint8)

    # ------------------------------------------------------------------
    # Imaging helpers
    # ------------------------------------------------------------------

    @staticmethod
    def image_acquisition(image) -> np.ndarray:
        """Accept a file path or ndarray and return a 50Ã30 grayscale image."""
        if isinstance(image, str):
            image = cv2.imread(image, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError("Invalid image source")
        return cv2.resize(image, (50, 30))

    @staticmethod
    def remove_non_thermal(img: np.ndarray) -> np.ndarray:
        """Remove reflections / nonâthermal artefacts with inâpainting."""
        if img.ndim == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        img = np.clip(img, 0, 255).astype(np.uint8)
        _, mask = cv2.threshold(img, 100, 255, cv2.THRESH_BINARY)
        mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), 1)
        return cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)

    def generate_colored_thermal_image(self, t_data: np.ndarray) -> np.ndarray:
        """Map temperature ranges to userâdefined colours."""
        h, w = t_data.shape
        out = np.full((h, w, 3), self._neutral_rgb, dtype=np.uint8)
        for _, (rng, colour, _) in self.get_active_ranges().items():
            lo, hi = rng
            out[(t_data >= lo) & (t_data <= hi)] = self._color_to_rgb(colour)
        return out

    # ------------------------------------------------------------------
    # Main processing entryâpoint
    # ------------------------------------------------------------------

    def process_image(self, raw: np.ndarray):
        """
        Returns ONLY: cleaned_frame, soundscape
        Counting is now done in the runner.
        """
        proc  = self.image_acquisition(raw)
        clean = self.remove_non_thermal(proc)
        flip  = cv2.flip(clean, 1)

        scape = self.create_soundscape(flip)

        if self.save_images:
            i = self.frame_index
            cv2.imwrite(f"{self.output_dir}/cleaned/frame_{i:03}.png", flip)
            rgb = self.generate_colored_thermal_image(flip)
            cv2.imwrite(f"{self.output_dir}/thermal/frame_{i:03}.png",
                        cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))

        self.frame_index += 1
        return flip, scape                    # <-- only two items


    # ------------------------------------------------------------------
    # Sound generation
    # ------------------------------------------------------------------

    def create_soundscape(self, thermal_image: np.ndarray) -> np.ndarray:
        """
        Keeps the old row-to-pitch melody but multiplies it by the
        user-chosen base_freq of the pixels range.
        -  neutral or freq==0  ? silent
        -  brass for hot/warm, reed for cold/freezing
        """
        h, w          = thermal_image.shape
        time_per_col  = self.sweep_duration / w
        total_samples = int(self.sample_rate * self.sweep_duration)
        soundscape    = np.zeros((total_samples, 2), dtype=np.float32)

        active = self.get_active_ranges()

        for x in range(w):
            s = int(x * time_per_col * self.sample_rate)
            e = s + int(time_per_col * self.sample_rate)
            if e > total_samples:
                continue

            col_wave = np.zeros((e - s,), dtype=np.float32)

            for y in range(h):
                t = thermal_image[y, x]
                row_pitch = self._pitch_from_y(y, h)   # old melodic mapping

                for name, (rng, _col, base) in active.items():
                    lo, hi = rng
                    if not (lo <= t <= hi):
                        continue

                    # -- silent / neutral
                    if base == 0 or "neutral" in name.lower():
                        break

                    eff = base * row_pitch / 440.0       # <-- scaled melody
                    if "hot" in name.lower() or "warm" in name.lower():
                        col_wave += self._generate_brass_tone(eff, time_per_col)
                    else:  # cold / freezing
                        col_wave += self._generate_reed_tone(eff, time_per_col)
                    break

            mv = np.max(np.abs(col_wave))
            if mv > 0:
                col_wave /= mv + 1e-6

            pan = x / (w - 1)
            stereo        = np.zeros((e - s, 2), dtype=np.float32)
            stereo[:, 0]  = col_wave * np.sqrt(1 - pan)   # left
            stereo[:, 1]  = col_wave * np.sqrt(pan)       # right
            soundscape[s:e] += stereo

        return soundscape

    # ------------------------------------------------------------------
    # I/O helpers
    # ------------------------------------------------------------------

    def save_audio(self, scape: np.ndarray, path: str) -> None:
        """Normalise stereo buffer and write as 32bit float WAV."""
        if scape.ndim == 1:
            scape = np.column_stack((scape, scape))
        if np.isnan(scape).any() or np.isinf(scape).any():
            raise ValueError("Soundscape contains invalid values")
        scape /= np.max(np.abs(scape)) + 1e-6
        sf.write(path, scape, self.sample_rate)

    # ------------------------------------------------------------------
    # Tone generators (private)
    # ------------------------------------------------------------------

    def _generate_reed_tone(self, freq: float, duration: float) -> np.ndarray:
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        vibrato = 0.02 * np.sin(2 * np.pi * 5 * t)
        return 0.4 * np.sin(2 * np.pi * freq * t + vibrato)

    def _generate_brass_tone(self, freq: float, duration: float) -> np.ndarray:
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        return 0.5 * (
            np.sin(2 * np.pi * freq * t) +
            0.3 * np.sin(4 * np.pi * freq * t) +
            0.2 * np.sin(6 * np.pi * freq * t)
        )

    # Legacy aliases (other files might still call these)
    _reed = _generate_reed_tone
    _brass = _generate_brass_tone

    # ------------------------------------------------------------------
    # Misc helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _pitch_from_y(y: int, height: int) -> float:
        """Map pixel row to frequency inside a pentatonic scale."""
        base_freq = 300
        freq_range = 700
        raw_freq = base_freq + ((height - y) / height) * freq_range
        return ThermalSense._quantize(raw_freq)

    @staticmethod
    def _quantize(freq: float) -> float:
        ratios = [1.0, 1.125, 1.25, 1.5, 1.875]
        base = 220  # A3
        scale = [base * r * (2 ** octv) for octv in range(4) for r in ratios]
        return min(scale, key=lambda f: abs(f - freq))

    @staticmethod
    def detect_hot_cold_regions(img: np.ndarray,
                                hot_thr: float = 30.0,
                                cold_thr: float = 20.0) -> tuple[int, int]:
        """
        Count columns that contain =1 pixel = hot_thr (hot)
                                  or =1 pixel = cold_thr (cold).
        """
        h, w = img.shape
        hot = cold = 0
        for x in range(w):
            col = img[:, x]
            if np.any(col >= hot_thr):
                hot += 1
            elif np.any(col <= cold_thr):
                cold += 1
        return hot, cold

