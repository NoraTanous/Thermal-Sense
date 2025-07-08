import time
import board
import busio
import numpy as np
import adafruit_mlx90640
 
def main():
    # Setup I2C connection
    i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
    mlx = adafruit_mlx90640.MLX90640(i2c)
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ
 
    frame = np.zeros((24 * 32,))  # Initialize the array for all 768 temperature readings
 
    while True:
        try:
            mlx.getFrame(frame)  # Capture frame from MLX90640
            average_temp_c = np.mean(frame)
            average_temp_f = (average_temp_c * 9.0 / 5.0) + 32.0
            print(f"Average MLX90640 Temperature: {average_temp_c:.1f}C ({average_temp_f:.1f}F)")
            time.sleep(0.5)  # Adjust this value based on how frequently you want updates
 
        except ValueError as e:
            print(f"Failed to read temperature, retrying. Error: {str(e)}")
            time.sleep(0.5)  # Wait a bit before retrying to avoid flooding with requests
        except KeyboardInterrupt:
            print("Exiting...")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
 
if __name__ == "__main__":
    main()