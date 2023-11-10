# Microspectrometer Manual

## Introduction
This manual provides guidance on using the provided Python code to control a UV-Vis spectrometer using the SeaBreeze library. The code is designed to connect to a UV-Vis spectrometer, measure spectra, and perform various operations such as saving, plotting, and continuous monitoring of absorption or transmission spectra.

## Requirements
Before using the code, ensure the following requirements are met:

- Python 3.x installed.
- SeaBreeze library installed (`pip install seabreeze`).
- `pyseabreeze` installed (`pip install pyseabreeze`).
- Matplotlib library installed (`pip install matplotlib`).

## Code Overview

### Spectrum Class
The `Spectrum` class represents a spectrum and has the following attributes:

- `scan_number`: Scan number identifier.
- `integration_time`: Integration time in microseconds.
- `measurement_time_stamp`: Timestamp of the measurement.
- `wavelengths`: Array of wavelengths.
- `counts`: Array of counts corresponding to the wavelengths.
- `spectrum_type`: Type of spectrum (current_spectrum, reference, dark).
- `comments`: Comments associated with the spectrum.

### Microspectrometer Class
The `Microspectrometer` class manages the UV-Vis spectrometer and provides various methods to control and monitor the spectrometer.

#### Methods:

- `connect()`: Connects to the first available UV-Vis spectrometer.
- `disconnect()`: Disconnects the connected spectrometer.
- `change_integration_time(integration_time)`: Sets the integration time of the device in microseconds.
- `measure(spectrum_type, number_of_scans, save, filename, comments, store)`: Measures the current spectrum for the attached spectrometer.
- `datetime_stamp()`: Updates the object's datetime stamp for the current datetime.
- `start_new_experiment(directory)`: Creates a new directory for storing data.
- `plot_absorbance(save)`: Plots the log10 absorbance of the current spectrum.
- `save_transmission(spectrum_type, filename, comments)`: Saves the transmission spectrum.
- `save_absorbance(filename, comments)`: Saves the current absorbance spectrum.
- `load_spectrum(spectrum_type, filename)`: Loads an ASCII .xy spectrum to overwrite dark or reference.
- `save_all_spectra()`: Dumps all spectra in memory to files.
- `describe_all_spectra()`: Prints information about all stored spectra.
- `set_spectrum(spectrum_type, index)`: Sets a spectrum in memory to a dark or reference.
- `continuous_measurements(update_time, ref_spec_index)`: Continuously measures and displays the absorbance spectrum.
- `continuous_transmission(update_time, ref_spec_index)`: Continuously measures and displays the transmission spectrum.

## Getting Started

1. Import the required libraries.
   ```python
   import seabreeze
   import os
   from datetime import date, datetime
   from seabreeze.spectrometers import list_devices, Spectrometer
   import matplotlib.pyplot as plt
   import numpy as np
   from IPython import display
   import time
   # explicitly request pyseabreeze
   seabreeze.use('pyseabreeze')
2. Create an instance of the Microspectrometer class.
   spectrometer = Microspectrometer()
3. Connect to the spectrometer.
   spectrometer.connect()
4. Perform measurements using the measure method, and save or analyze the spectra as needed.

## Example Code
```python
# Example Usage with New Experiment
spectrometer = Microspectrometer()

# Connect to the spectrometer
spectrometer.connect()

# Start a new experiment with a custom directory name
experiment_directory = 'my_experiment'
spectrometer.start_new_experiment(directory=experiment_directory)

# Perform a measurement
spectrometer.measure(spectrum_type='current_spectrum', number_of_scans=10, save=True)

# Plot absorbance
spectrometer.plot_absorbance(save=False)

# Save transmission spectrum
spectrometer.save_transmission(spectrum_type='current_spectrum')

# Disconnect from the spectrometer
spectrometer.disconnect()

