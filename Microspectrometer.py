import os
from datetime import datetime
import seabreeze
from seabreeze.spectrometers import Spectrometer
seabreeze.use('cseabreeze')
import matplotlib.pyplot as plt
import numpy as np
from IPython import display
import time

class Spectrum:
    def __init__(self, scan_number, integration_time, measurement_time_stamp, wavelengths, counts, spectrum_type, comments):
        """
        Initialize a Spectrum object.

        Parameters:
        -----------
        scan_number : int
            The unique identifier for the spectrum.
        integration_time : float
            The integration time in microseconds used to capture the spectrum.
        measurement_time_stamp : str
            The timestamp when the spectrum was measured.
        wavelengths : array-like
            Array containing the wavelengths of the spectrum.
        counts : array-like
            Array containing the corresponding counts of the spectrum.
        spectrum_type : str
            Type of the spectrum (e.g., current_spectrum, reference, dark).
        comments : str
            Comments or additional information about the spectrum.
        """
        self.scan_number = scan_number
        self.measurement_time_stamp = measurement_time_stamp
        self.wavelengths = wavelengths
        self.counts = counts
        self.integration_time = integration_time
        self.spectrum_type = spectrum_type
        self.comments = comments
    
    def save_spectrum(self, filename=None):
        """
        Save the spectrum data to a file.

        Parameters:
        -----------
        filename : str, optional
            Name of the file to save the spectrum data. If not provided, a default filename will be used.
        """
        header = f'Scan Number: {self.scan_number}\nIntegration Time: {self.integration_time:.02f} microseconds.\nSpectrum Type: {self.spectrum_type}\nComments: {self.comments}\n'
        if filename is None:
            filename = f'Scan_{self.scan_number}.xy'
        np.savetxt(filename, np.transpose(np.vstack([self.wavelengths, self.counts])), header=header)

