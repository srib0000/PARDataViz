from PySide6.QtWidgets import QDockWidget, QMenu
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

class DynamicDockWidget(QDockWidget):
    """A dockable widget which removes itself from its parent's list of widgets."""
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.parent = parent

    def clean_up(self):
        """Disconnect signals and perform cleanup."""
        self.setParent(None)
        self.parent = None
        # Ensure child widgets are deleted
        self.widget().deleteLater()

    def closeEvent(self, event):
        """Handle close events by removing the dock widget from the parent's list."""
        if self.parent:
            self.parent.remove_dynamic_view(self)
        self.clean_up()
        super().closeEvent(event)

    def __del__(self):
        print(f'Dynamic view docking widget destroyed.')
        # super().__del__(self)