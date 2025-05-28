import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QListWidget, QHBoxLayout, QPushButton, QFileDialog
from PySide6.QtCore import Signal, Slot
from scan_set import ScanSet
from scan import Scan
from pathlib import Path

class ScanFileListEditor(QWidget):
    """
    """
    status_updated = Signal(str)
    scan_files_added = Signal(int)
    scan_name_changed = Signal(str)

    def __init__(self):
        super().__init__()

        self.main_layout = QVBoxLayout(self)

        self.scan_label_placeholder_text = 'Select a scan to edit'
        self.scan_label = QLabel(self.scan_label_placeholder_text)
        self.scan_label.setEnabled(False)
        self.main_layout.addWidget(self.scan_label)

        self.scan_name_editor = QLineEdit()
        self.scan_name_editor.setEnabled(False)
        self.scan_name_editor.textEdited.connect(self.on_scan_name_changed)
        self.main_layout.addWidget(self.scan_name_editor)

        self.scan_files_list = QListWidget()
        self.scan_files_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.scan_files_list.setEnabled(False)
        self.main_layout.addWidget(self.scan_files_list)

        self.h_layout2 = QHBoxLayout()
        self.add_files_button = QPushButton("Add files...")
        self.add_files_button.setEnabled(False)
        self.add_files_button.clicked.connect(self.add_scan_files_clicked)
        self.h_layout2.addWidget(self.add_files_button)

        self.remove_files_button = QPushButton("Remove selected files")
        self.remove_files_button.setEnabled(False)
        self.remove_files_button.clicked.connect(self.remove_scan_files_clicked)
        self.h_layout2.addWidget(self.remove_files_button)
        self.main_layout.addLayout(self.h_layout2)
        
    def on_scan_name_changed(self, new_name):
        # Eject early if the name matches an existing name
        if len([scan for scan in self.scanset.get_scans() if scan.get_name() == new_name]) > 0:
            self.scan_name_editor.setStyleSheet("border: 2px solid red;")
            return
        self.scan_name_editor.setStyleSheet("")

        if self.selected_scan is not None:
            self.scan_label.setText(f'Editing scan, "{new_name}"')
            self.scan_name_changed.emit(new_name)

    def add_scan_files_clicked(self):
        if self.selected_scan is not None:
            (filenames, selected_filter) = QFileDialog.getOpenFileNames(self, "Select Scan Files...", self.scanset.get_base_dir().__str__(), filter="MATLAB files (*.mat)")
            for filename in filenames:
                rel_filename = (Path(filename).relative_to(self.scanset.get_base_dir()).__str__())
                self.selected_scan.get_scan_files().append(rel_filename)
                self.scan_files_list.addItem(rel_filename)
            self.status_updated.emit(f'Added {len(filenames)} files to {self.selected_scan.get_name()}.')

    def remove_scan_files_clicked(self):
        removals = []
        for item in self.scan_files_list.selectedItems():
            # print(item.text())
            removals.append((next(file for file in self.selected_scan.get_scan_files() if file == item.text()), item))
        
        for file, item in removals:
            self.selected_scan.get_scan_files().remove(file)
            self.scan_files_list.takeItem(self.scan_files_list.row(item))
        self.status_updated.emit(f'Removed {len(removals)} files from {self.selected_scan.get_name()}.')

    @Slot(ScanSet)
    def on_new_scanset(self, scanset: ScanSet):
        self.scanset = scanset
        self.reset()

    @Slot(Scan)
    def on_selected_scan_changed(self, scan: Scan):
        if scan is not None:
            self.selected_scan = scan
            self.scan_label.setText(f'Editing scan, "{scan.get_name()}"')
            self.scan_label.setEnabled(True)

            self.scan_name_editor.setText(scan.get_name())
            self.scan_name_editor.setEnabled(True)
            
            self.scan_files_list.clear()
            for filename in scan.get_scan_files():
                self.scan_files_list.addItem(filename)
            self.scan_files_list.setEnabled(True)
            
            self.add_files_button.setEnabled(True)
            self.remove_files_button.setEnabled(True)
        else:
            self.reset()

    def reset(self):
        self.scan_label.setEnabled(False)
        self.scan_label.setText(self.scan_label_placeholder_text)
        self.scan_name_editor.setEnabled(False)
        self.scan_name_editor.clear()
        self.scan_files_list.setEnabled(False)
        self.scan_files_list.clearSelection()
        self.scan_files_list.clear()
        self.add_files_button.setEnabled(False)
        self.remove_files_button.setEnabled(False)
        self.selected_scan = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScanFileListEditor()
    window.setWindowTitle("Scan File List Editor")
    window.show()
    sys.exit(app.exec())