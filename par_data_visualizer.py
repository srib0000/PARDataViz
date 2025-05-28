import os
import sys
import random
import vispy.app
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QDockWidget, QFileDialog, QLabel)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal, Slot
from data_manager import Data_Manager
from scan_set import ScanSet
from scanset_builder import ScansetBuilder
from volume_slice_selector import VolumeSliceSelector
from dynamic_dock_widget import DynamicDockWidget
from timeline_controls import TimelineControls
from slice_plot import SlicePlot
from radar_volume import RadarVolume

class PARDataVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PAR Data Visualizer")
        self.setGeometry(0, 0, 1600, 900)

        # Volume data manager
        self.data_manager = Data_Manager(num_files_to_load=10)

        # Menu bar and related actions
        menu_bar = self.menuBar()
        self.file_menu = menu_bar.addMenu("File")
        
        new_scanset_action = QAction("New scanset...", self, shortcut="Ctrl+N")
        new_scanset_action.triggered.connect(self.new_scanset)
        self.file_menu.addAction(new_scanset_action)

        load_scanset_action = QAction("Load scanset...", self, shortcut="Ctrl+O")
        load_scanset_action.triggered.connect(self.load_scanset)
        self.file_menu.addAction(load_scanset_action)

        exit_action = QAction("Exit", self, shortcut="Ctrl+Q")
        exit_action.triggered.connect(self.close)
        self.file_menu.addAction(exit_action)

        self.view_menu = menu_bar.addMenu("View")
        
        new_ppi_view_action = QAction("New PPI View...", self)
        new_ppi_view_action.triggered.connect(lambda: self.create_new_dynamic_view(True, 'ppi'))
        self.view_menu.addAction(new_ppi_view_action)

        new_rhi_view_action = QAction("New RHI View...", self)
        new_rhi_view_action.triggered.connect(lambda: self.create_new_dynamic_view(True, 'rhi'))
        self.view_menu.addAction(new_rhi_view_action)

        # Sections (e.g. context_menu.addSection()) may be ignored depending on the
        # platform look and feel, so just add a disabled "action" and separator
        # to act as a label for a group of actions in the menu.
        # view_menu.addSection("Toggle Views")
        self.toggle_views_action = QAction("Toggle Views", self)
        self.toggle_views_action.setEnabled(False)
        self.view_menu.addAction(self.toggle_views_action)
        self.view_menu.addSeparator()

        # Get wild with docking
        self.setDockNestingEnabled(True)

        # Scanset Builder
        self.dockable_ssb = QDockWidget("Scan Set Builder", self)
        # self.dockable_ssb.setFloating(True) # Start as a floating window
        self.dockable_ssb.hide() # Don't show up at startup
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dockable_ssb)
        self.view_menu.addAction(self.dockable_ssb.toggleViewAction())

        self.scanset_builder = ScansetBuilder()
        self.scanset_builder.status_updated.connect(self.on_status_updated)
        self.scanset_builder.scanset_loaded.connect(self.data_manager.on_scanset_load)
        self.dockable_ssb.setWidget(self.scanset_builder)

        # Volume Slice Selector (separate but dockable dialog)
        self.dockable_vss = QDockWidget("Volume Slice Selector", self)
        self.dockable_vss.setFloating(True) # Start as a floating window
        self.dockable_vss.hide() # Don't show up at startup
        self.view_menu.addAction(self.dockable_vss.toggleViewAction())

        self.volume_slice_selector = VolumeSliceSelector()
        self.data_manager.render_volume.connect(lambda r_vol: self.volume_slice_selector.on_grid_updated(len(r_vol.elevations_rad), len(r_vol.azimuths_rad), 20, 20, 10))
        # self.volume_slice_selector.on_grid_updated(1, 1, 20, 20, 10)
        self.dockable_vss.setWidget(self.volume_slice_selector)
        
        # Timeline controls    
        self.dockable_timec = QDockWidget("Timeline Controls", self)
        self.dockable_timec.setFloating(True) # Start as a floating window
        self.dockable_timec.hide()
        self.timeline_controls = TimelineControls()
        self.timeline_controls.timeline_index_changed.connect(lambda index: self.data_manager.set_current_index(index))
        self.data_manager.num_volumes_changed.connect(self.timeline_controls.on_num_volumes_changed)
        self.dockable_timec.setWidget(self.timeline_controls)
        self.view_menu.addAction(self.dockable_timec.toggleViewAction())
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dockable_timec)

        # This is a bit of a hack to create a known position in the menu
        # before which we can insert new dynamic views.
        self.dummy_view_action = QAction("Dummy View Action", self)
        self.dummy_view_action.setEnabled(False)
        self.dummy_view_action.setVisible(False)
        self.view_menu.addAction(self.dummy_view_action)
        
        self.dynamic_views = []
        self.dynamic_view_actions = {}
        self.dynamic_view_count = 0

        # Initial PPI Canvas
        initial_ppi = self.create_new_dynamic_view(False, 'ppi')
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, initial_ppi)

        # Initial RHI Canvas
        initial_rhi = self.create_new_dynamic_view(False, 'rhi')
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, initial_rhi)

        self.happy_messages = ['Jolly good.', 'Happy hunting.', 'Best of luck.', 'I\'m rooting for you.']
        self.ready_status_widget = QLabel('Ready to rock. 🎸 v0.1')
        self.show()
        self.statusBar().addPermanentWidget(self.ready_status_widget)
        self.statusBar().showMessage(f'PAR Data Visualizer initialized! {random.choice(self.happy_messages)}')
        
    def closeEvent(self, event):
        """Ensure the viewer quits when the main window is closed. This is necessary
        because a QApplication will continue running as long as at least one
        top-level widget is still visible. This behavior is undesireable. The 
        user shouldn't have to close all windows before exiting."""
        # Signal background loading tasks to stop.
        self.data_manager.loader.stop_flag.set()
        QApplication.instance().quit()

    def create_new_dynamic_view(self, floating, slice_type):
        self.dynamic_view_count = self.dynamic_view_count + 1
        if slice_type == 'rhi':
            view_title = f'View {self.dynamic_view_count} - RHI (Z)'
        else:
            view_title = f'View {self.dynamic_view_count} - PPI (Z)'
        dock_widget = DynamicDockWidget(view_title, self)

        if floating:
            dock_widget.setFloating(floating) # Start as a floating window
            dock_widget.show()
        
        # Slice plot setup
        slice_plot = SlicePlot(self.dynamic_view_count, dock_widget, slice_type)
        dock_widget.setWidget(slice_plot.canvas.native)
        
        # Connect slots and signals

        # When the data manager requests, render a volume
        self.data_manager.render_volume.connect(slice_plot.on_radar_volume_updated)

        # When the selected RHI/PPI slices change, update the plot
        self.volume_slice_selector.selection_changed.connect(slice_plot.on_az_el_index_selection_changed)

        # When the user hovers on RHI/PPI slices, update the plot
        self.volume_slice_selector.slice_hovered.connect(slice_plot.on_az_el_slice_hovered)

        
        # View menu action management
        toggle_view_action = dock_widget.toggleViewAction()
        self.view_menu.insertAction(self.dummy_view_action, toggle_view_action)
        
        # Add an entry in the widget -> action mapping
        self.dynamic_view_actions[dock_widget] = toggle_view_action

        self.dynamic_views.append(dock_widget)
        self.statusBar().showMessage(f'{dock_widget.windowTitle()} view created.')
        return dock_widget

    def remove_dynamic_view(self, dock_widget):
        if dock_widget in self.dynamic_views:
            self.dynamic_views.remove(dock_widget)

        # Use the mapping between widget -> action to easily remove the view action
        if dock_widget in self.dynamic_view_actions:
            action = self.dynamic_view_actions.pop(dock_widget)
            self.view_menu.removeAction(action)

        self.statusBar().showMessage(f'{dock_widget.windowTitle()} view closed.')
        
    def new_scanset(self):
        self.dockable_ssb.setVisible(True)
        self.scanset = ScanSet("New scanset", base_dir=Path(os.path.expanduser("~")))
        self.scanset_builder.on_scanset_loaded(self.scanset)

    def load_scanset(self):
        (filename, selected_filter) = QFileDialog.getOpenFileName(self, "Load scanset...", os.path.expanduser("~"), "JSON files (*.json)")
        if filename:
            self.scanset = ScanSet.load_scanset(Path(filename))
            self.scanset_builder.on_scanset_loaded(self.scanset)
            self.statusBar().showMessage(f'Loaded scanset "{self.scanset.get_name()}" ✔️')

    @Slot(str)
    def on_status_updated(self, status: str):
        self.statusBar().showMessage(status)

    def on_volume_loaded(self, filename: str, r_volume: RadarVolume):
        print(f'Loaded volume {filename} {r_volume.products["Z"].shape}')

