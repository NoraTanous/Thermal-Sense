import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ThermalSense import ThermalSense

ts = ThermalSense()
ts.run()