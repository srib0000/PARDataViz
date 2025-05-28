import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QHBoxLayout, QPushButton, QListWidgetItem
from PySide6.QtCore import Signal, Slot
from scan_set import ScanSet
from scan import Scan

class ScansListEditor(QWidget):
    """
    """
    status_updated = Signal(str)
    selected_scan_changed = Signal(Scan)

    def __init__(self):
        super().__init__()

        self.main_layout = QVBoxLayout(self)

        self.scan_count = 0

         # List of scans in this scanset
        self.scanset_scanslist_label = QLabel("Scans:")
        self.main_layout.addWidget(self.scanset_scanslist_label)

        self.scans_list = QListWidget()
        self.scans_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.scans_list.itemSelectionChanged.connect(self.scan_selected)
        self.main_layout.addWidget(self.scans_list)

        self.horizb_layout = QHBoxLayout()

        self.add_scan_button = QPushButton("Add Scan")
        self.add_scan_button.clicked.connect(self.on_add_scan_clicked)
        self.horizb_layout.addWidget(self.add_scan_button)

        self.remove_scan_button = QPushButton("Remove Scan")
        self.remove_scan_button.clicked.connect(self.on_remove_scan_clicked)
        self.horizb_layout.addWidget(self.remove_scan_button)
        self.main_layout.addLayout(self.horizb_layout)

    @Slot(ScanSet)
    def on_new_scanset(self, scanset: ScanSet):
        self.scanset = scanset
        self.scan_count = len(scanset.get_scans())

        # Clear the scan list and populate it with the new scanset's scans (if any).
        self.scans_list.clear()
        for scan in scanset.get_scans():
            self.scans_list.addItem(scan.get_name())

    def scan_selected(self):
        (scan, _) = self.find_selected_scan()
        if scan is not None:
            # Update internal state and emit signals
            self.status_updated.emit(f'Scan selected: "{scan.get_name()}"')
            self.selected_scan_changed.emit(scan)
            
    
    def find_selected_scan(self) -> tuple[Scan, QListWidgetItem] | None:
        if len(self.scans_list.selectedItems()) > 0:
            scan_name = self.scans_list.selectedItems()[0].text()
            
            # Find the selection in the scanset.
            matches = [scan for scan in self.scanset.get_scans() if scan.get_name() == scan_name]

            # Get the first matching scan
            if len(matches) > 0:
                return (matches[0], self.scans_list.selectedItems()[0])
            
            # Found a QListWidgetItem but no matching scan...
            return (None, self.scans_list.selectedItems()[0])

        # Didn't find anything!
        return (None, None)

    @Slot()
    def on_add_scan_clicked(self):
        # Create a new name for a scan.
        self.scan_count = self.scan_count + 1
        scan_name = f'Scan {self.scan_count}'

        # Add a new scan to the scanset and to the scan list UI.
        self.scanset.add_scan(Scan(name=scan_name))
        self.scans_list.addItem(scan_name)

        self.status_updated.emit(f'Created scan: "{scan_name}"')

    def on_remove_scan_clicked(self):
        (scan, item) = self.find_selected_scan()
        if scan is not None:
            # Remove the scan from the scanset
            self.scanset.remove_scan(scan)

            # Update internal state and emit status
            self.status_updated.emit(f'Removed scan: "{scan.get_name()}"')

        if item is not None:
            # Remove it from the scans list
            self.scans_list.clearSelection()
            self.scans_list.takeItem(self.scans_list.row(item))
        
        # The QListWidget doesn't trigger an empty selection, so let everyone know we're out of scans.
        if len(self.scanset.get_scans()) == 0:
            self.selected_scan_changed.emit(None)

    @Slot(str)
    def on_scan_name_changed(self, scan_name: str):
        (scan, item) = self.find_selected_scan()

        if scan is not None:
            scan.set_name(scan_name)
        
        if item is not None:
            item.setText(scan_name)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from pathlib import Path
    import os

    app = QApplication(sys.argv)
    window = ScansListEditor()
    
    window.on_new_scanset(ScanSet(name="Test ScanSet", base_dir=Path(os.path.expanduser("~"))))
    
    def on_status(msg):
        print(msg)
    
    window.status_updated.connect(on_status)
    window.setWindowTitle("Scans List Editor")
    window.show()
    sys.exit(app.exec())