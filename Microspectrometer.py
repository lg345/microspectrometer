import seabreeze
import os
from datetime import date,datetime
seabreeze.use('pyseabreeze')
from seabreeze.spectrometers import list_devices, Spectrometer
import matplotlib.pyplot as plt
import numpy as np
from IPython import display
import time
# explicitly request pyseabreeze

class Spectrum:
    def __init__(self,scan_number,integration_time,measurement_time_stamp,wavelengths,counts,spectrum_type,comments):
        self.scan_number=scan_number
        self.measurement_time_stamp = measurement_time_stamp
        self.wavelengths = wavelengths
        self.counts = counts
        self.integration_time = integration_time
        self.spectrum_type = spectrum_type
        self.comments = comments
    
    def save_spectrum(self,filename = None):
        header='Scan Number: %d\n' % (self.scan_number)
        header+='Integration Time %.02f microseconds.\n' % (self.integration_time)
        header+='Spectrum Type: %s\n' % (self.spectrum_type)
        header+='Comments: %s\n' % self.comments
        if filename == None:
            filename = 'Scan_%d.xy' % (self.scan_number)
        np.savetxt(filename,np.transpose(np.vstack([self.wavelengths,self.counts])),header=header)

class Microspectrometer:
    def __init__(self):
        self.integration_time = 1.0E5
        self.collected_spectra = []
    
    def connect(self):   
        """
        Connects to the first available UV-Vis spectrometer. Make sure this is ran AFTER it is plugged in (power+usb)
        """
        self.spectrometer = Spectrometer.from_first_available(emulate=emulate)
        self.wavelengths = self.spectrometer.wavelengths()
        self.spectrometer.features['spectrometer'][0].set_integration_time_micros(self.integration_time)
        
    def disconnect(self):
        """
        Disconnects the current spectrometer instance from the physical device. 
        Usually only need this if the spectrometer was powered off or disconnected physically.
        ----------
        """
        self.spectrometer.close()
        
    def change_integration_time(self, integration_time):
        """
        Sets the integration time of the device in microseconds.
        Parameters
        ----------
        integration_time : float
            The desired integration time in microseconds. Default is 1E5.
        ----------
        """
        self.integration_time=integration_time
        self.spectrometer.features['spectrometer'][0].set_integration_time_micros(self.integration_time)
        #self.spectrometer.set_integration_time_micros(self.integration_time)#The default is 10k microseconds, 100ms.

    def measure(self, spectrum_type = 'current_spectrum', number_of_scans = 10, save = True, filename = None, comments='', store = True):
        """
        Measures the current spectrum for the attached spectrometer.
        Parameters
        ----------
        spectrum_type : string
            Identify what type of spectrum it is. Options: current_spectrum, reference, or dark.
            Using reference or dark will override the current ref or dark spectrum when measuring new spectra.
        number_of_scans : int
            Number of scans to use for the measurement.
        save : boolean
            If the file scan should be saved. The transmission spectrum.
        filename : string
            Name of the file if it is saved. It defaults to a datetime stamp for the filename.
        comments : string
            Comment for the scan.
        ----------
        """
        if spectrum_type not in ['current_spectrum','reference','dark']:
            raise Exception('Invalid spectrum_type.', 'Scans must be current_spectrum, reference, or dark.')     
        if spectrum_type == 'dark':
            self.dark = np.zeros(len(self.wavelengths))
        running_y=np.zeros(len(self.wavelengths))
        for scan in range(number_of_scans):
            running_y=running_y+self.spectrometer.intensities()-self.dark
        running_y = running_y/number_of_scans
        setattr(self,spectrum_type,running_y)
        self.datetime_stamp()
        cur_spec=Spectrum(len(self.collected_spectra),self.integration_time,
                              self.last_run_datetime,self.wavelengths,running_y,spectrum_type,comments=comments)
        if store:
            self.collected_spectra.append(cur_spec)
        if save:
            self.save_transmission(spectrum_type, filename,comments)
            
    def datetime_stamp(self):
        """
        Updates the objects datetime stamp for the current datetime.
        ----------
        """
        today=datetime.now()
        self.last_run_datetime=today.strftime('%m/%d/%Y %H:%M:%S')
        
    def start_new_experiment(self, directory=None):
        """
        Creates a new directory and chdir into that directory. Does not overwrite a previous directory.
        ----------
        directory : string
            The name of the directory. The default is a datestamped directory.
        ----------
        """
        today = date.today()
        if directory == None:
            d1 = today.strftime('%m%d%Y')
        else:
            d1 = directory
        
        os.makedirs(d1,exist_ok=True)
        os.chdir(d1)
    
    def plot_absorbance(self,save = False):
        """
        Plots the log10 absorbance of the current spectrum (last measured).
        ----------
        save : boolean
            Saves a .png of the absorbance. Not yet implemented.
        ----------
        """
        y = np.log10(self.reference/self.current_spectrum)
        x = self.wavelengths
        plt.figure(dpi=100)
        plt.plot(x,y)
        return plt.gcf()
             
    def save_transmission(self, spectrum_type, filename = None,comments=''):
        """
        Saves the transmission spectrum.
        ----------
        spectrum_type : string
            This defines which type of spectrum to save: current_spectrum, dark, or reference. 
        filename : string
            Name of the saved file. Defaults to datettime stamp.
        comments : string
            Comments to be included in the file. 
        ----------
        """
        y = getattr(self,spectrum_type)
        if filename == None:
            today=datetime.now()
            timestamp=today.strftime('%m_%d_%Y_%H_%M_%S')
            filename = 'UV_Vis_'+timestamp+'.xy'
        np.savetxt(filename,np.transpose(np.vstack([self.wavelengths,y])),header=comments)
        
    def save_absorbance(self, filename=None,comments=''):
        """
        Saves the current absorbance spectrum.
        ---------- 
        filename : string
            Name of the saved file. Defaults to datettime stamp.
        comments : string
            Comments to be included in the file. 
        ----------
        """
        if filename == None:
            today=datetime.now()
            timestamp=today.strftime('%m_%d_%Y_%H_%M_%S')
            filename = 'UV_Vis_abs_'+timestamp+'.xy'
        np.savetxt(filename,np.transpose(np.vstack([self.wavelengths,np.log10(self.reference/self.current_spectrum)])),header=comments)
        
    def load_spectrum(self, spectrum_type,filename):
        """
        Loads in ascii .xy spectra. Specifically to overwrite dark or reference with a previously measure spectrum.
        ---------- 
        spectrum_type : string
            Type of spectrum that the loaded file is. Options are dark and reference - could also do 
            current_spectrum but not sure why anyone would.
        filename : string
            Name of the file containing the data.
        ----------
        """
        y=np.loadtxt(filename)[:,1]
        setattr(self,spectrum_type,y)
    
    def save_all_spectra(self):
        """
        This is a backup method to dump all of the spectra out of memory in case they weren't being saved.
        ----------
        """
        for i in self.collected_spectra:
            i.save_spectrum()
    
    def describe_all_spectra(self):
        """
        Print out information of all the spectra currently stored in memory.
        ----------
        """
        print('Scan\tDateTime\tSpectrumType\tComment')
        for i in self.collected_spectra:
            print('%d\t%s\t%s\t%s' % (i.scan_number,i.measurement_time_stamp,i.spectrum_type,i.comments))
    
    def set_spectrum(self, spectrum_type,index):
        """
        Sets a spectrum in memory to a dark or reference. E.g. you want to replace the reference spectrum
        with an old scan that hasn't yet been saved. Or go back to an old dark/ref
        ----------
        spectrum_type : string
            Type of spectrum to replace: dark or reference
        index : integer
            The index of the scan: 'scan_number' that will replace either the dark or the reference.
        ----------

        """
        running_y=self.collected_spectra[index].counts
        setattr(self,spectrum_type,running_y)
        
    def continuous_measurements(self, update_time = 0.5, ref_spec_index=None, save = False):
        """
        Continuously measures and displays the absorbance spectrum to monitor over time. 
        To exit stop the kernel (don't restart it).
        ----------
        update_time : float
            Time in seconds to update the plot. 
        ref_spec_index : integer
            The index of the scan to use as a reference to compare to. 
            Not in the same sense as a reference spectrum for absorbance
            but a scan you also want plotted for comparison. 
        ----------

        """
        fig = plt.figure(dpi=100)
        ax = fig.add_subplot(111)
        plt.ion()
        x1 = self.wavelengths
        line1, = ax.plot(x1, self.current_spectrum, 'r-') # Returns a tuple of line objects, thus the comma
        if ref_spec_index == None:
            ref_spec_index=-1
        y_ref=np.log10(self.reference/self.collected_spectra[ref_spec_index].counts)
        plt.plot(x1,y_ref,'k-')
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Absorbance')
        plt.title('Running Absorption Spectrum. Every %.02f seconds and acq time.' % update_time)
        plt.legend(['Current Spectrum','Starting Spectrum'])
        while 1==1:
            try:
                self.measure(store = False, save = False)
                line1.set_ydata(np.log10(self.reference/self.current_spectrum))#This will plot the absorption spectrum which is the log of you reference divided by the sample.)
                plt.gcf().canvas.draw()
                display.clear_output(wait=True)
                display.display(plt.gcf())
                ax.relim()
                ax.autoscale_view()
                #plt.ylim([0,4])
                time.sleep(update_time)
            except KeyboardInterrupt:
                plt.close()
                break
    def continuous_transmission(self, update_time = 0.5, ref_spec_index=None,save = False):
        """
        Continuously measures and displays the transmission spectrum to monitor over time. 
        To exit stop the kernel (don't restart it). TODO: merge with above.
        ----------
        update_time : float
            Time in seconds to update the plot. 
        ref_spec_index : integer
            The index of the scan to use as a reference to compare to. 
            Not in the same sense as a reference spectrum for absorbance
            but a scan you also want plotted for comparison. 
        ----------

        """
        fig = plt.figure(dpi=100)
        ax = fig.add_subplot(111)
        plt.ion()
        x1 = self.wavelengths
        line1, = ax.plot(x1, self.current_spectrum, 'r-') # Returns a tuple of line objects, thus the comma
        if ref_spec_index == None:
            ref_spec_index=-1
        y_ref=self.collected_spectra[ref_spec_index].counts
        plt.plot(x1,y_ref,'k-')
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Absorbance')
        plt.title('Running Absorption Spectrum. Every %.02f seconds and acq time.' % update_time)
        plt.legend(['Current Spectrum','Starting Spectrum'])
        while 1==1:
            try:
                self.measure(store = False, save = save)
                line1.set_ydata(self.current_spectrum)#This will plot the absorption spectrum which is the log of you reference divided by the sample.)
                plt.gcf().canvas.draw()
                display.clear_output(wait=True)
                display.display(plt.gcf())
                ax.relim()
                ax.autoscale_view()
                #plt.ylim([0,4])
                time.sleep(update_time)
            except KeyboardInterrupt:
                plt.close()
                break