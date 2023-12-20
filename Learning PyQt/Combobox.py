from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import sys


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #Set window title
        self.setWindowTitle("Combobox")
        
        #set layout
        layout = QGridLayout()
        self.setLayout(layout)

        #Widgets
        label = QLabel("Choose a platform", self)
        
        self.combobox = QComboBox(self)
        self.combobox.addItem("Android")
        self.combobox.addItem("IOS")
        self.combobox.addItem("Windows")

        self.combobox.activated.connect(self.update)
        
        self.decision_label = QLabel("", self)

        layout.addWidget(label)
        layout.addWidget(self.combobox)
        layout.addWidget(self.decision_label)

        self.show()

    def update(self):
        self.decision_label.setText(
            f"You selected {self.combobox.currentText()}"
        )



if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    #Create the main window
    window = MainWindow()

    #Start the event loop
    sys.exit(app.exec())