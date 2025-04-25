import pycc
import cccorelib

CC = pycc.GetInstance()

params = pycc.FileIOFilter.LoadParameters()
params.coordinatesShiftEnabled = True
params.shiftHandlingMode = pycc.ccGlobalShiftManager.Mode.NO_DIALOG_AUTO_SHIFT
params.alwaysDisplayLoadDialog = False
params.parentWidget = CC.getMainWindow()

path = r"D:\___WodyPolskie\Gora\winsko_przetwarzanie\las\gora-winsko-lot-1.las"

#obj = pycc.FileIOFilter.LoadFromFile(path, params)
obj = CC.loadFile(path, params)


child = obj.getChild(0)

bbox = child.ccBBox()

grid = pycc.ccRasterGrid()

grid.gridStep = 1.0

grid.init(bbox, 2, grid.gridStep, 0)

grid.updateCellStats()

grid.saveToGeoTIFF(r"D:\___WodyPolskie\Gora\winsko_przetwarzanie\las\test.tif", pycc.ccRasterGrid.GridLayer.R_RGB)

