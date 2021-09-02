import os, math
import numpy as np
try:
    import gdal
except:
    from osgeo import gdal

# This function is called when the dependencies are not present
def firstTimeRun():
    path = os.__file__.split('\\')
    path.pop()
    path.pop()
    path.append('python')
    path = '\\'.join(path)
    command = '%s -m pip install opencv-python pyrsgis --user' % (path)
    os.system(command)

try:
    import cv2
    from pyrsgis import raster
except:
    firstTimeRun()
    
class dataGeneratorClass():
    # The data generator class initiates with the input file names and the required parameters
    def __init__(self, mxFileList, labelledFile, windowX, windowY, strideX, strideY, labelType, classValue='NULL', centerLabel=True, outFormat='tif', jpgBands=[1,2,3], equalise=True, outDir=os.getcwd()):
        self.inputFiles = list(mxFileList)
        self.labelFile = labelledFile
        self.windowXSize = windowX
        self.windowYSize = windowY
        self.strideX = strideX
        self.strideY = strideY
        self.labelType = labelType
        self.classValue = classValue
        self.centerPixelIsLabel = centerLabel
        self.outFormat = outFormat
        self.jpgBands = jpgBands
        
        self.performChecks()
        self.generateFeaturesLabelArray()
        self.createCoordinateMesh()
        if self.outFormat.upper() == 'JPG' or self.outFormat.upper() == 'PNG':
            self.geoLocation = False
            self.generateJpgFeatures(bands = jpgBands, equalise = equalise)
        else:
            self.geoLocation = True
        self.generateData(exportDir=outDir)
        

    # A method to check the geometries of input files
    def performChecks(self):
        self.checksCleared = True
        ds = gdal.Open(self.labelFile)
        xSize = ds.RasterXSize
        ySize = ds.RasterYSize
        geoTransform = ds.GetGeoTransform()
        projection = ds.GetProjection()

        # Check if the labe file is a single band raster
        if ds.RasterCount > 1:
            self.checksCleared = False
            print('InputError: Input label image is not a single band raster.')
        # Transformation and projection issue tracker
        transformIssue = False
        projectionIssue = False
        for file in self.inputFiles:
            ds = gdal.Open(file)
            # If the rows and columns do not match, execution terminates
            if (not xSize == ds.RasterXSize) or (not ySize == ds.RasterYSize):
                print('GeometryError: The cols and rows of input files do not match.')
                self.checksCleared = False
                break
            if not geoTransform == ds.GetGeoTransform():
                transformIssue = True
            if not projection == ds.GetProjection():
                projectionIssue = True
                ds = None
        # If any of the files have a different projection or geo-transform,
        # execution proceeds if the rows and columns are the same
        if projectionIssue == True:
            print('Warning! The projection of input files are different. Proceeding if number of rows and cols are the same.')
        if transformIssue == True:
            print('Warning! The cell size or the extent of input files are different. Proceeding if number of rows and cols are the same.')

        # If input files clear the checks, initiate the default geometry values
        if self.checksCleared == True:
            self.xSize = xSize
            self.ySize = ySize
            self.geoTransform = geoTransform
            self.projection = projection

    # A method to generate features and label array
    def generateFeaturesLabelArray(self):
        for n, file in enumerate(self.inputFiles):
            ds = gdal.Open(file)
            self.ds = raster.createDS(ds)
            # If it the first file, create the numpy array, else concatenate to the existing array
            if n == 0:
                features = ds.ReadAsArray()
            else:
                # If the current file is a multispectral image or single band image, treat them differently
                if ds.RasterCount > 1:
                    # If the already present feature array is three dimesional, reshape before concatenation
                    if len(features.shape) == 3:
                        features = np.concatenate((features, ds.ReadAsArray()))
                    else:
                        features = np.concatenate((np.reshape(features, (1, features.shape[0], features.shape[1])), ds.ReadAsArray()))
                else:
                    # If the already present feature array is three dimesional, reshape before concatenation
                    if len(features.shape) == 3:
                        features = np.concatenate((features, np.reshape(ds.ReadAsArray(), (1, ds.RasterXSize, ds.RasterYSize))))
                    else:
                        features = np.concatenate((np.reshape(features, (1, features.shape[0], features.shape[1])), np.reshape(ds.ReadAsArray(), (1, ds.RasterXSize, ds.RasterYSize))))
        self.features = features
        self.labels = gdal.Open(self.labelFile).ReadAsArray()

        if type(self.classValue) in [type(1), type(1.1)]:
            self.labels = (self.labels == self.classValue).astype(int)
            self.centerPixelIsLabel = False
        elif self.classValue.upper() == 'CENTER PIXEL':
            self.labels = ((self.labels > 0) * self.labels).astype(int)
            self.centerPixelIsLabel = True
        else:
            self.labels = ((self.labels > 0) * self.labels).astype(int)
    
    # A method to create upper left coordinate mesh
    def createCoordinateMesh(self):
        ulLong = self.geoTransform[0]
        ulLat = self.geoTransform[3]
        xCellSize = self.geoTransform[1]
        yCellSize = self.geoTransform[-1]

        lrLong = ulLong + (xCellSize * self.xSize)
        lrLat = ulLat + (yCellSize * self.ySize)
        
        self.longitudeMesh = np.arange(ulLong, lrLong+xCellSize, xCellSize)
        self.latitudeMesh = np.arange(ulLat, lrLat+yCellSize, yCellSize)

        #self.longitudeMesh = np.linspace(ulLong, lrLong, self.xSize)
        #self.latitudeMesh = np.linspace(ulLat, lrLat, self.ySize)
        
        #self.longitudeMesh, self.latitudeMesh = np.meshgrid(longitudeMesh, latitudeMesh)

    def generateChipDs(self, row, col):
        dummyDs = self.ds
        dummyTransform = list(self.geoTransform)
        
        dummyTransform[0] = self.longitudeMesh[col]
        dummyTransform[3] = self.latitudeMesh[row]

        dummyDs.GeoTransform = tuple(dummyTransform)
        return(dummyDs)
            
    def normalise8bit(self, arr, depth=8):
        temp = (arr-arr.min()) / (arr.max()-arr.min())
        temp = 2**depth*temp
        return(temp)

    # A method to equalise the histogram of the image if the selected format is JGP/ PNG
    def generateJpgFeatures(self, bands, equalise=True):
        if not len(bands) == 3:
            print('ERROR! Exporting jpeg requires 3 bands.')
        else:
            bands = [int(i)-1 for i in bands]
            blue_idx, green_idx, red_idx = bands[:3]
        
            blueArr = self.normalise8bit(self.features[blue_idx, :, :])
            greenArr = self.normalise8bit(self.features[green_idx, :, :])
            redArr = self.normalise8bit(self.features[red_idx, :, :])

            if equalise == True:
                blueArr = cv2.equalizeHist(blueArr.astype(np.uint8))
                greenArr = cv2.equalizeHist(greenArr.astype(np.uint8))
                redArr = cv2.equalizeHist(redArr.astype(np.uint8))

            self.jpgFeatures = cv2.merge([blueArr,greenArr,redArr])

    def exportTifChip(self, labelType, featureWindow, labelWindow=None, featureFile='x.tif', labelFile='y.tif', ds=None):
        if labelType == 'label':
            raster.export(featureWindow, ds, filename=featureFile, bands='all')
        if labelType == 'mask':
            raster.export(featureWindow, ds, filename=featureFile, bands='all')
            raster.export(labelWindow, ds, filename=labelFile)
    
    def exportJpgChip(self, labelType, featureWindow, labelWindow=None, featureFile='x.jpg', labelFile='y.jpg'):
        if labelType == 'label':
            cv2.imwrite(featureFile, featureWindow)
        if labelType == 'mask':
            cv2.imwrite(featureFile, featureWindow)
            cv2.imwrite(labelFile, labelWindow)
    
    def generateData(self, exportDir):
        os.chdir(exportDir)
        if not os.path.exists('ImageChips'):
            os.mkdir('ImageChips')

        if self.windowXSize % 2 == 0:
            xBuffer = 0
        else:
            xBuffer = 1
            
        if self.windowYSize % 2 == 0:
            yBuffer = 0
        else:
            yBuffer = 1
            
        self.xWindowMargin = math.floor(self.windowXSize / 2)
        self.yWindowMargin = math.floor(self.windowYSize / 2)

        n = 0
        for row in range(self.yWindowMargin, self.ySize-self.yWindowMargin, self.strideY):
            for col in range(self.xWindowMargin, self.xSize-self.xWindowMargin, self.strideX):
                #print('Row: %d, Col: %d' % (row, col))
                
                # Keeping the stride margin on all edges
                if (self.xSize - col > self.strideX) and (self.ySize - row > self.strideY):
                    n += 1
                    
                    # For GeoTif output
                    if self.outFormat.upper() == 'TIFF' or self.outFormat.upper() == 'TIF':
                        ds = self.generateChipDs(row-self.yWindowMargin, col-self.xWindowMargin)
                        
                        featureWindow = self.features[:, row-self.yWindowMargin:row+self.yWindowMargin+yBuffer, col-self.xWindowMargin:col+self.xWindowMargin+xBuffer]
                        
                        if not self.centerPixelIsLabel == True:
                            labelWindow = self.labels[row-self.yWindowMargin:row+self.yWindowMargin+yBuffer, col-self.xWindowMargin:col+self.xWindowMargin+xBuffer]
                            
                            print(labelWindow.shape)
                            if type(labelWindow) == type(1):
                                if labelWindow > 0:
                                    label = 1
                            elif sum(sum(labelWindow)) > 0:
                                  label = 1
                            else:
                                label = 0

                            featureFile = '%s/Feature%d_%d.tif' % ('ImageChips', n, label)
                            
                            if self.labelType.upper() == 'LABEL':
                                self.exportTifChip(labelType='label', featureWindow=featureWindow, featureFile=featureFile, ds=ds)
                                
                            elif self.labelType.upper() == 'MASK':
                                labelFile = '%s/Mask%d_%d.tif' % ('ImageChips', n, label)
                                self.exportTifChip(labelType='mask', featureWindow=featureWindow, labelWindow=labelWindow, featureFile=featureFile, labelFile=labelFile, ds=ds)

                        else:
                            label = self.labels[row, col]
                            labelWindow = self.labels[row-self.yWindowMargin:row+self.yWindowMargin+yBuffer, col-self.xWindowMargin:col+self.xWindowMargin+xBuffer]
                            featureFile = '%s/Feature%d_%d.tif' % ('ImageChips', n, label)
                            labelFile = '%s/Label%d_%d.tif' % ('ImageChips', n, label)
                            
                            if self.labelType.upper() == 'LABEL':
                                self.exportTifChip(labelType='label', featureWindow=featureWindow, featureFile=featureFile, ds=ds)
                                
                            elif self.labelType.upper() == 'MASK':
                                labelFile = '%s/Mask%d_%d.tif' % ('ImageChips', n, label)
                                self.exportTifChip(labelType='mask', featureWindow=featureWindow, labelWindow=labelWindow, featureFile=featureFile, labelFile=labelFile, ds=ds)


                    # For image type output (without geolocation)
                    else:
                        featureWindow = self.jpgFeatures[row-self.yWindowMargin:row+self.yWindowMargin+yBuffer, col-self.xWindowMargin:col+self.xWindowMargin+xBuffer, :]

                        if not self.centerPixelIsLabel == True:
                            labelWindow = self.labels[row-self.yWindowMargin:row+self.yWindowMargin+yBuffer, col-self.xWindowMargin:col+self.xWindowMargin+xBuffer]

                            if sum(sum(labelWindow)) > 0:
                                label = 1
                            else:
                                label = 0

                            featureFile = '%s/Feature%d_%d.jpg' % ('ImageChips', n, label)
                            
                            if self.labelType.upper() == 'LABEL':
                                self.exportJpgChip(labelType='label', featureWindow=featureWindow, featureFile=featureFile)
                                
                            elif self.labelType.upper() == 'MASK':
                                labelFile = '%s/Mask%d_%d.jpg' % ('ImageChips', n, label)
                                self.exportJpgChip(labelType='mask', featureWindow=featureWindow, labelWindow=labelWindow, featureFile=featureFile, labelFile=labelFile)

                        else:
                            label = self.labels[row, col]
                            labelWindow = self.labels[row-self.yWindowMargin:row+self.yWindowMargin+yBuffer, col-self.xWindowMargin:col+self.xWindowMargin+xBuffer]
                            featureFile = '%s/Feature%d_%d.jpg' % ('ImageChips', n, label)
                            labelFile = '%s/Label%d_%d.jpg' % ('ImageChips', n, label)
                            
                            if self.labelType.upper() == 'LABEL':
                                self.exportJpgChip(labelType='label', featureWindow=featureWindow, featureFile=featureFile)
                                
                            elif self.labelType.upper() == 'MASK':
                                labelFile = '%s/Mask%d_%d.jpg' % ('ImageChips', n, label)
                                self.exportTifChip(labelType='mask', featureWindow=featureWindow, labelWindow=labelWindow, featureFile=featureFile, labelFile=labelFile)


                

###############################
###############################
###############################
"""
myDir = r'F:\QGISplugin_DeepLearning'
mxFilesList = ['feature_raster.tif']
labelFile = 'label_raster.tif'
os.chdir(myDir)

prototype = dataGeneratorClass(mxFileList = mxFilesList,
                               labelledFile = labelFile,
                               windowX = 100,
                               windowY = 100,
                               strideX = 100,
                               strideY = 100,
                               labelType = 'label',
                               classValue = 1,
                               outFormat='jpg')
prototype.generateFeaturesLabelArray()
prototype.createCoordinateMesh()
prototype.equaliseBands(bands = [2,3,4])
prototype.generateData(exportDir=myDir)
"""

