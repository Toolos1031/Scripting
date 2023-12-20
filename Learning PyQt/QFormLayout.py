from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import sys


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #Set window title
        self.setWindowTitle("QFormLayout")

        #Set form layout
        layout = QFormLayout()
        self.setLayout(layout)

        layout.addRow("Name:", QLineEdit())
        layout.addRow("Email:", QLineEdit())
        layout.addRow("Password:", QLineEdit(echoMode = QLineEdit.EchoMode.Password))
        layout.addRow("Confirm Password:", QLineEdit(echoMode = QLineEdit.EchoMode.Password))
        layout.addRow("Phone:", QLineEdit())

        layout.addRow(QPushButton("Sign Up"))

        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    #Create the main window
    window = MainWindow()

    #Start the event loop
    sys.exit(app.exec())