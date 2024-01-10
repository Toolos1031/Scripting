import sys
import time
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel
 
class Worker(QThread):
 
    # signal to indicate that the thread has finished
    finished = pyqtSignal()
 
    # signal to indicate the progress of the task
    progress = pyqtSignal(int)
    def __init__(self):
        super().__init__()
 
    def run(self):
        for i in range(101):
 
            # Simulate time consuming task
            time.sleep(0.1)
 
            # this emit  progress signal
            self.progress.emit(i)
 
        # Emit  finished signal when the task is complet
        self.finished.emit()
 
 
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GeeksCoders")
 
        self.label = QLabel("Click the button to start the task", self)
        self.label.move(50, 50)
 
        self.button = QPushButton("Start", self)
        self.button.move(50, 100)
        self.button.clicked.connect(self.start_task)
 
        self.show()
 
    def start_task(self):
 
        # Disable the button
        self.button.setEnabled(False)
 
        # Create a worker thread
        self.worker = Worker()
 
        # Connect the progress signal
        self.worker.progress.connect(self.update_progress)
 
        # Connect the finished signal
        self.worker.finished.connect(self.task_complete)
 
        # Start the thread
        self.worker.start()
 
    def update_progress(self, value):
        # Update the label text
        self.label.setText(f"Task in progress: {value}%")
 
    def task_complete(self):
        # Update the label text
        self.label.setText("Task complete")
 
        # Enable the button
        self.button.setEnabled(True)
 
 
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())