from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import sys

from form import Ui_MainWindow

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

app = QApplication([])
window = MainWindow()
window.show()
app.exec()