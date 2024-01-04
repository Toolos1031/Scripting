from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import sys
from pathlib import Path


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #Set window title
        self.setWindowTitle("QFileDialog")
        
        #set layout
        layout = QGridLayout()
        self.setLayout(layout)

        #file selection
        file_browser_btn = QPushButton("Browse")
        file_browser_btn.clicked.connect(self.open_file_dialog)

        file_browser_btn2 = QPushButton("Browse 2")
        file_browser_btn2.clicked.connect(self.open_file_dialog2)
        
        dir_browser_btn = QPushButton("Browse directory")
        dir_browser_btn.clicked.connect(self.open_directory)

        self.file_list = QListWidget(self)
        self.single_file_list = QLineEdit(self)
        self.dir_list = QLineEdit(self)

        layout.addWidget(QLabel("Files:"), 0, 0)
        layout.addWidget(self.file_list, 1, 0)
        layout.addWidget(file_browser_btn, 2, 0)
        layout.addWidget(QLabel("File:"), 3, 0)
        layout.addWidget(self.single_file_list, 3, 1)
        layout.addWidget(file_browser_btn2, 3, 2)
        layout.addWidget(QLabel("Directory:"), 4, 0)
        layout.addWidget(self.dir_list, 4, 1)
        layout.addWidget(dir_browser_btn, 4, 2)

        self.show()

    def open_directory(self):
        dir_name = QFileDialog.getExistingDirectory(self, "Select a directory")
        if dir_name:
            path = Path(dir_name)
            self.dir_list.setText(str(path))

    def open_file_dialog2(self):
        filename, ok = QFileDialog.getOpenFileName(
            self,
            "Select a file",
            r"D:\Spychowo",
            "Images (*.png *.jpg)"
        )
        if filename:
            path = Path(filename)
            self.single_file_list.setText(str(path))

    def open_file_dialog(self):
        dialog = QFileDialog(self)
        dialog.setDirectory(r"D:\Python")
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        dialog.setNameFilter("Images (*.png *.jpg)")
        dialog.setViewMode(QFileDialog.ViewMode.List)
        if dialog.exec():
            filenames = dialog.selectedFiles()
            if filenames:
                self.file_list.addItems([str(Path(filename)) for filename in filenames])
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    #Create the main window
    window = MainWindow()

    #Start the event loop
    sys.exit(app.exec())