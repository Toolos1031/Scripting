from PyQt6.QtWidgets import *
import sys


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #Set window title
        self.setWindowTitle("QHBoxLayout")
        self.setGeometry(100, 100, 1000, 100)

        #Add to a layout
        layout1 = QHBoxLayout()
        layout2 = QHBoxLayout()
        layout3 = QHBoxLayout()
        layout4 = QHBoxLayout()
        layout5 = QHBoxLayout()
        layout_main = QVBoxLayout()
        layout_main.addLayout(layout1)
        layout_main.addLayout(layout2)
        layout_main.addLayout(layout3)
        layout_main.addLayout(layout4)
        layout_main.addLayout(layout5)
        self.setLayout(layout_main)

        #add spacer to align right
        layout1.addStretch()


        #Create buttons and add them to the layout
        label1 = QLabel("Align right with spacer")
        layout1.addWidget(label1)
        titles = ["yes", "no", "Cancel"]

        for title in titles:
            button = QPushButton(title)
            layout1.addWidget(button)


        #Create buttons with a spacer in between
        label2 = QLabel("Spacer in between")
        layout2.addWidget(label2)
        buttons = [QPushButton(title) for title in titles]
        
        layout2.addWidget(buttons[0])
        layout2.addWidget(buttons[1])

        layout2.addStretch()

        layout2.addWidget(buttons[2])


        #third layout for stretching
        label3 = QLabel("Stretching")
        layout3.addWidget(label3)
        buttons1 = [QPushButton(title) for title in titles]
        for button in buttons1:
            layout3.addWidget(button)

        #set stretch factor
        layout3.setStretchFactor(buttons1[0], 2)
        layout3.setStretchFactor(buttons1[1], 2)
        layout3.setStretchFactor(buttons1[2], 1)


        #fourth layout for spacing
        label4 = QLabel("Spacing")
        layout4.addWidget(label4)
        buttons2 = [QPushButton(title) for title in titles]
        for button in buttons2:
            layout4.addWidget(button)
        
        layout4.setSpacing(50)


        #fifth layout for margins
        label5 = QLabel("Margins")
        layout5.addWidget(label5)
        buttons3 = [QPushButton(title) for title in titles]
        for button in buttons3:
            layout5.addWidget(button)

        layout5.setContentsMargins(50, 50, 50, 50)
        #Show the window
        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    #Create the main window
    window = MainWindow()

    #Start the event loop
    sys.exit(app.exec())