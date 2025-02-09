from PyQt6.QtWidgets import *
import sys


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #Set window title
        self.setWindowTitle("Signals And Slots")

        #Create widgets
        label = QLabel("Start")
        line_edit = QLineEdit()
        line_edit.textChanged.connect(label.setText)

        #Add the button to a vertical layout
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(line_edit)
        self.setLayout(layout)

        #Show the window
        self.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    #Create the main window
    window = MainWindow()

    #Start the event loop
    sys.exit(app.exec())