**Mandatory:**<br/>
 * Input Image (Multispectral raster, at least three bands)<br/>
 * Input Label (classified raster, single band)<br/>
 * Export Directory (where the image chips folder will be created)<br/>
 
**Available combinations in the plugin:**<br/>
 * Generate image chips of any window size and stride in TIFF and JPG format.<br/>
 * When stride is equal to or greater than the window size, the overlap is zero. When the stride is half of the window size, overlap is 50 per cent and so on.<br/>
 * When output format is TIFF, all the bands will be exported. Equalise Histogram option will be disabled.<br/>
 * When output format is JPG, three bands should be specified for export. Equalise Histogram option will be enabled.<br/>
 * If class value is null and center pixel is unchecked, all the non-zero values will be converted to 1 and will be considered as the label value. Label type can either be labelled tiles or mask pairs.<br/>
 * If class value is null and center pixel is checked, all the non-zero values will be converted to 1 and will be considered as the label value. Label type can can only be labelled tiles.<br/>
 * If class value is an integer or float, it will be converted to integer to be considered as label. The center pixel option will be disabled in this case. Label type can either be labelled tiles or mask pairs.<br/>


 ## 1. Export labelled tiles to see whether a feature is present or not in image chips ##
 ## 2. Export mask tiles to trace the footprint of the feature in image chips ##
 ## 3. Export tiles with the center pixel value of the classified raster as the label ##