class Microspectrometer:
    def __init__(self):
        """
        Initialize a Microspectrometer object with default integration time and an empty list for collected spectra.
        """
        self.integration_time = 1.0E5
        self.collected_spectra = []
    
    def connect(self):   
        """
        Connect to the first available UV-Vis spectrometer. Ensure the device is powered and connected before running this.
        """
        self.spectrometer = Spectrometer.from_first_available()
        self.wavelengths = self.spectrometer.wavelengths()
        self.spectrometer.features['spectrometer'][0].set_integration_time_micros(self.integration_time)
        
    def disconnect(self):
        """
        Disconnect the current spectrometer instance from the physical device.
        """
        self.spectrometer.close()
        
    def change_integration_time(self, integration_time):
        """
        Change the integration time of the device.

        Parameters:
        -----------
        integration_time : float
            The desired integration time in microseconds.
        """
        self.integration_time = integration_time
        self.spectrometer.features['spectrometer'][0].set_integration_time_micros(self.integration_time)

    def measure(self, spectrum_type='current_spectrum', number_of_scans=10, save=True, filename=None, comments='', store=True):
        """
        Measure the current spectrum for the attached spectrometer.

        Parameters:
        -----------
        spectrum_type : str
            Identify what type of spectrum it is. Options: current_spectrum, reference, or dark.
        number_of_scans : int
            Number of scans to use for the measurement.
        save : bool
            Whether to save the measured spectrum.
        filename : str, optional
            Name of the file to save the spectrum data.
        comments : str
            Comment for the scan.
        store : bool
            Whether to store the measured spectrum in memory.
        """
        if spectrum_type not in ['current_spectrum', 'reference', 'dark']:
            raise ValueError('Invalid spectrum_type. Scans must be current_spectrum, reference, or dark.')     
        if spectrum_type == 'dark':
            self.dark = np.zeros(len(self.wavelengths))
        running_y = np.zeros(len(self.wavelengths))
        for _ in range(number_of_scans):
            running_y += self.spectrometer.intensities() - self.dark
        running_y /= number_of_scans
        setattr(self, spectrum_type, running_y)
        self.datetime_stamp()
        cur_spec = Spectrum(len(self.collected_spectra), self.integration_time, self.last_run_datetime, self.wavelengths, running_y, spectrum_type, comments=comments)
        if store:
            self.collected_spectra.append(cur_spec)
        if save:
            self.save_transmission(spectrum_type, filename, comments)
            
    def datetime_stamp(self):
        """
        Updates the object's datetime stamp for the current datetime.
        """
        self.last_run_datetime = datetime.now().strftime('%m/%d/%Y %H:%M:%S')
        
    def start_new_experiment(self, directory=None):
        """
        Creates a new directory and changes directory into that directory. Does not overwrite a previous directory.

        Parameters:
        -----------
        directory : str
            The name of the directory. The default is a date-stamped directory.
        """
        today = datetime.now().strftime('%m%d%Y')
        d1 = directory or today
        os.makedirs(d1, exist_ok=True)
        os.chdir(d1)
    
    def plot_absorbance(self, save=False):
        """
        Plots the log10 absorbance of the current spectrum (last measured).

        Parameters:
        -----------
        save : bool
            Saves a .png of the absorbance. Not yet implemented.
        """
        y = np.log10(self.reference/self.current_spectrum)
        x = self.wavelengths
        plt.figure(dpi=100)
        plt.plot(x, y)
        return plt.gcf()
             
    def save_transmission(self, spectrum_type, filename=None, comments=''):
        """
        Saves the transmission spectrum.

        Parameters:
        -----------
        spectrum_type : str
            This defines which type of spectrum to save: current_spectrum, dark, or reference. 
        filename : str, optional
            Name of the saved file. Defaults to datetime stamp.
        comments : str
            Comments to be included in the file. 
        """
        y = getattr(self, spectrum_type)
        filename = filename or f'UV_Vis_{datetime.now().strftime("%m_%d_%Y_%H_%M_%S")}.xy'
        np.savetxt(filename, np.transpose(np.vstack([self.wavelengths, y])), header=comments)
        
    def save_absorbance(self, filename=None, comments=''):
        """
        Saves the current absorbance spectrum.

        Parameters:
        -----------
        filename : str, optional
            Name of the saved file. Defaults to datetime stamp.
        comments : str
            Comments to be included in the file. 
        """
        filename = filename or f'UV_Vis_abs_{datetime.now().strftime("%m_%d_%Y_%H_%M_%S")}.xy'
        np.savetxt(filename, np.transpose(np.vstack([self.wavelengths, np.log10(self.reference/self.current_spectrum)])), header=comments)
        
    def load_spectrum(self, spectrum_type, filename):
        """
        Loads ascii .xy spectra to overwrite dark or reference with a previously measured spectrum.

        Parameters:
        -----------
        spectrum_type : str
            Type of spectrum that the loaded file is. Options are dark and reference.
        filename : str
            Name of the file containing the data.
        """
        y = np.loadtxt(filename)[:, 1]
        setattr(self, spectrum_type, y)
    
    def save_all_spectra(self):
        """
        Backup method to dump all spectra out of memory in case they weren't being saved.
        """
        for i in self.collected_spectra:
            i.save_spectrum()
    
    def describe_all_spectra(self):
        """
        Print out information of all the spectra currently stored in memory.
        """
        print('Scan\tDateTime\tSpectrumType\tComment')
        for i in self.collected_spectra:
            print(f'{i.scan_number}\t{i.measurement_time_stamp}\t{i.spectrum_type}\t{i.comments}')
    
    def set_spectrum(self, spectrum_type, index):
        """
        Sets a spectrum in memory to a dark or reference.

        Parameters:
        -----------
        spectrum_type : str
            Type of spectrum to replace: dark or reference
        index : int
            The index of the scan to replace either the dark or the reference.
        """
        running_y = self.collected_spectra[index].counts
        setattr(self, spectrum_type, running_y)
        
    def continuous_measurements(self, update_time=0.5, ref_spec_index=None, save=False):
        """
        Continuously measures and displays the absorbance spectrum to monitor over time.

        Parameters:
        -----------
        update_time : float
            Time in seconds to update the plot. 
        ref_spec_index : int
            The index of the scan to use as a reference to compare to.
        """
        fig = plt.figure(dpi=100)
        ax = fig.add_subplot(111)
        plt.ion()
        x1 = self.wavelengths
        line1, = ax.plot(x1, self.current_spectrum, 'r-') # Returns a tuple of line objects, thus the comma
        if ref_spec_index is None:
            ref_spec_index = -1
        y_ref = np.log10(self.reference/self.collected_spectra[ref_spec_index].counts)
        plt.plot(x1, y_ref, 'k-')
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Absorbance')
        plt.title(f'Running Absorption Spectrum. Every {update_time:.02f} seconds and acquisition time.')
        plt.legend(['Current Spectrum', 'Starting Spectrum'])
        while True:
            try:
                self.measure(store=False, save=False)
                line1.set_ydata(np.log10(self.reference/self.current_spectrum))
                plt.gcf().canvas.draw()
                display.clear_output(wait=True)
                display.display(plt.gcf())
                ax.relim()
                ax.autoscale_view()
                time.sleep(update_time)
            except KeyboardInterrupt:
                plt.close()
                break
                
    def continuous_transmission(self, update_time=0.5, ref_spec_index=None, save=False):
        """
        Continuously measures and displays the transmission spectrum to monitor over time.

        Parameters:
        -----------
        update_time : float
            Time in seconds to update the plot. 
        ref_spec_index : int
            The index of the scan to use as a reference to compare to.
        save : bool
            Whether to save the continuously measured spectra.
        """
        fig = plt.figure(dpi=100)
        ax = fig.add_subplot(111)
        plt.ion()
        x1 = self.wavelengths
        line1, = ax.plot(x1, self.current_spectrum, 'r-') # Returns a tuple of line objects, thus the comma
        if ref_spec_index is None:
            ref_spec_index = -1
        y_ref = self.collected_spectra[ref_spec_index].counts
        plt.plot(x1, y_ref, 'k-')
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Absorbance')
        plt.title(f'Running Absorption Spectrum. Every {update_time:.02f} seconds and acquisition time.')
        plt.legend(['Current Spectrum', 'Starting Spectrum'])
        while True:
            try:
                self.measure(store=False, save=save)
                line1.set_ydata(self.current_spectrum)
                plt.gcf().canvas.draw()
                display.clear_output(wait=True)
                display.display(plt.gcf())
                ax.relim()
                ax.autoscale_view()
                time.sleep(update_time)
            except KeyboardInterrupt:
                plt.close()
                break
