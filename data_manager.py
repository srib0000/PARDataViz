from PySide6.QtCore import QObject, Signal, Slot
from scan_set import ScanSet
from scan import Scan
from pathlib import Path
from radar_volume import RadarVolume
from background_loader import BackgroundLoader
import numpy as np

class Data_Manager(QObject):
    """
    Data manager for managing radar volume files and loading them in the background.
    """
    scan_selected = Signal(str)
    num_volumes_changed = Signal(int)
    # volume_loaded = Signal(str, object)
    render_volume = Signal(RadarVolume)

    def __init__(self, num_files_to_load=2):
        super().__init__()
        self.selected_scan = None
        self.mat_files = []
        self.current_index = 0
        # Number of files "around" the current file to load, i.e. the total number of mat files loaded at a given time will be (2 * num_files_to_load + 1).
        # E.g. num_files_to_load = 2 -> matfiles loaded = (2 * 2 + 1) = 5
        self.num_files_to_load = num_files_to_load
        self.loaded_volumes = {}
        self.loader = BackgroundLoader()
        self.loader.volume_loaded.connect(self.on_volume_loaded)

    def get_current_index(self):
        return self.current_index

    def set_current_index(self, index):
        print(f"Data Manger: Index {index} requested")
        if 0 <= index <= len(self.mat_files):
            self.current_index = index
            # Remove files outside the range
            self._cleanup_distant_files()
            self._load_surrounding_files()

            if self.mat_files[index] in self.loaded_volumes:
                self.render_volume.emit(self.loaded_volumes[self.mat_files[index]])

    def _load_surrounding_files(self):
        """
        Load files within the range of `num_files_to_load` around the current index.
        """
        start_index = max(0, self.current_index - self.num_files_to_load)
        end_index = min(len(self.mat_files), self.current_index + self.num_files_to_load + 1)

        for i in range(start_index, end_index):
            filename = self.mat_files[i]
            # Avoid reloading already loaded files
            if filename not in self.loaded_volumes and self.files_state[i] == 0:
                # Set the state tracker to loading
                self.files_state[i] = 1 
                self.loader.load_volume(filename)

    def _cleanup_distant_files(self):
        """
        Remove files from the loaded volumes that are not within the range of the current index.
        """
        start_index = max(0, self.current_index - self.num_files_to_load)
        end_index = min(len(self.mat_files), self.current_index + self.num_files_to_load + 1)
        nearby_files = set(self.mat_files[start_index:end_index])

        # Identify and remove files that are not "nearby"
        files_to_remove = [filename for filename in self.loaded_volumes if filename not in nearby_files]
        for filename in files_to_remove:
            index = self.mat_files.index(filename)
            print(f'Data Manager: Unloaded index {self.mat_files.index(filename)} {filename}')
            self.files_state[index] = 0
            del self.loaded_volumes[filename]

    @Slot(RadarVolume)
    def on_volume_loaded(self, r_volume: RadarVolume):
        """
        Slot to handle when a volume is loaded.
        """
        index = self.mat_files.index(r_volume.filename)
        self.loaded_volumes[r_volume.filename] = r_volume
        print(f"Data Manager: Loaded index {index} {r_volume.filename} {r_volume.products['Z'].shape}")
        # self.volume_loaded.emit(filename, r_volume)
        
        # Set the state tracker to loaded
        self.files_state[index] = 2

        # This covers the case when a scan is first selected. The first volume will be loaded asynchronously but everyone will need to be notified when it is loaded.
        if self.mat_files[self.current_index] == r_volume.filename:
            print(f"Just loaded volume for current index, requesting rendering! {r_volume.filename}")
            self.render_volume.emit(r_volume)


    @Slot(ScanSet)
    def on_scanset_load(self, scanset: ScanSet):
        print(f'Data manager now working with scanset "{scanset.get_name()}".')
        self.scanset = scanset
        if len(self.scanset.get_scans()) > 0:
            self.on_scan_selected(self.scanset.get_scans()[0])

    @Slot(str)
    def on_scan_selected(self, scan: Scan):
        print(f'Setting selected scan to "{scan.get_name()}"')
        self.selected_scan = scan
        self.reinitialize_file_list()
    
    def reinitialize_file_list(self):
        if self.selected_scan is not None:
            self.mat_files.clear()

            # Working from the base directory for the scanset
            base_dir = self.scanset.get_base_dir()
            # Loop over all the files in the current scan
            for filename in self.selected_scan.get_scan_files():
                
                # Extract the time for each scan file
                # timestamp = self.extract_timestamp_from_filename(filename)

                # if timestamp is not None:

                mat_file = base_dir / Path(filename)

                # self.scan_times.append((timestamp, mat_file))
                self.mat_files.append(mat_file)
            
            # This 1-D numpy array tracks the current state of each file:
            #
            # 0 - unloaded
            # 1 - loading
            # 2 - loaded
            #
            # The data manager will use this array to avoid requesting to load the same file multiple times.
            self.files_state = np.zeros(len(self.mat_files))
            
            self.set_current_index(0)
            self.num_volumes_changed.emit(len(self.mat_files))


    # def extract_timestamp_from_filename(self, filename):
    #     try:
    #         timestamp_str = filename.split('_')[1] + filename.split('_')[2][:6]
    #         return timestamp_str
    #     except IndexError:
    #         return None