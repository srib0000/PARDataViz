from PySide6.QtWidgets import QApplication, QWidget, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsTextItem, QLabel, QVBoxLayout, QLineEdit, QCheckBox, QFormLayout
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QDoubleValidator, QIntValidator

class PolarTransformEditor(QWidget):
    """
    This class was helpful when figuring out the transformation of the data into a
    polar plot in VisPy.
    """

    # Define a signal that will be emitted when any transformation is updated
    transform_updated = Signal(float, float, int, int, int, float, int)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Set up the layout
        self.layout = QVBoxLayout(self)
        
        # Create form layout to contain the input fields
        self.form_layout = QFormLayout()

        # Define the input fields for each attribute
        self.scale_x_input = QLineEdit(self)
        self.scale_x_input.setText("1")
        self.scale_x_input.setValidator(QDoubleValidator())  # Ensure input is a number
        self.scale_x_input.textChanged.connect(self.on_transform_changed)
        
        self.scale_y_input = QLineEdit(self)
        self.scale_y_input.setText("1")
        self.scale_y_input.setValidator(QDoubleValidator())  # Ensure input is a number
        self.scale_y_input.textChanged.connect(self.on_transform_changed)
        
        self.x_offset_input = QLineEdit(self)
        self.x_offset_input.setText("0")
        self.x_offset_input.setValidator(QIntValidator())  # Ensure input is an integer
        self.x_offset_input.textChanged.connect(self.on_transform_changed)
        
        self.y_offset_input = QLineEdit(self)
        self.y_offset_input.setText("0")
        self.y_offset_input.setValidator(QIntValidator())  # Ensure input is an integer
        self.y_offset_input.textChanged.connect(self.on_transform_changed)

        self.origin_from_bottom_input = QCheckBox("Origin from bottom", self)
        self.origin_from_bottom_input.toggled.connect(self.on_transform_changed)
        
        self.zero_loc_input = QLineEdit(self)
        self.zero_loc_input.setText("0")
        self.zero_loc_input.setValidator(QDoubleValidator())  # Ensure input is a number
        self.zero_loc_input.textChanged.connect(self.on_transform_changed)
        
        self.direction_input = QLineEdit(self)
        self.direction_input.setText("1")
        self.direction_input.setValidator(QIntValidator())  # Ensure input is an integer
        self.direction_input.textChanged.connect(self.on_transform_changed)

        # Add the input fields to the form layout
        self.form_layout.addRow("Scale X", self.scale_x_input)
        self.form_layout.addRow("Scale Y", self.scale_y_input)
        self.form_layout.addRow("X Offset", self.x_offset_input)
        self.form_layout.addRow("Y Offset", self.y_offset_input)
        self.form_layout.addRow(self.origin_from_bottom_input)
        self.form_layout.addRow("Zero Location", self.zero_loc_input)
        self.form_layout.addRow("Direction", self.direction_input)

        # Add the form layout to the main layout
        self.layout.addLayout(self.form_layout)

    def safe_get_float(self, text, default=0.0):
        try:
            return float(text)
        except ValueError:
            return default

    def safe_get_int(self, text, default=0):
        try:
            return int(text)
        except ValueError:
            return default

    @Slot()
    def on_transform_changed(self):
        # Get the current values from the input fields
        scale_x = self.safe_get_float(self.scale_x_input.text(), default=0.0)
        scale_y = self.safe_get_float(self.scale_y_input.text(), default=0.0)
        x_offset = self.safe_get_int(self.x_offset_input.text(), default=0)
        y_offset = self.safe_get_int(self.y_offset_input.text(), default=0)
        origin_from_bottom = 1 if self.origin_from_bottom_input.isChecked() else 0
        zero_loc = self.safe_get_float(self.zero_loc_input.text(), default=0.0)
        direction = self.safe_get_int(self.direction_input.text(), default=1)

        # Emit the signal with all the current transform values
        self.transform_updated.emit(scale_x, scale_y, x_offset, y_offset, origin_from_bottom, zero_loc, direction)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    widget = PolarTransformEditor()
    widget.setWindowTitle("Polar Transform Editor")

# Connect the signal to a slot to print all transform values when it's emitted
    def on_transform_updated(scale_x, scale_y, x_offset, y_offset, origin_from_bottom, zero_loc, direction):
        print(f"Transform updated: Scale X={scale_x}, Scale Y={scale_y}, X Offset={x_offset}, Y Offset={y_offset}, "
              f"Origin From Bottom={origin_from_bottom}, Zero Location={zero_loc}, Direction={direction}")


    widget.transform_updated.connect(on_transform_updated)

    widget.show()
    sys.exit(app.exec())
