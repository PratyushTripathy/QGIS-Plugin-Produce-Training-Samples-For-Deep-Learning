# -*- coding: utf-8 -*-
"""
/***************************************************************************
 produceTrainingDataForDeepLearning
                                 A QGIS plugin
 The plugin fragments the remote sensing image, to be used as deep learning training datasets.
 
                              -------------------
        begin                : 2019-12-26
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Pratyush Tripathy
        email                : pratkrt@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QAction, QFileDialog, QListWidgetItem

import os, time
from osgeo import gdal
from .dataGeneratorDeepLearning8 import dataGeneratorClass
# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .produce_training_data_for_deep_learning_dialog import produceTrainingDataForDeepLearningDialog
import os.path

class produceTrainingDataForDeepLearning:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'produceTrainingDataForDeepLearning_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Produce Training Data For Deep Learning')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('produceTrainingDataForDeepLearning', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToRasterMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/produce_training_data_for_deep_learning/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Training data generator for Deep Learning'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginRasterMenu(
                self.tr(u'&Produce Training Data For Deep Learning'),
                action)
            self.iface.removeToolBarIcon(action)

    def installDependencies(self):
        path = os.__file__.split('\\')
        path.pop()
        path.pop()
        path.append('python')
        path = '\\'.join(path)
        command1 = '%s -m pip install opencv-python --user' % (path)
        command2 = '%s -m pip install pyrsgis --user' % (path)
        os.system(command1)
        os.system(command2)
    
    def populateCanvasLayers(self):
        """
        When the plugin window initiates, this method adds
        the available layers in the QGIS canvas to the input
        raster drop down menu.
        """
        self.layers = self.iface.mapCanvas().layers()
        self.layersList = list()
        for layer in self.layers:
            self.layersList.append(layer.source())
        self.dlg.InputMxDropDown.clear()
        self.dlg.InputMxDropDown.addItems(self.layersList)
        self.inMxFile = self.dlg.InputMxDropDown.currentText()
        
        self.dlg.InputLabelDropDown.clear()
        self.dlg.InputLabelDropDown.addItems(self.layersList)
        self.inLabelFile = self.dlg.InputMxDropDown.currentText()
        
    def selectMxFile(self):
        """
        This method allows the user to select the MX raster
        from the directory. If the raster layer is not already
        opened in the QGIS session.
        """
        self.inMxFile, _filter = QFileDialog.getOpenFileName(self.dlg, 'Select multispectral raster', 'F:\\QGISplugin_DeepLearning',"GeoTif (*.tif)")
        self.dlg.InputMxDropDown.addItem(self.inMxFile)
        time.sleep(0.25)
        index = self.dlg.InputMxDropDown.findText(self.inMxFile, QtCore.Qt.MatchFixedString)
        self.dlg.InputMxDropDown.setCurrentIndex(index)
        time.sleep(0.25)

    def selectLabelFile(self):
        """
        This method allows the user to select the labelled raster
        from the directory. If the raster layer is not already
        opened in the QGIS session.
        """
        self.inLabelFile, _filter = QFileDialog.getOpenFileName(self.dlg, 'Select classified raster', 'F:\\QGISplugin_DeepLearning',"GeoTif (*.tif)")
        self.dlg.InputLabelDropDown.addItem(self.inLabelFile)
        time.sleep(0.25)
        index = self.dlg.InputLabelDropDown.findText(self.inLabelFile, QtCore.Qt.MatchFixedString)
        self.dlg.InputLabelDropDown.setCurrentIndex(index)
        time.sleep(0.25)
        
    def selectOutputDirectory(self):
        """
        This method allows the user to select the output
        directory for image chips.
        """
        self.outDirectory = QFileDialog.getExistingDirectory(self.dlg, 'Select export directory', 'F:\\QGISplugin_DeepLearning')
        self.dlg.outputDirectory.setText(self.outDirectory)
        time.sleep(0.25)
        os.chdir(self.outDirectory)

    def updateEualiseHistogramStatus(self):
        if self.dlg.equaliseHistogramCheckBox.isChecked() == True:
            self.equalise = True
        else:
            self.equalise = False

    def toggleCenterPixelLabel(self):
        if self.dlg.classValue.text().upper() == 'NULL':
            self.centerPixelIsLabel = True
            self.dlg.centerPixelLabel.setDisabled(False)
            self.dlg.labelDropDown.setDisabled(True)
        else:
            self.centerPixelIsLabel = False
            self.dlg.centerPixelLabel.setDisabled(True)
            # When class value is Null, label drop down should be defaulted to labelled tiles before disabling
            if self.dlg.labelDropDown.currentText() == self.dlg.labelDropDown.itemText(1):
                self.dlg.labelDropDown.setCurrentIndex(0)
            self.dlg.labelDropDown.setDisabled(False)
                       
    def populateBandsDropDown(self):
        """
        This method is called when the output format is
        changed from TIFF to JPG or PNG. The method
        inquires the number of bands of the multispectral
        raster and adds them to the drop down for three
        colour guns.
        """
        self.dlg.mRasterBandComboBoxBlue.clear()
        self.dlg.mRasterBandComboBoxGreen.clear()
        self.dlg.mRasterBandComboBoxRed.clear()
        # Declaring this here is important to avoid the Python Error: Variable referred before assignment.
        nBands = 0 
        try:
            nBands = gdal.Open(self.inMxFile).RasterCount
        except:
            self.iface.messageBar().pushMessage("Please select a multispectral raster first.", duration=3)
        for idx in range(nBands):
            bandName = 'Band %d' % (idx+1)
            self.dlg.mRasterBandComboBoxBlue.addItems([bandName])
            self.dlg.mRasterBandComboBoxGreen.addItems([bandName])
            self.dlg.mRasterBandComboBoxRed.addItems([bandName])

    def updateBandsDropDownState(self):
        """
        This method enables/ disables the options
        dependent on the FORMAT of the output file.
        """
        index = self.dlg.formatDropDown.findText(self.dlg.formatDropDown.currentText(), QtCore.Qt.MatchFixedString)
        #print(index)
        if index == 0:
            self.dlg.label_13.setDisabled(True)
            self.dlg.label_14.setDisabled(True)
            self.dlg.label_15.setDisabled(True)
            self.dlg.label_16.setDisabled(True)
            self.dlg.mRasterBandComboBoxBlue.setDisabled(True)
            self.dlg.mRasterBandComboBoxGreen.setDisabled(True)
            self.dlg.mRasterBandComboBoxRed.setDisabled(True)
            self.dlg.equaliseHistogramCheckBox.setDisabled(True)
        else:
            self.dlg.label_13.setDisabled(False)
            self.dlg.label_14.setDisabled(False)
            self.dlg.label_15.setDisabled(False)
            self.dlg.label_16.setDisabled(False)
            self.dlg.mRasterBandComboBoxBlue.setDisabled(False)
            self.dlg.mRasterBandComboBoxGreen.setDisabled(False)
            self.dlg.mRasterBandComboBoxRed.setDisabled(False)
            self.dlg.equaliseHistogramCheckBox.setDisabled(False)
            self.populateBandsDropDown()

    def getJpgBandNumbers(self):
        self.blueBand = self.dlg.mRasterBandComboBoxBlue.currentText().split(' ')[1]
        self.greenBand = self.dlg.mRasterBandComboBoxGreen.currentText().split(' ')[1]
        self.redBand = self.dlg.mRasterBandComboBoxRed.currentText().split(' ')[1]
        #print(self.blueBand, self.greenBand, self.redBand)

    def updateEnteredParameters(self):
        if self.dlg.classValue.text().upper() == 'NULL':
            if self.dlg.centerPixelLabel.isChecked():
                self.classValue = 'center pixel'
            else:
                self.classValue = self.dlg.classValue.text()
                self.centerPixelIsLabel = False
        else:
            self.classValue = float(self.dlg.classValue.text())
        
        self.windowSizeX = int(self.dlg.windowSizeX.text())
        self.windowSizeY = int(self.dlg.windowSizeY.text())
        self.strideX = int(self.dlg.strideX.text())
        self.strideY = int(self.dlg.strideY.text())
        
        self.labelType = self.dlg.labelDropDown.currentText()
        if self.labelType == 'Labelled Tiles':
            self.labelType = 'label'
        else:
            self.labelType = 'mask'
        self.format = self.dlg.formatDropDown.currentText()
        if self.format.upper() == 'JPG':
            self.getJpgBandNumbers()
        #print(self.classValue, self.windowSizeX, self.windowSizeY, self.strideX, self.strideY)
        
    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = produceTrainingDataForDeepLearningDialog()
            self.populateCanvasLayers()
            self.dlg.pushButtonMx.clicked.connect(self.selectMxFile)
            self.dlg.pushButtonLabel.clicked.connect(self.selectLabelFile)
            self.dlg.pushButtonOutput.clicked.connect(self.selectOutputDirectory)
            self.dlg.pushButtonDependencies.clicked.connect(self.installDependencies)
            self.dlg.formatDropDown.currentIndexChanged.connect(self.updateBandsDropDownState)
            self.equalise = True
            self.centerPixelIsLabel = True
            
        # show the dialog
        self.dlg.show()
        #print(self.dlg.width(), self.dlg.height())
        
        self.dlg.equaliseHistogramCheckBox.toggled.connect(self.updateEualiseHistogramStatus)
        self.dlg.classValue.textChanged.connect(self.toggleCenterPixelLabel)

        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            self.updateEnteredParameters()
            
            if self.format.upper() == 'JPG':
                self.getJpgBandNumbers()
                prototype = dataGeneratorClass(mxFileList = [self.inMxFile],
                                   labelledFile = self.inLabelFile,
                                   windowX = self.windowSizeX,
                                   windowY = self.windowSizeY,
                                   strideX = self.strideX,
                                   strideY = self.strideY,
                                   labelType = self.labelType,
                                   classValue = self.classValue,
                                   outFormat=self.format,
                                   jpgBands = [self.blueBand, self.greenBand, self.redBand],
                                   equalise = self.equalise,
                                   outDir = self.outDirectory,
                                   centerLabel = self.centerPixelIsLabel)
            else:
                prototype = dataGeneratorClass(mxFileList = [self.inMxFile],
                                   labelledFile = self.inLabelFile,
                                   windowX = self.windowSizeX,
                                   windowY = self.windowSizeY,
                                   strideX = self.strideX,
                                   strideY = self.strideY,
                                   labelType = self.labelType,
                                   classValue = self.classValue,
                                   outFormat=self.format,
                                   equalise = self.equalise,
                                   outDir = self.outDirectory,
                                   centerLabel = self.centerPixelIsLabel)
            
            
