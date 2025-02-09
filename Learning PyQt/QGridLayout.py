from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import sys


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #Set window title
        self.setWindowTitle("QGridLayout")

        #Set grid layout
        layout = QGridLayout()
        self.setLayout(layout)

        #username
        layout.addWidget(QLabel("Username"), 0, 0)
        layout.addWidget(QLineEdit(), 0, 1)

        #password
        layout.addWidget(QLabel("Password"), 1, 0)
        layout.addWidget(QLineEdit(echoMode = QLineEdit.EchoMode.Password), 1, 1)

        #buttons
        layout.addWidget(QPushButton("Log in"), 2, 0, alignment = Qt.AlignmentFlag.AlignRight)
        layout.addWidget(QPushButton("Close"), 2, 1, alignment = Qt.AlignmentFlag.AlignRight)

        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    #Create the main window
    window = MainWindow()

    #Start the event loop
    sys.exit(app.exec())