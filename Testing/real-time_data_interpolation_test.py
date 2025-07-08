# -*- coding: utf-8 -*-

"""
Real-time data interpolation and visualization using MLX90640 thermal camera
This script captures thermal data from the MLX90640 sensor and visualizes it in real-time using Matplotlib.         
It also handles potential errors during data retrieval and provides a retry mechanism.
"""

import time
import board
import busio
import numpy as np
import adafruit_mlx90640
import matplotlib.pyplot as plt
 
def initialize_sensor():
    i2c = busio.I2C(board.SCL, board.SDA)
    mlx = adafruit_mlx90640.MLX90640(i2c)
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
    return mlx
 
def setup_plot():
    plt.ion()
    fig, ax = plt.subplots(figsize=(12, 7))
    therm1 = ax.imshow(np.zeros((24, 32)), vmin=0, vmax=60, cmap='inferno', interpolation='bilinear')
    cbar = fig.colorbar(therm1)
    cbar.set_label('Temperature [°C]', fontsize=14)
    plt.title('Thermal Image')
    return fig, ax, therm1
 
def update_display(fig, ax, therm1, data_array):
    therm1.set_data(np.fliplr(data_array))
    therm1.set_clim(vmin=np.min(data_array), vmax=np.max(data_array))
    fig.canvas.draw()
    fig.canvas.flush_events()
 
def main():
    mlx = initialize_sensor()
    fig, ax, therm1 = setup_plot()
    
    frame = np.zeros((24*32,))
    t_array = []
    max_retries = 5
 
    while True:
        t1 = time.monotonic()
        retry_count = 0
        while retry_count < max_retries:
            try:
                mlx.getFrame(frame)
                data_array = np.reshape(frame, (24, 32))
                update_display(fig, ax, therm1, data_array)
                plt.pause(0.001)
                t_array.append(time.monotonic() - t1)
                print('Sample Rate: {0:2.1f}fps'.format(len(t_array) / np.sum(t_array)))
                break
            except ValueError:
                retry_count += 1
            except RuntimeError as e:
                retry_count += 1
                if retry_count >= max_retries:
                    print(f"Failed after {max_retries} retries with error: {e}")
                    break
 
if __name__ == '__main__':
    main()