import Metashape
from PySide2 import QtGui, QtCore, QtWidgets
import os

class Dialog(QtWidgets.QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.resize(500, self.height())

        self.setWindowTitle("Ortho Forest Workflow")

        self.photoFolderLabel = QtWidgets.QLabel("Path to photos folder")
        self.outputFolderLabel = QtWidgets.QLabel("Path to output folder")
        self.photoFolderLineEdit = QtWidgets.QLineEdit("V:\RDLP_Zielona Gora 2025\dane")
        self.outputFolderLineEdit = QtWidgets.QLineEdit("D:\___Lasy\out")
        self.photoButton = QtWidgets.QPushButton("Select photos")
        self.outButton = QtWidgets.QPushButton("Select output")

        self.photoButton.clicked.connect(lambda: self.openDirectory(self.photoFolderLineEdit))
        self.outButton.clicked.connect(lambda: self.openDirectory(self.outputFolderLineEdit))

        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.setCenterButtons(True)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.photoFolderLabel, 1, 0)
        layout.addWidget(self.photoFolderLineEdit, 1, 1)
        layout.addWidget(self.outputFolderLabel, 2, 0)
        layout.addWidget(self.outputFolderLineEdit, 2, 1)
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
        self.photoFolder = self.photoFolderLineEdit.text()
        self.outFolder = self.outputFolderLineEdit.text()
        super().accept()


def main():
    main_window =QtWidgets.QApplication.instance().activeWindow()

    dlg = Dialog(main_window)

    if dlg.exec() != QtWidgets.QDialog.Accepted:
        return
    
    photoFolder = dlg.photoFolder
    outFolder = dlg.outFolder

    photo_folders = [entry for entry in os.listdir(photoFolder) if os.path.isdir(os.path.join(photoFolder, entry))]

    doc = Metashape.app.document
    doc.remove(doc.chunk)
    
    for folder in photo_folders:
        chunkname = folder
        doc.addChunk()
        chunks = doc.chunks
        chunks[-1].label = chunkname
    
    doc.save(outFolder + "/project.psx")

    for chunk in doc.chunks:
        name = str(chunk)
        
        try:
            photos = [os.path.join(photoFolder, name.split("'")[1], "RGB", photo) for photo in os.listdir(os.path.join(photoFolder, name.split("'")[1], "RGB")) if photo.endswith(".JPG")]
            chunk.addPhotos(photos, load_reference = True, load_xmp_accuracy = True, load_xmp_orientation = True, load_xmp_antenna = True, load_xmp_calibration = True)
            accuracy = Metashape.Vector((1, 1, 1))
            chunk.camera_rotation_accuracy = accuracy
        except:
            pass

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
            chunk.buildDepthMaps(downscale = 2)
            doc.save()
            chunk.buildPointCloud(source_data = Metashape.DepthMapsData, point_colors = True, point_confidence = False)
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
            chunk.buildDem(source_data = Metashape.PointCloudData, classes = [2], projection = proj, replace_asset = True)
            doc.save()
            if chunk.elevation:
                compression = Metashape.ImageCompression()
                compression.tiff_tiled = False
                compression.tiff_overviews = False
                compression.tiff_compression = Metashape.ImageCompression.TiffCompressionLZW
                compression.tiff_big = True
                chunk.exportRaster(path = outFolder + "/" + name.split("'")[1] + "DEM.tif",
                                   source_data = Metashape.ElevationData,
                                   projection = proj,
                                   image_compression = compression)
            doc.save()
        except:
            print("FAIIILEEEDDDD")


label = "Scripts/Ortho Forest Workflow"
Metashape.app.addMenuItem(label, main)