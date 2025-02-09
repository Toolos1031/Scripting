from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import sys


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #Set window title
        self.setWindowTitle("QMessageBox")
        
        #set layout
        layout = QHBoxLayout()
        self.setLayout(layout)

        #Widgets
        
        btn_question = QPushButton("Question")
        btn_question.clicked.connect(self.question)

        btn_information = QPushButton("Information")
        btn_information.clicked.connect(self.information)

        btn_warning = QPushButton("Warning")
        btn_warning.clicked.connect(self.warning)

        btn_critical = QPushButton("Critical")
        btn_critical.clicked.connect(self.critical)

        layout.addWidget(btn_question)
        layout.addWidget(btn_information)
        layout.addWidget(btn_warning)
        layout.addWidget(btn_critical)

        self.show()

    def information(self):
        QMessageBox.information(
            self,
            "Information",
            "This is an important information"
        )

    def warning(self):
        QMessageBox.warning(
            self,
            "Warning",
            "This is a warning message"
        )

    def question(self):
        answer = QMessageBox.question(
            self,
            "Confirmation",
            "Do you want to quit?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )

        if answer == QMessageBox.StandardButton.Yes:
                QMessageBox.information(
                    self,
                    'Information',
                    'You selected Yes. The program will be terminated.',
                    QMessageBox.StandardButton.Ok
                )
                self.close()
        else:
            QMessageBox.information(
                self,
                'Information',
                'You selected No.',
                QMessageBox.StandardButton.Ok
            )

    def critical(self):
        QMessageBox.critical(
            self,
            "Critical",
            "This is a critical message"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    #Create the main window
    window = MainWindow()

    #Start the event loop
    sys.exit(app.exec())