# OLD STUFF

    # def update_scan_from_index(self):
    #     if not self.scan_times:
    #         return
        
    #     # Update slider position (prevent recursive updates)
    #     self.timeline_slider.blockSignals(True)
    #     self.timeline_slider.setValue(self.current_scan_index)
    #     self.timeline_slider.blockSignals(False)

    #     # Extract and display data
    #     timestamp_str, file_path = self.scan_times[self.current_scan_index]
    #     formatted_time = self.format_timestamp(timestamp_str)
    #     self.timeline_label.setText(f"Selected Time: {formatted_time}")
    #     self.controller.mat_file_selected.emit(file_path)    

    # def format_timestamp(self, timestamp_str):
    #     try:
    #         parsed_time = datetime.strptime(timestamp_str, "%d%m%y%H%M%S")
    #         if parsed_time.year == 2007:
    #             parsed_time = parsed_time.replace(year=2024)
    #         return parsed_time.strftime("%m/%d/%Y %H:%M:%S")
    #     except ValueError:
    #         return timestamp_str

if __name__ == "__main__":
    # Solves issue with VisPy plots breaking when docks transition between floating and docked: 
    # https://github.com/vispy/vispy/issues/1759#issuecomment-724217682
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    # VisPy + PySide6 application initialization
    app = vispy.app.use_app("pyside6")
    app.create()
    window = PARDataVisualizer()
    window.show()
    sys.exit(app.run())
