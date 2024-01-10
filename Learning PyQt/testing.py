from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import sys
from pathlib import Path
from osgeo import gdal
import os
import threading

gdal.TermProgress = gdal.TermProgress_nocb


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        #Set window title
        self.setWindowTitle("MVC Pattern")
        self.setFixedSize(500, 300)

        #Set central widget
        centralWidget = QWidget(self)
        
        self.generalLayout = QGridLayout()
        centralWidget.setLayout(self.generalLayout)
        self.setCentralWidget(centralWidget)

        self._createButtons()
        self._createLabels()

    def _createButtons(self):
        self.browse_button = QPushButton("Browse File")
        self.generalLayout.addWidget(self.browse_button, 0, 1)

        self.dir_button = QPushButton("Browse directory")
        self.generalLayout.addWidget(self.dir_button, 1, 1)

        self.clear_button = QPushButton("Clear selection")
        self.generalLayout.addWidget(self.clear_button, 2, 1)

        self.start_button = QPushButton("START")
        self.generalLayout.addWidget(self.start_button, 2, 0)
    
    def _createLabels(self):
        self.inputLabel = QLineEdit("Select an input file")
        self.inputLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.generalLayout.addWidget(self.inputLabel, 0, 0)

        self.outputLabel = QLineEdit("Select an output directory")
        self.outputLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.generalLayout.addWidget(self.outputLabel, 1, 0)

    def fileDialog(self):
        filename, ok = QFileDialog.getOpenFileName(
            self,
            "Select a file",
            r"D:\SAM",
            "TIFF files (*.tif)"
        )
        if filename:
            path = Path(filename)
            self.inputLabel.setText(str(path))
    
    def directoryDialog(self):
        dir_name = QFileDialog.getExistingDirectory(self, "Select a directory", r"D:\python")
        if dir_name:
            path = Path(dir_name)
            self.outputLabel.setText(str(path))

    def clearText(self):
        self.inputLabel.setText("Select an input file")
        self.outputLabel.setText("Select an output directory")
    
    def getInput(self):
        text = self.inputLabel.text()
        return text
    
    def getOutput(self):
        text = self.outputLabel.text()
        return text
    
    def warning(self, text):
        QMessageBox.warning(
            self,
            "Warning",
            f"{text}"
        )
        
def changeExtension(input, output):
    extension = ".gpkg"
    target = None
    if input != "Select an input file" and output != "Select an output directory":
        split_path = os.path.split(input)
        split_text = os.path.splitext(split_path[1])
        new_file = split_text[0]+extension
        target = os.path.join(output, new_file)
    else:
        MainWindow().warning("Select input and output first")
    
    return target
    
def run(input, output):
    target = changeExtension(input, output)

    if target:
        translate_options = gdal.TranslateOptions(format = "GPKG", outputSRS = "EPSG:2180", callback = gdal.TermProgress)
        gdal.Translate(target, input, options = translate_options)

def runInThread(input, output):
    thread = threading.Thread(target = run, args = (input, output))
    thread.start()

class Logic:

    def __init__(self, view, thread):
        self._view = view
        self._thread = thread
        self._connectSignalsAndSlots()

    def _connectSignalsAndSlots(self):
        self._view.browse_button.clicked.connect(self._view.fileDialog)
        self._view.dir_button.clicked.connect(self._view.directoryDialog)
        self._view.clear_button.clicked.connect(self._view.clearText)
        self._view.start_button.clicked.connect(lambda: self._thread(self._view.getInput(), self._view.getOutput()))

def main():
    myApp = QApplication([])
    window = MainWindow()
    window.show()
    Logic(view = window, thread = runInThread)
    sys.exit(myApp.exec())

if __name__ == "__main__":
    main()