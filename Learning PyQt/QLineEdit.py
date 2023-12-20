from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
import sys


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #Set window title
        self.setWindowTitle("QLineEdit")
        self.setGeometry(100, 100, 320, 210)
        
        #Completer widget
        common_fruits = QCompleter([
            'Apple',
            'Apricot',
            'Banana',
            'Carambola',
            'Olive',
            'Oranges',
            'Papaya',
            'Peach',
            'Pineapple',
            'Pomegranate',
            'Rambutan',
            'Ramphal',
            'Raspberries',
            'Rose apple',
            'Starfruit',
            'Strawberries',
            'Water apple'
        ])

        #Create widgets
        line_edit = QLineEdit(
            self,
            clearButtonEnabled = True,
            placeholderText = "Enter something ...",
            maxLength = 30
        )

        line_read = QLineEdit(
            "Read me",
            self,
            readOnly = True
        )

        line_password = QLineEdit(
            self,
            placeholderText = "Enter password...",
            echoMode = QLineEdit.EchoMode.Password,
            clearButtonEnabled = True
        )

        line_fruits = QLineEdit(self)
        line_fruits.setCompleter(common_fruits)

        #Add the button to a vertical layout
        layout = QVBoxLayout()
        layout.addWidget(line_edit)
        layout.addWidget(line_read)
        layout.addWidget(line_password)
        layout.addWidget(line_fruits)
        self.setLayout(layout)

        #Show the window
        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    #Create the main window
    window = MainWindow()

    #Start the event loop
    sys.exit(app.exec())