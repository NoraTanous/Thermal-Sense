ThermalSense  – Real-Time Thermal-to-Audio Perception System



ThermalSense is a project designed to translate thermal camera data into sound. By doing this, it enables users to "hear" temperature differences in their surroundings, offering a new way to sense the world—through sound.



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

**ThermalSense ** enables human perception of invisible heat patterns by translating thermal images into rich auditory cues.  
Inspired by landmark systems like *The vOICe* and *EyeMusic*, which encode visual features as sound, **ThermalSense** targets the infrared domain: it captures input from a thermal sensor and generates a structured soundscape representing the temperature distribution in a scene.
 Building on these ideas, ThermalSense specifically targets the infrared thermal spectrum: it takes input from a thermal sensor (infrared camera) and generates an auditory "thermal soundscape" that represents the temperature distribution of a scene.
Unlike traditional visual cameras, a thermal sensor captures the heat radiation of objects, revealing hot and cold areas that are otherwise invisible to the naked eye. ThermalSense processes this thermal data and maps it to sound in real-time. By listening to the output, users can localize and recognize thermal properties of objects or environments, effectively gaining a new sense for temperature differences.
An initial proof-of-concept study of the system showed that users could achieve high accuracy in identifying and localizing thermal features with only a short training period , indicating the practicality of the approach. 
This README  serves as a comprehensive technical guide to the ThermalSense Core system, detailing its design considerations, algorithmic implementation, object-oriented software architecture, and the step-by-step operation of the conversion from thermal data to audio signals. All aspects of the system—from signal generation and frequency-to-tone mapping, to the modular class structure of the code—are explained in depth to provide a clear understanding of how ThermalSense functions and how
it was engineered.


---

## System Architecture & OOP Model

The ThermalSense Core system is organized into distinct components that work together to capture thermal data and produce corresponding audio output. The design follows a modular object-oriented programming (OOP) model to ensure clarity, maintainability, and extensibility of the code.

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

ThermalSenseGUI → ThermalSenseRunner
The GUI is purely a control layer: it collects the settings (mode, ranges, logging options) and, when you hit Run, it launches a ThermalSenseRunner in the background. It never deals with sensor hardware or sound generation itself.

ThermalSenseRunner → ThermalSenseInput & ThermalSense
The Runner is the orchestrator. In a tight loop it:
Grabs frames from the camera via ThermalSenseInput

Hands each frame to ThermalSense for cleaning, color‐mapping, and sonification

Plays back the generated audio, updates the GUI plot, and writes logs/files

ThermalSenseInput
Responsibility: Only sensor I/O.
It opens the I²C connection to the MLX90640, reads each 24×32 thermal frame into a NumPy array, handles retries on errors, and returns clean raw data—nothing more.

ThermalSense
Responsibility: All data transformations.
Given a raw temperature array, it:

Cleans and inpaints non-thermal artifacts

Normalizes and colorizes pixels into a heatmap

Maps pixel positions and temperature bands (default or custom) to musical pitches and timbres

Builds the stereo audio buffer (sonic “heatmap”) and saves images/audio files

##  Data Flow 

**A single real-time frame processing cycle involves:**

1. **ThermalSenseInput – Frame Acquisition**

   * The method ThermalSenseInput.__init__() establishes the I2C connection with the MLX90640 thermal camera (self.i2c = busio.I2C(board.SCL, board.SDA)), initializes the sensor object (self.mlx), and pre-allocates a 1D float32 array self.frame to hold the incoming data.
   * Each time a new frame is needed, self.mlx.getFrame(self.frame) is called,  which fills that array with floating-point values (°C) for every pixel.
  Returns a flat buffer—no processing yet.

2. **ThermalSenseRunner – Frame Handling**

   * ThermalSenseRunner.run() operates in a loop, pulling each new frame from the sensor by calling self.thermal_sensor.mlx.getFrame(frame), then reshaping it to a 2D numpy array (24 rows × 32 columns) for spatial processing ,where each entry corresponds to a specific row/column in the camera’s field of view.
   * Loop Control This capture step runs inside a while running: loop so new frames are continually fetched at the configured sample rate.



3. **ThermalSense – Processing and Mapping**

   * The new frame (2D numpy array) is passed to ThermalSense.process_image(raw):

     * Calls ThermalSense.image_acquisition to resize and/or validate the incoming image (guaranteeing a consistent format for downstream processing).
     * Calls ThermalSense.remove_non_thermal to mask out and inpaint non-thermal artifacts, such as sensor reflections or environmental noise.
     * Flips or rotates the frame so “up” in the thermal view matches “up” in the user’s perspective.
     * generate_colored_thermal_image() colors each pixel according to its temperature range (hot/cold/neutral or custom ranges).
     * create_soundscape() :
       Divides the image into vertical slices (columns).
       For each column, maps pixel heights to musical pitches (quantized to a pentatonic scale) and temperatures to timbres (brass for heat, reed for cold).
       Builds a stereo audio buffer by mixing all tones, applying left-right panning based on column position, and normalizing to prevent clipping.
    

4. **ThermalSenseRunner – Output and Feedback**

   * Receives the cleaned image and soundscape array.
   * Saves files (PNG images, WAV audio) to the appropriate result directories if enabled.
   * Logs statistics (mean temp, hot/cold column counts, etc.) to CSV.
   * Triggers real-time playback (play_audio(wav_path)) and updates GUI overlays to indicate hot/cold/total counts per frame.
   * The entire process loops at a rate set by the GUI/sample rate, providing near real-time feedback.

5. **ThermalSenseGUI – User Control**

   * Runtime adjustment - the user can Enable/Disable modes (Default vs. Custom), enable/disable logging or image saving, and start or stop the loop at any time.
   * Clean Exit - When the user hit Stop or Exit, the GUI signals the runner to end its loop, waits for the thread to finish, closes any open files or hardware connections,     and returns control to the user .

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

Once we have a cleaned, normalized thermal image, we need to turn its 2D temperature data into a 1D sequence of sounds. ThermalSense does this in two main steps:

** Spatial → Temporal & Pitch Encoding

*Horizontal → Time
We “scan” the image left-to-right, one column at a time. If a full sweep is 3 s and there are 32 columns, each column gets ~0.094 s of audio.

*Vertical → Pitch
Within each column, a pixel’s row (top → bottom) maps to a musical pitch: top rows become higher notes, bottom rows lower notes. We compute a raw frequency and then snap it to the nearest note in a pentatonic scale so every chord stays harmonious.

**Temperature → Volume & Timbre

*Volume scales with how hot (or cold) the pixel is—hotter = louder, cooler = softer.

*Timbre defaults to two instrument voices:

Brass-like for “warm”/“hot” ranges (rich, harmonic waveform)

Reed-like for “cool” ranges (pure sine with light vibrato)

*In Custom Mode, you supply your own frequency for each named temperature band—so you could even make “warm” pixels always play at 880 Hz, regardless of row.

**Chord Assembly & Stereo Panning

If multiple pixels in one column fall into active ranges, we play all their notes simultaneously (a chord).

We pan each column’s chord slightly left or right in stereo—early columns favor the left speaker, later columns the right—giving an extra spatial cue.



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
Once the mapping algorithm has decided what notes to play and when, ThermalSense must actually produce the corresponding sound waves. This section breaks down how we turn those abstract “note events” into real audio you can hear.

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
