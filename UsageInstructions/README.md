### **Available combinations in the plugin:** ###
* Export labelled tiles to see whether a feature is present or not in image chips
* Export mask tiles to trace the footprint of the feature in image chips
* Export tiles with the center pixel value of the classified raster as the label

### **Mandatory:** ###
 * Input Image (Multispectral raster, at least three bands)<br/>
 * Input Label (classified raster, single band)<br/>
 * Export Directory (where the image chips folder will be created)<br/>
  
### **Options:** ###
 * **Class Value** - 
   * If the class value is *Null*, non-zero values will be converted to 1 and considered as the label value. The center pixel feature will be optional.
   * If class value is an integer or float, it will be converted to integer to be considered as label. The center pixel feature will be disabled in this case.
 * **Center Pixel** - will be active only when **Class Value** is *Null*.
 * **Window Size** - size should be given as integers. Image chips can be generated of any window size.
 * **Stride** - This is the amount of shift in the window for consecutive image chips. When stride is equal to or greater than the window size, the overlap is zero. When the stride is half of the window size, overlap is 50 per cent and so on.
 * **Equalise Histogram** - will be active only when the output format is JPG. It uses [*opencv::equaliseHistogram*](https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_histograms/py_histogram_equalization/py_histogram_equalization.html) function in the backend.
 * **Label Type** - will be active only when **Center Pixel** is not checked. Default is *Labelled Tiles*.
   * *Labelled Tiles* produces image chips with labels only.
   * *Mask Pairs* produces image chips and corresponding mask from the classified raster. (This option is not available when **Center Pixel** option is checked.)
 * **Format** - output format of image chips.
   * JPG format requires three bands for the RGB colour guns.
   * When JPG format is opted and **Equalise Histogram** is checked, the input image is converted to 8-bit data.
   * TIFF format exports all the bands in the input raster. **Equalise Histogram** option will be disabled. Original values of the raster will be exported.
   
