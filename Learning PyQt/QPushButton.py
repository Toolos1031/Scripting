from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
import sys


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #Set window title
        self.setWindowTitle("QPushButton")
        self.setGeometry(100, 100, 320, 210)
        
        #Create widgets
        button = QPushButton("Click me")

        button_del = QPushButton("Delete")
        button_del.setIcon(QIcon("trash.png"))
        button_del.setFixedSize(QSize(100, 30))

        button_toggle = QPushButton("Toggle me")
        button_toggle.setCheckable(True)
        button_toggle.clicked.connect(self.on_toggle)

        #Add the button to a vertical layout
        layout = QVBoxLayout()
        layout.addWidget(button)
        layout.addWidget(button_del)
        layout.addWidget(button_toggle)
        self.setLayout(layout)

        #Show the window
        self.show()
    
    def on_toggle(self, checked):
        print(checked)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    #Create the main window
    window = MainWindow()

    #Start the event loop
    sys.exit(app.exec())