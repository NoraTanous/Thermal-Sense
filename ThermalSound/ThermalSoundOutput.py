import random
import time
import AudioManager

class ThermalSoundOutput:
    def __init__(self, sound_dir='Sounds'):
        self.audio_manager = AudioManager.AudioManager(sound_dir)

    def play_sound_by_temperature(self, temperature):
        temperature = int(temperature)
        if temperature in range(0, 10):
            self.play_sound('very_cold_range')
            time.sleep(1)
            self.play_temperature_value(temperature)
        elif temperature in range(10, 20):
            self.play_sound('cold_range')
            time.sleep(1)
            self.play_temperature_value(temperature)
        elif temperature in range(20, 30):
            self.stop_all_sounds()
            time.sleep(1)
        elif temperature in range(30, 40):
            self.play_sound('warm_range')
            time.sleep(1)
            self.play_temperature_value(temperature)
        elif temperature in range(40, 70):
            self.play_sound('hot_range')
            time.sleep(1)
            self.play_temperature_value(temperature)
        elif temperature >= 70:
            self.play_temperature_value(temperature)
            time.sleep(1)
            self.play_sound('alert')
        else:
            self.stop_all_sounds()

    def play_temperature_value(self, temperature):
        if 0 <= temperature < 100:
            self.play_sound(str(temperature))
        else:
            print("Temperature out of range")

    def play_sound(self, sound_name):
        self.audio_manager.play_sound(sound_name)

    def stop_sound(self, sound_name):
        self.audio_manager.stop_sound(sound_name)

    def set_volume(self, sound_name, volume):
        self.audio_manager.set_volume(sound_name, volume)

    def stop_all_sounds(self):
        self.audio_manager.stop_all_sounds()

    def pause_all_sounds(self):
        self.audio_manager.pause_all_sounds()

    def unpause_all_sounds(self):
        self.audio_manager.unpause_all_sounds()

    def quit(self):
        self.audio_manager.quit()


# Example test loop
if __name__ == "__main__":
    thermal_sensor = ThermalSoundOutput()

    try:
        while True:
            random_temperature = random.randint(0, 100)
            print(f"Current temperature: {random_temperature} C")
            thermal_sensor.play_sound_by_temperature(random_temperature)
            print("Waiting for next temperature reading...")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nExiting program...")
        thermal_sensor.quit()
