ThermalSense Core – Real-Time Thermal-to-Audio Perception System



ThermalSense Core is an open-source Python project designed to translate thermal camera data into sound. By doing this, it enables users to "hear" temperature differences in their surroundings, offering a new way to sense the world—through sound.



The idea behind ThermalSense is to provide real-time auditory feedback that reflects thermal information captured by infrared cameras. For example, hotter regions produce higher-pitched sounds, and cooler ones are represented with lower tones. This sensory substitution system can be especially helpful in assistive technologies for visually impaired users, in education for teaching about thermal imaging and perception, or in research and experimentation with human-computer interaction systems.



The system works by continuously capturing data from a thermal sensor (like the MLX90640), processing it, and mapping temperature values to audio cues. The sound updates in real-time, offering immediate spatial and thermal feedback. Depending on the configuration, users can hear different tone schemes, adjust the temperature range for detection, save audio logs, and even snapshot thermal images as CSV or PNG files. The sound can also pan left to right to help locate the source of heat across a scene.



ThermalSense is built with modularity in mind. It separates sensor input, processing logic, and audio output into distinct components, making it easy to add support for new sensors or experiment with different auditory mappings.

## Table of Contents

- [Introduction](#introduction)
- [System Architecture & OOP Model](#system-architecture--oop-model)
  - [Class Structure](#class-structure)
  - [Data Flow](#data-flow)
- [Algorithm Overview](#algorithm-overview)
  - [Data Acquisition and Preprocessing](#data-acquisition-and-preprocessing)
  - [Thermal-to-Auditory Mapping Algorithm](#thermal-to-auditory-mapping-algorithm)
  - [Step-by-Step Operation](#step-by-step-operation)
- [Signal Generation](#signal-generation)
  - [Frequency-to-Tone Mapping](#frequency-to-tone-mapping)
  - [Audio Output Implementation](#audio-output-implementation)
- [Class-by-Class Code Walkthrough](#class-by-class-code-walkthrough)
- [Flow of Execution](#flow-of-execution)
- [ThermalSense GUI: Features & Modes](#thermalsense-gui-features--modes)
- [Installation Guide](#installation-guide)
- [Running the System](#running-the-system)
- [Key Features](#key-features)
- [Use Cases](#use-cases)
- [Project Structure](#project-structure)

---

## Introduction

**ThermalSense Core** enables human perception of invisible heat patterns by translating thermal images into rich auditory cues.  
Inspired by landmark systems like *The vOICe* and *EyeMusic*, which encode visual features as sound, **ThermalSense** targets the infrared domain: it captures input from a thermal sensor and generates a structured soundscape representing the temperature distribution in a scene.

Initial studies showed that users can accurately identify and localize thermal features after only a short training period—highlighting the system’s practical impact for sensory substitution.

---

## System Architecture & OOP Model

ThermalSense Core is implemented with four main classes:

ThermalSenseGUI: Main GUI. Collects user parameters and launches/stops processing.

ThermalSenseRunner: Orchestrator that manages data acquisition, processing, audio output, and logging.

ThermalSenseInput: Interface to the MLX90640 thermal camera; provides raw data frames and live visualization support.

ThermalSense: Core logic for thermal data cleaning, color mapping, soundscape synthesis, and saving results.

All major functionalities are encapsulated in these classes.

### Class Structure

-ThermalSenseGUI

Responsible for GUI building, collecting user input (mode, custom ranges), and running/stopping the pipeline.

Launches a background thread running a ThermalSenseRunner.

-ThermalSenseRunner

Coordinates real-time cycles.

Owns a ThermalSenseInput (hardware interface) and a ThermalSense (core processing and mapping).

Handles image acquisition, passes frames to ThermalSense.process_image, manages sound playback and file logging.

-ThermalSenseInput

Handles I2C connection and real-time reading from the MLX90640 sensor via .mlx.getFrame.

Provides helper methods for live plot updates.

-ThermalSense

Provides all thermal image processing (resizing, cleaning, colorization), temperature-to-color mapping, and the core soundscape generation.

Contains all logic for default and custom mapping modes.

---
Inter-class relationships:

ThermalSenseGUI instantiates and controls a ThermalSenseRunner

ThermalSenseRunner owns a ThermalSenseInput (sensor) and a ThermalSense (processing/mapping)

ThermalSenseInput is responsible only for sensor I/O

ThermalSense is responsible for all data, sound, and image transformations

##  Data Flow 

**A single real-time frame processing cycle involves:**

1. **ThermalSenseInput – Frame Acquisition**

   * The method ThermalSenseInput.__init__() establishes the I2C connection with the MLX90640 thermal camera (self.i2c = busio.I2C(board.SCL, board.SDA)), initializes the sensor object (self.mlx), and pre-allocates a 1D float32 array self.frame to hold the incoming data.
   * Each time a new frame is needed, self.mlx.getFrame(self.frame) is called, filling self.frame (length 768) with absolute temperature values (Celsius, by default) for each pixel.

2. **ThermalSenseRunner – Frame Handling**

   * ThermalSenseRunner.run() operates in a loop, pulling each new frame from the sensor by calling self.thermal_sensor.mlx.getFrame(frame), then reshaping it to a 2D numpy array (24 rows × 32 columns) for spatial processing.

3. **ThermalSense – Processing and Mapping**

   * The new frame (2D numpy array) is passed to ThermalSense.process_image(raw):

     * Calls ThermalSense.image_acquisition to resize and/or validate the incoming image (guaranteeing a consistent format for downstream processing).
     * Calls ThermalSense.remove_non_thermal to mask out and inpaint non-thermal artifacts, such as sensor reflections or environmental noise.
     * Flips image as needed (to match user spatial expectations).
     * Calls ThermalSense.create_soundscape, which generates a stereo waveform buffer representing the temperature distribution as audio.
   * Also, generates colored overlays (generate_colored_thermal_image) if enabled.

4. **ThermalSenseRunner – Output and Feedback**

   * Receives the cleaned image and soundscape array.
   * Saves files (PNG images, WAV audio) to the appropriate result directories if enabled.
   * Logs statistics (mean temp, hot/cold column counts, etc.) to CSV.
   * Triggers real-time playback (play_audio(wav_path)) and updates GUI overlays to indicate hot/cold/total counts per frame.
   * The entire process loops at a rate set by the GUI/sample rate, providing near real-time feedback.

5. **ThermalSenseGUI – User Control**

   * User can change parameters, choose  modes, and start/stop/exit the program .
   * Upon stopping, threads are joined and resources (open files, sensors) are safely closed.

---

##  Algorithm Overview 

###  Data Acquisition and Preprocessing

* **Sensor Setup** (ThermalSenseInput.__init__):

  * Direct hardware communication with MLX90640 sensor.
  * Sets sensor refresh rate for a stable data flow (typically 2 Hz, but adjustable).
  * Frame array pre-allocated and updated for each cycle.

* **Raw Data Extraction**:

  * self.mlx.getFrame(self.frame) retrieves the latest sensor readings. Output is a 1D numpy array (float32, length 768).
  * Data is reshaped to (24, 32) for 2D processing.

* **Preprocessing** (ThermalSense.process_image):

  * image_acquisition: Ensures correct size (50x30 default for image operations, though source is 24x32; resizing handled by OpenCV).
  * remove_non_thermal: Uses inpainting via OpenCV to eliminate outliers/reflections—masking with threshold and dilating, followed by inpaint to fill invalid regions smoothly.
  * Final cleaning may involve flipping or orientation corrections to match expected left/right/up/down spatial perception.

###  Thermal-to-Auditory Mapping Algorithm

* **Color Mapping** (generate_colored_thermal_image):

  * Maps pixels in temperature ranges (hot/cold/neutral or user-defined) to corresponding RGB color values.
  * Uses _color_to_rgb to convert color names (e.g., “red”, “blue”) to uint8 RGB triplets for OpenCV.

* **Soundscape Creation** (create_soundscape):

  * For each column x in the image (left to right):

    * Calculates its slice in the audio output buffer (based on column index and total sweep time).
    * For each row y:

      * Reads the pixel temperature value.
      * Identifies the matching active temperature range (e.g., is it “hot”, “cold”, or “neutral”?).
      * Uses _pitch_from_y(y, h) to map vertical pixel position to pitch (frequency), **quantized** by _quantize to a pentatonic scale.
      * Determines timbre based on range: “hot”/“warm” = **brass**, “cold” = **reed**. These use custom synthesized waveforms:

        * _generate_brass_tone: Complex waveform (fundamental plus harmonics).
        * _generate_reed_tone: Pure tone with vibrato for a distinct color.
      * Each time step (column) may sum multiple tones (for multiple hot/cold regions) into the left/right audio channels, using stereo panning.
    * **Stereo Panning**: The further left the column, the louder in the left channel, and vice versa, using a square-root law for perceptual evenness.

* **Counting** (detect_hot_cold_regions):

  * Scans each column to check if at least one pixel exceeds the hot or cold thresholds (customizable).
  * Counts how many columns contain hot/cold pixels—used for display overlays and logging.

###  Step-by-Step Operation 

1. **Initialization**:

   * User launches via GUI, sets up parameters (mode, ranges, logging, display).
   * ThermalSenseRunner and sensor interface initialized.

2. **Main Run Loop**:

   * For each frame:

     * Get raw frame from ThermalSenseInput.
     * Clean/process with ThermalSense.process_image.
     * Generate colored overlay and soundscape.
     * Save results and log data if enabled.
     * Play the soundscape immediately.
     * Update GUI overlays with frame counts and stats.
     * Delay based on sample rate (ensures smooth real-time performance).

3. **User Control**:

   * At any time, user can pause/stop/modify settings via the GUI, triggering safe termination or reinitialization of threads/resources.

---

##  Signal Generation 

###  Frequency-to-Tone Mapping

* **Pitch Calculation** (_pitch_from_y):

  * Vertical position is mapped to a continuous frequency range, e.g., 300 Hz (bottom) to 1000 Hz (top), then **quantized**.
  * _quantize matches the frequency to the closest value in a precomputed pentatonic scale table (ratios over several octaves from base A3).
  * This guarantees that all simultaneous tones are musically consonant, avoiding dissonance even with multiple active regions.

* **Scale Table**:

  * Predefined using ratios: [1.0, 1.125, 1.25, 1.5, 1.875] across four octaves above base 220 Hz (A3).

### Audio Output Implementation

* **Waveform Synthesis**:

  * _generate_brass_tone (for hot/warm): Sums sine waves at fundamental and multiples (harmonics) for a rich, “brassy” timbre.
  * _generate_reed_tone (for cold): Pure sine with vibrato for clarity and distinction.
  * Waveforms are generated as numpy arrays (per note), summed per column.

* **Mixing and Normalization**:

  * Each time slot’s stereo buffer is populated and summed for all relevant notes (could be multiple hot/cold spots in a column).
  * Total buffer is normalized to avoid clipping; pan is handled by distributing amplitude according to column position.

* **Saving and Playback**:

  * save_audio writes stereo buffer as 32-bit float WAV using soundfile.
  * play_audio loads the WAV (via simpleaudio), triggers real-time playback, and blocks until playback is finished (ensuring correct sync).

* **Real-time Feedback**:

  * Playback is started immediately after soundscape generation per frame, so user perceives “live” audio that tracks the sensor in real time.


---

## Class-by-Class Code Walkthrough

### `ThermalSenseGUI/MAIN`
- **Tkinter-based GUI** for user interaction.
- **Key Methods:**  
  - `__init__()`: Setup, widget placement, runner instantiation.
  - `build_gui()`, `build_options_panel()`: Widget layout for modes/range selection.
  - `on_mode_change()`: Switches between Default/Custom.
  - `start_algorithm()`, `stop_all()`: Launch and halt the system.
- **Features:**  
  - Mode selection, real-time plot, mapping controls, status/error feedback, results folder access.

### `ThermalSenseRunner` (orchestrator)
- **Runs the acquisition → processing → sonification → output loop**.
- **Key Methods:**  
  - `__init__()`: Sets up references, configures output.
  - `run()`: Main continuous processing loop.
  - `stop()`: Graceful shutdown, resource cleanup.
  - `play_audio()`, `log_results()`: Audio playback and data logging.

### `ThermalSenseInput` (`ThermalSensor`)
- **Hardware interface for the thermal sensor** (MLX90640).
- **Key Methods:**  
  - `__init__()`: Open sensor.
  - `calculate_temperature()`: Capture frame, filter as needed.
  - `update_display()`: Visualize current frame.
  - `close()`: Release hardware.


---

## Flow of Execution

1. **Launch:**  
   `main.py` creates the GUI and backend.
2. **User Sets Parameters:**  
   Via GUI: mode, mapping, scan speed, etc.
3. **Start:**  
   Begins processing loop in a background thread.
4. **Continuous Loop:**  
   Capture, preprocess, map, synthesize, output, and visualize/log each frame.
5. **User Can Pause/Adjust:**  
   Real-time interaction; immediate feedback.
6. **Stop:**  
   Releases resources and resets.

---

## ThermalSense GUI: Features & Modes

- **Default Mode**  
  - Automatically computes `hot_thr = μ + σ` and `cold_thr = μ – σ` on the very first frame.  
  - Uses those fixed thresholds for all subsequent frames.  
  - The custom-range panel is hidden and cannot be edited.

- **Custom Mode**  
  - Reveals a panel allowing you to define up to **7** named temperature ranges.  
  - For each range you specify:  
    - **Name** (e.g. “Hot Spot”)  
    - **Low** and **High** temperature (in °C)  
    - **Color** (CSS name or `#RRGGBB`)  
    - **Sound Frequency** (base tone in Hz)  
  - You can **Add** or **Delete** rows dynamically.  
  - Press **Validate Data** before running to ensure:  
    - Low < High  
    - Valid color string or hex code  
    - Frequency is an integer ≥ 0  
  - Once validated, those ranges become the fixed thresholds for every frame.

---

## User Controls

In the options panel you can also toggle:

- **Enable Image Saving**  
  Save each processed thermal frame as a PNG in `Results/.../thermal/`.

- **Enable CSV Log**  
  Record per-frame stats (mean temperature, hot/cold counts, filenames) in a timestamped CSV.

- **Enable Frame Capture Save**  
  Snapshot the Matplotlib figure of each frame to `Results/.../*.png`.

- **Enable Sound File Save**  
  Write every generated soundscape to a WAV in `Results/.../audio/` before playback.

- **Enable Real-Time Visual Display**  
  Show or hide the live thermal image plot in the GUI.

- **Sample Rate**  
  Control how many audio samples per second are used (default 44100 Hz).

When **Default Mode** is selected, all custom-range controls are grayed out and ignored; conversely, in **Custom Mode** the automatic thresholds are disabled and your validated settings drive the entire pipeline.


---

## Installation Guide

**Requirements:** Raspberry Pi or Linux PC, Python 3.8+, MLX90640 sensor.



To get started, follow these steps:



**1.Clone the Repository**



git clone https://github.com/NoraTanous/Thermal-Sense.git

cd Thermal-Sense



**2.Create and Activate a Virtual Environment**



python3 -m venv venv

source venv/bin/activate



**3.Upgrade pip**



pip install --upgrade pip



**4.Install System Dependencies**



sudo apt-get update

sudo apt-get install -y libportaudio2 libatlas-base-dev



**5.Install Required Python Libraries**


pip install numpy

pip install matplotlib

pip install opencv-python

pip install sounddevice

pip install scipy

pip install adafruit-circuitpython-mlx90640

pip install adafruit-blinka



**6.Enable I2C Interface on Raspberry Pi**



sudo raspi-config

\# Go to Interfacing Options → I2C → Enable → Reboot when prompted



## Running the System



python main.py



**Saving and Logging**



You can save the following outputs:



Thermal Snapshots: Capture a frame of the thermal scene (CSV or PNG).



Audio Recordings: Save the real-time generated audio as a .wav file.



Data Logs: Log temperature readings over time in CSV or JSON format for analysis.



All outputs are saved in a designated output/ folder with timestamped filenames.


## Key Features 

- **Real-Time Thermal-to-Audio Conversion**  
  Continuously captures MLX90640 frames and immediately sonifies them into stereo “thermal soundscapes,” so you can literally _hear_ heat patterns as they occur.

- **Default vs. Custom Mode**  
  - **Default Mode** auto-computes hot/cold thresholds (μ ± σ) for a zero-config quick start (custom UI disabled).  
  - **Custom Mode** lets you define up to **7** named temperature ranges, each with its own low/high bounds, display color (CSS name or hex RGB), and base tone frequency.

- **Range Management UI**  
  - Add or remove up to 7 custom ranges  
  - Specify **Name**, **Low [°C]**, **High [°C]**, **Color** (text or RGB), **Frequency [Hz]**  
  - “Validate Data” button enforces that low < high, color names are valid, and frequencies are non-negative before starting

- **Comprehensive Logging & Saving**  
  - **Enable/Disable**: image saving (PNG), CSV logging, frame capture, audio file output (WAV)  
  - Each run creates a timestamped folder under `Results/ThermalSense-<YYYY-MM-DD_HH-MM-SS>/`  
  - CSV output includes frame number, mean temperature, heat category, file paths, and hot/cold counts

- **Real-Time Visualization Controls**  
  - **Enable/Disable** live Matplotlib display  
  - Overlays show current hot/cold/total column counts on the thermal image  
  - Smooth fade-in/out transitions for splash and stop backgrounds

- **Stereo Panning & Musical Mapping**  
  - Scans left-to-right: horizontal position → time & stereo pan  
  - Vertical position quantized to a pentatonic scale for harmonious chords  
  - “Hot” ranges use a brass-like timbre, “Cold” ranges use a reed-like timbre, “Neutral” can be silent

- **Modular, OOP Design**  
  - **ThermalSenseGUI**: user interface & control panel  
  - **ThermalSenseRunner**: threaded orchestration of capture → process → output → log  
  - **ThermalSenseInput**: MLX90640 I²C handling & display update  
  - **ThermalSense** (in `Dependencies/ThermalSense`): core image cleaning, color mapping & soundscape synthesis

- **Safe Threading & Shutdown**  
  - Start/Stop buttons launch or terminate the runner thread cleanly  
  - All resources (I²C bus, open files, Matplotlib figures) are released on exit



## Use Cases



ThermalSense Core can be applied in many creative and impactful ways:



Assistive Technology: Allow people with visual impairments to "hear" heat sources and better navigate spaces.



Home \& Maintenance: Identify overheating equipment, insulation failures, or air leaks hands-free.



Education: Teach students about temperature, infrared sensing, and alternative perception systems.



Research \& Development: Integrate into experimental setups, wearable devices, or even VR systems to explore sensory augmentation.
 
## Project Structure 

ThermalSense/
├── __pycache__/                 # Python byte-code cache
├── Backup/                      # (optional) previous versions or backups
├── Dependencies/
│   └── ThermalSense/            # Core thermal→audio engine
│       ├── __init__.py
│       ├── object_thermal_sound.py   # ThermalSense class: image & sound processing
│       └── …                     # any other helper modules
├── Pictures/                    # GUI splash & icon images
│   ├── Welcome.png
│   ├── ThermalSenseResults.png
│   └── StopBackground.png
├── Results/                     # Runtime output (auto-created)
│   └── ThermalSense-<timestamp>/
│       ├── cleaned/             # cleaned grayscale frames
│       ├── thermal/             # colorized thermal overlays
│       ├── audio/               # WAV soundscapes
│       └── ThermalSense-<timestamp>.csv
├── venv/                        # Python virtual-env (gitignored)
├── .gitignore
├── LICENSE
├── main.py                      # Launches ThermalSenseGUI
├── ObjectThermalSenseRunner.py  # ThermalSenseRunner: orchestrates loop, I/O, logging
├── README.md                    # This file
├── ThermalSenseInput.py         # MLX90640 sensor interface & live display
└── ThermalSense/                # (optional alias of Dependencies/ThermalSense)
