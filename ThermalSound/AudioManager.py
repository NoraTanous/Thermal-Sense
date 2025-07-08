import pygame
import os , time

class AudioManager:
    def __init__(self, sound_dir='ThermalSense/Sounds'):
        pygame.mixer.init()
        pygame.mixer.music.set_volume(0.8)
        base_path = os.path.dirname(os.path.abspath(__file__))  # path to main thermalSense Project
        self.sound_dir = os.path.join(base_path, sound_dir)

        self.sounds = {}
        self.load_sounds()

    def load_sounds(self):
        for filename in os.listdir(self.sound_dir):
            if filename.endswith('.wav') or filename.endswith('.mp3') or filename.endswith('.ogg') or filename.endswith('.mod'):
                sound_name = os.path.splitext(filename)[0]
                sound_path = os.path.join(self.sound_dir, filename)
                self.sounds[sound_name] = pygame.mixer.Sound(sound_path)
                

    def play_sound(self, sound_name):
        if sound_name in self.sounds:
            self.sounds[sound_name].play()
            time.sleep(2)  # Wait for 2 seconds before playing the next sound
        else:
            print(f"Sound '{sound_name}' not found.")

    def stop_sound(self, sound_name):   
        if sound_name in self.sounds:
            self.sounds[sound_name].stop()
        else:
            print(f"Sound '{sound_name}' not found.")           
    
    def set_volume(self, sound_name, volume):
        if sound_name in self.sounds:
            self.sounds[sound_name].set_volume(volume)
        else:
            print(f"Sound '{sound_name}' not found.")                           
        
    def stop_all_sounds(self):
        for sound in self.sounds.values():
            sound.stop()

    def pause_all_sounds(self):
        pygame.mixer.pause()

    def unpause_all_sounds(self):
        pygame.mixer.unpause()
    
    def quit(self):
        pygame.mixer.quit()
        
# Example usage:

if __name__ == "__main__":  
    audio_manager = AudioManager()
    for key, value in audio_manager.sounds.items():
        print(f"Loaded sound: {key}")
    # Play a sound  
    audio_manager.play_sound('very_cold_range')
    time.sleep(1.3)  # Replace 'example_sound' with the actual sound file name without extension
  #  audio_manager.set_volume('1', 1.0)  # Set volume to 50%
    audio_manager.play_sound('3')
      # Replace 'example_sound' with the actual sound file name without extension
   # audio_manager.set_volume('example_sound', 0.5)  # Set volume to 50%
    #audio_manager.stop_sound('example_sound')
    #audio_manager.quit()
# Note: Ensure you have the pygame library installed and the sound files in the specified directory.        
# You can install pygame using pip:
# pip install pygame
# Make sure to replace 'example_sound' with the actual sound file name without extension.
