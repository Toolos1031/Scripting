import Metashape
from PySide2 import QtGui, QtCore, QtWidgets
import os

class Dialog(QtWidgets.QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.resize(500, self.height())

        self.setWindowTitle("Orthomosaics from Point Clouds")

        self.lasFolderLabel = QtWidgets.QLabel("Path to scan folder")
        self.photoFolderLabel = QtWidgets.QLabel("Path to photos folder")
        self.outputFolderLabel = QtWidgets.QLabel("Path to output folder")
        self.lasFolderLineEdit = QtWidgets.QLineEdit("D:/WODY_testy/agi_test/las")
        self.photoFolderLineEdit = QtWidgets.QLineEdit("D:/WODY_testy/agi_test/photo")
        self.outputFolderLineEdit = QtWidgets.QLineEdit("D:/WODY_testy/agi_test/out")
        self.lasButton = QtWidgets.QPushButton("Select scans")
        self.photoButton = QtWidgets.QPushButton("Select photos")
        self.outButton = QtWidgets.QPushButton("Select output")

        self.lasButton.clicked.connect(lambda: self.openDirectory(self.lasFolderLineEdit))
        self.photoButton.clicked.connect(lambda: self.openDirectory(self.photoFolderLineEdit))
        self.outButton.clicked.connect(lambda: self.openDirectory(self.outputFolderLineEdit))

        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.setCenterButtons(True)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.lasFolderLabel, 0, 0)
        layout.addWidget(self.lasFolderLineEdit, 0, 1)
        layout.addWidget(self.photoFolderLabel, 1, 0)
        layout.addWidget(self.photoFolderLineEdit, 1, 1)
        layout.addWidget(self.outputFolderLabel, 2, 0)
        layout.addWidget(self.outputFolderLineEdit, 2, 1)
        layout.addWidget(self.lasButton, 0, 3)
        layout.addWidget(self.photoButton, 1, 3)
        layout.addWidget(self.outButton, 2, 3)
        layout.addWidget(self.buttonBox, 3, 1)
        layout.addWidget(self.outButton)
        self.setLayout(layout)

        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self, QtCore.SLOT("accept()"))
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), self, QtCore.SLOT("reject()"))

    def openDirectory(self, line_edit):
        self.folderPath = QtWidgets.QFileDialog.getExistingDirectory(self, "Select")
        if self.folderPath:
            line_edit.setText(self.folderPath)

    def accept(self):
        self.lasFolder = self.lasFolderLineEdit.text()
        self.photoFolder = self.photoFolderLineEdit.text()
        self.outFolder = self.outputFolderLineEdit.text()
        super().accept()


def main():
    main_window =QtWidgets.QApplication.instance().activeWindow()

    dlg = Dialog(main_window)

    if dlg.exec() != QtWidgets.QDialog.Accepted:
        return
    
    lasFolder = dlg.lasFolder
    photoFolder = dlg.photoFolder
    outFolder = dlg.outFolder

    laser_scans = [entry for entry in os.listdir(lasFolder) if entry.endswith(".las")]

    doc = Metashape.app.document
    doc.remove(doc.chunk)

    for scan in laser_scans:
        chunkname = scan.split(".")[0]
        doc.addChunk()
        chunks = doc.chunks
        chunks[-1].label = chunkname

    doc.save(outFolder + "/project.psx")

    for chunk in doc.chunks:
        name = str(chunk)
        photos = [photoFolder + "/" + name.split("'")[1] + "/" + photo for photo in os.listdir(photoFolder + "/" + name.split("'")[1] + "/") if photo.endswith(".JPG")]
        try:
            las_path = lasFolder + "/" + name.split("'")[1] + ".las"
            chunk.importPointCloud(las_path, is_laser_scan = False)
            chunk.addPhotos(photos, load_reference = True, load_xmp_accuracy = True, load_xmp_orientation = True, load_xmp_antenna = True, load_xmp_calibration = True)
            accuracy = Metashape.Vector((1, 1, 1))
            chunk.camera_rotation_accuracy = accuracy
        except:
            raise Exception(f"Failed to load data for chunk: {name}")

    doc.save()

    for chunk in doc.chunks:
        name = str(chunk)

        proj = Metashape.OrthoProjection()
        proj.crs = Metashape.CoordinateSystem("EPSG::2180")
        try:
            chunk.matchPhotos(downscale = 1, keypoint_limit = 40000, tiepoint_limit = 10000, generic_preselection = True, reference_preselection = True)
            doc.save()
            chunk.alignCameras()
            doc.save()
            chunk.buildDem(source_data = Metashape.PointCloudData, projection = proj)
            doc.save()
            chunk.buildOrthomosaic(surface_data = Metashape.ElevationData, projection = proj)
            doc.save()
            if chunk.orthomosaic:
                compression = Metashape.ImageCompression()
                compression.tiff_tiled = False
                compression.tiff_overviews = False
                compression.tiff_compression = Metashape.ImageCompression.TiffCompressionLZW
                compression.tiff_big = True
                chunk.exportRaster(path = outFolder + "/" + name.split("'")[1] + ".tif", 
                                source_data = Metashape.OrthomosaicData, 
                                projection = proj, 
                                image_compression = compression)
            doc.save()
        except:
            continue


label = "Scripts/Ortho from Las"
Metashape.app.addMenuItem(label, main)