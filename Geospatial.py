from PyQt6.QtWidgets import *
import sys


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #Set window title
        self.setWindowTitle("Signals And Slots")

        #Create a button and connect it to a method
        button = QPushButton("click me")
        button.clicked.connect(self.button_clicked)

        #Add the button to a vertical layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(button)

        #Show the window
        self.show()

    def button_clicked(self):
        print("clicked")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    #Create the main window
    window = MainWindow()

    #Start the event loop
    sys.exit(app.exec())