from PySide6.QtWidgets import QApplication, QWidget, QSlider, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QSize, Slot, Signal, QTimer
from PySide6.QtGui import QIcon

class TimelineControls(QWidget):
    timeline_index_changed = Signal(int)

    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout(self)
        self.timeline_button_layout = QHBoxLayout()
        
        # Add a vertical spacer to push content to the bottom
        # self.main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Timeline controls
        self.back_button = QPushButton()
        self.back_button.setIcon(QIcon.fromTheme("media-skip-backward"))
        self.back_button.clicked.connect(self.on_back_button_pressed)
        self.timeline_button_layout.addWidget(self.back_button)

        self.play_button = QPushButton()
        self.play_button.setIcon(QIcon.fromTheme("media-playback-start"))
        self.play_button.clicked.connect(self.toggle_play_pause)
        self.timeline_button_layout.addWidget(self.play_button)

        self.forward_button = QPushButton()
        self.forward_button.setIcon(QIcon.fromTheme("media-skip-forward"))
        self.forward_button.clicked.connect(self.on_forward_button_pressed)
        self.timeline_button_layout.addWidget(self.forward_button)

        self.timeline_button_layout.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        # Timeline slider
        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setRange(0, 100)  # Initial range for testing
        self.timeline_slider.setSingleStep(1)
        self.timeline_slider.setPageStep(1)
        self.timeline_slider.valueChanged.connect(self.timeline_index_changed)
        self.timeline_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.timeline_slider.setTickInterval(1)
        self.timeline_slider.setTracking(False) # Don't emit an updated value until the user stops dragging the slider.
        # self.timeline_slider.setEnabled(False)  # Disabled until data is loaded

        # Add the slider to the timeline layout
        self.timeline_button_layout.addWidget(self.timeline_slider)
        self.main_layout.addLayout(self.timeline_button_layout)

        self.timeline_label = QLabel("Selected Time:")
        self.main_layout.addWidget(self.timeline_label)

        # Set up the timer
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.on_forward_button_pressed)
    
    @Slot()
    def on_forward_button_pressed(self):
        current_val = self.timeline_slider.value()
        new_val = current_val + 1
        if new_val <= self.timeline_slider.maximum():
            self.timeline_slider.setValue(new_val)
        else:
            self.timeline_slider.setValue(0)
        
    @Slot()
    def on_back_button_pressed(self):
        current_val = self.timeline_slider.value()
        new_val = current_val - 1
        if 0 <= new_val:
            self.timeline_slider.setValue(new_val)
        else:
            self.timeline_slider.setValue(self.timeline_slider.maximum())

    @Slot(int)
    def on_num_volumes_changed(self, num_vols: int):
        self.timeline_slider.setValue(0)
        self.scan_times = num_vols
        print(f"Timeline Slider Updated Range: [{0}, {num_vols})")
        self.timeline_slider.setRange(0, num_vols - 1)

    def toggle_play_pause(self):
        if self.timer.isActive():
            self.timer.stop()
            self.play_button.setIcon(QIcon.fromTheme("media-playback-start")) 
        else:
            self.timer.start(1000)  # Start timer with 1-second intervals
            self.play_button.setIcon(QIcon.fromTheme("media-playback-pause"))  

def main():
    """Test the TimelineControls widget."""
    import sys
    app = QApplication(sys.argv)

    timeline_controls = TimelineControls()    
    timeline_controls.setWindowTitle("TimelineControls Test")
    timeline_controls.resize(800, 100)
    timeline_controls.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()