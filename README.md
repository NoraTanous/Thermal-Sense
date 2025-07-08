ThermalSense Core – Real-Time Thermal-to-Audio Perception System



ThermalSense Core is an open-source Python project designed to translate thermal camera data into sound. By doing this, it enables users to "hear" temperature differences in their surroundings, offering a new way to sense the world—through sound.



The idea behind ThermalSense is to provide real-time auditory feedback that reflects thermal information captured by infrared cameras. For example, hotter regions produce higher-pitched sounds, and cooler ones are represented with lower tones. This sensory substitution system can be especially helpful in assistive technologies for visually impaired users, in education for teaching about thermal imaging and perception, or in research and experimentation with human-computer interaction systems.



The system works by continuously capturing data from a thermal sensor (like the MLX90640), processing it, and mapping temperature values to audio cues. The sound updates in real-time, offering immediate spatial and thermal feedback. Depending on the configuration, users can hear different tone schemes, adjust the temperature range for detection, save audio logs, and even snapshot thermal images as CSV or PNG files. The sound can also pan left to right to help locate the source of heat across a scene.



ThermalSense is built with modularity in mind. It separates sensor input, processing logic, and audio output into distinct components, making it easy to add support for new sensors or experiment with different auditory mappings.





Key Features:



Real-Time Audio Feedback: The system transforms temperature readings into sounds instantly, enabling users to identify heat sources quickly.



Custom Temperature Ranges: Users can define the minimum and maximum temperature of interest and tune the audio mapping accordingly.



Interactive Controls: Easily start or stop sensing, tweak parameters like audio volume or scanning speed, and switch tone schemes via config or command-line options.



Audio and Image Output: Save live sound as .wav files, thermal images as .png, or temperature matrices as .csv for analysis or demonstrations.



Hardware Agnostic \& Modular: Works with various thermal sensors and is organized to support extension and development by others.



----------------------------------------------------------------------------------------------------------------------------------





Installation Guide (Raspberry Pi or Linux PC)



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



**Running the System**



python main.py



**Saving and Logging**



You can save the following outputs:



Thermal Snapshots: Capture a frame of the thermal scene (CSV or PNG).



Audio Recordings: Save the real-time generated audio as a .wav file.



Data Logs: Log temperature readings over time in CSV or JSON format for analysis.



All outputs are saved in a designated output/ folder with timestamped filenames.





**Use Cases**



ThermalSense Core can be applied in many creative and impactful ways:



Assistive Technology: Allow people with visual impairments to "hear" heat sources and better navigate spaces.



Home \& Maintenance: Identify overheating equipment, insulation failures, or air leaks hands-free.



Education: Teach students about temperature, infrared sensing, and alternative perception systems.



Research \& Development: Integrate into experimental setups, wearable devices, or even VR systems to explore sensory augmentation.


**Project Structure:**

ThermalSense/

├── main.py                    # Entry script

├── thermal\_core.py            # Core logic for thermal processing

├── sensors/                   # Sensor drivers (MLX90640, AMG8833, FLIR)

├── audio/                     # Audio generation and tone mapping

├── utils/                     # Math, scaling, helpers

├── gui/                       # Optional GUI for visualization/control

├── output/                    # Output data folder (created on runtime)

├── config.example.yaml        # Sample config (can be copied to config.yaml)

└── README.md                  # Documentation





