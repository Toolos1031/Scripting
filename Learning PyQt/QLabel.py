from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap
import sys


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #Set window title
        self.setWindowTitle("QLabel")
        #self.setGeometry(100, 100, 320, 210)
        
        #Create widgets
        label = QLabel()
        label.setText("This is QLabel widget")

        display_label = QLabel()
        pixmap = QPixmap("1.png")
        display_label.setPixmap(pixmap)

        button = QPushButton("Clear")
        button.clicked.connect(label.clear)

        color_label = QLabel()
        color_label.setStyleSheet("QLabel{background-color:red}")

        #Add the button to a vertical layout
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(button)
        layout.addWidget(display_label)
        layout.addWidget(color_label)
        self.setLayout(layout)

        #Show the window
        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    #Create the main window
    window = MainWindow()

    #Start the event loop
    sys.exit(app.exec())