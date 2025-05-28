import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFileDialog, QFrame, QSizePolicy
from PySide6.QtCore import Slot, Signal
from scan_set import ScanSet
from scans_list_editor import ScansListEditor
from scan_file_list_editor import ScanFileListEditor

class ScansetBuilder(QWidget):
    """
    """
    status_updated = Signal(str)
    scanset_loaded = Signal(ScanSet)

    def __init__(self):
        super().__init__()
        
        self.last_selected_base_dir = os.path.expanduser("~")

        self.scanset = ScanSet("Default Scanset", Path(self.last_selected_base_dir))

        main_layout = QVBoxLayout()
        
        # Label for scanset name editor field
        self.scanset_name_editor_label = QLabel("Scanset Name:")
        main_layout.addWidget(self.scanset_name_editor_label)

        # Scanset name editor field
        self.scanset_name_editor = QLineEdit()
        self.scanset_name_editor.setPlaceholderText("Enter a name for the scanset...")
        self.scanset_name_editor.setText(self.scanset.get_name())
        self.scanset_name_editor.textChanged.connect(self.scanset_editor_text_changed)
        main_layout.addWidget(self.scanset_name_editor)

        # Label for scanset directory
        self.scanset_dir_label = QLabel("Base directory:")
        main_layout.addWidget(self.scanset_dir_label)

        # Scanset dir editor field
        base_dir_layout = QHBoxLayout()
        self.scanset_dir_editor = QLineEdit()
        self.scanset_dir_editor.setPlaceholderText("Base directory for the scanset...")
        self.scanset_dir_editor.setText(self.scanset.get_base_dir().__str__())
        self.scanset_dir_editor.textChanged.connect(self.scanset_editor_basedir_text_changed)
        self.scanset_dir_editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        base_dir_layout.addWidget(self.scanset_dir_editor)

        self.scanset_dir_browse_button = QPushButton("Browse...")
        self.scanset_dir_browse_button.clicked.connect(self.scanset_editor_base_dir_browse_clicked)
        base_dir_layout.addWidget(self.scanset_dir_browse_button)
        main_layout.addLayout(base_dir_layout)

        # Scans list editor
        self.scans_list_editor = ScansListEditor()
        self.scans_list_editor.status_updated.connect(self.on_status_updated)
        main_layout.addWidget(self.scans_list_editor)

        self.scan_hrule = QFrame()
        self.scan_hrule.setFrameShape(QFrame.Shape.HLine)
        self.scan_hrule.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(self.scan_hrule)

        # Scan file list editor
        self.scan_file_list_editor = ScanFileListEditor()
        self.scans_list_editor.selected_scan_changed.connect(self.scan_file_list_editor.on_selected_scan_changed)
        self.scan_file_list_editor.scan_name_changed.connect(self.scans_list_editor.on_scan_name_changed)
        self.scan_file_list_editor.status_updated.connect(self.on_status_updated)
        main_layout.addWidget(self.scan_file_list_editor)

        self.scan_hrule2 = QFrame()
        self.scan_hrule2.setFrameShape(QFrame.Shape.HLine)
        self.scan_hrule2.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(self.scan_hrule)
        
        self.h_layout3 = QHBoxLayout()
        self.save_scanset_button = QPushButton("Save scanset...")
        self.save_scanset_button.clicked.connect(self.save_scanset_button_clicked)
        self.h_layout3.addWidget(self.save_scanset_button)
        # layout.addWidget(self.save_scanset_button)

        self.load_scanset_button = QPushButton("Load scanset...")
        self.load_scanset_button.clicked.connect(self.load_scanset_button_clicked)
        self.h_layout3.addWidget(self.load_scanset_button)
        # layout.addWidget(self.load_scanset_button)
        main_layout.addLayout(self.h_layout3)

        # Signal child components to update themselves after initialization
        self.scans_list_editor.on_new_scanset(self.scanset)
        self.scan_file_list_editor.on_new_scanset(self.scanset)
        
        self.setLayout(main_layout)

    def on_status_updated(self, str):
        self.status_updated.emit(str)

    def scanset_editor_text_changed(self, text):
        # Programmatic change of the text
        self.scanset.set_name(text)

    def scanset_editor_basedir_text_changed(self, text):
        self.scanset.set_base_dir(Path(text))

    def scanset_editor_base_dir_browse_clicked(self):
        dir = QFileDialog.getExistingDirectory(self, "Select Scanset Base Folder...", self.last_selected_base_dir)
        if dir:
            self.last_selected_base_dir = dir
            self.scanset.set_base_dir(dir)
            self.scanset_dir_editor.setText(dir)

    def save_scanset_button_clicked(self):
        (filename, selected_filter) = QFileDialog.getSaveFileName(self, "Save scanset...", os.path.expanduser("~"), "JSON files (*.json)")
        if filename:
            scanset_path = Path(filename)
            ScanSet.dump_scanset(scanset_path, self.scanset)

    def load_scanset_button_clicked(self):
        (filename, selected_filter) = QFileDialog.getOpenFileName(self, "Load scanset...", os.path.expanduser("~"), "JSON files (*.json)")
        if filename:
            scanset_path = Path(filename)
            scanset = ScanSet.load_scanset(scanset_path)
            self.on_scanset_loaded(scanset)

    @Slot(ScanSet)
    def on_scanset_loaded(self, scanset: ScanSet):
        self.scanset = scanset
        self.scanset_name_editor.setText(self.scanset.get_name())
        self.scanset_dir_editor.setText(self.scanset.get_base_dir().__str__())

        self.scans_list_editor.on_new_scanset(self.scanset)
        self.scan_file_list_editor.on_new_scanset(self.scanset)
        
        self.scanset_loaded.emit(self.scanset)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScansetBuilder()
    window.setWindowTitle("Test Scanset Builder")

    def on_status(msg):
        print(msg)

    window.status_updated.connect(on_status)

    window.show()
    sys.exit(app.exec())