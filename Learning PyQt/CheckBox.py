from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import sys


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #Set window title
        self.setWindowTitle("Checkbox")
        
        #set layout
        layout = QGridLayout()
        self.setLayout(layout)

        #checkbox
        self.checkbox = QCheckBox("I agree", self)
        
        #buttons
        check_button = QPushButton("Check")
        check_button.clicked.connect(self.check)

        uncheck_button = QPushButton("Uncheck")
        uncheck_button.clicked.connect(self.uncheck)
        
        #layout
        layout.addWidget(self.checkbox, 0, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(check_button, 1, 0)
        layout.addWidget(uncheck_button, 1, 1)

        self.show()

    def check(self):
        self.checkbox.setChecked(True)
    
    def uncheck(self):
        self.checkbox.setChecked(False)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    #Create the main window
    window = MainWindow()

    #Start the event loop
    sys.exit(app.exec())