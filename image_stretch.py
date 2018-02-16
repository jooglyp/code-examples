import os
import sys
import rasterio
import numpy as np
from skimage.util.dtype import dtype_range
from skimage.util import img_as_ubyte, img_as_float
from skimage.morphology import disk
from skimage.filters import rank
from skimage import io, transform, exposure, data
import warnings


"""
Description:
    Script creates 4 stretched variations of input image using 4 different methods
    Write output files to input file directory

Requirements:
    scikit-image (skimage)
    rasterio

Usage:
    image_stretch.py "IMAGE_FILENAME"
Example:
    image_stretch.py "C:\Imagery\17NOV23153913-P2AS-057274106030_01_P001.TIF"
"""

def main(in_image):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with rasterio.open(in_image) as dataset:
            band1 = dataset.read(1)
            band1_profile = dataset.profile


        # QGIS-Based Stretching (mean +/- (standard deviation * 2))
        print "Performing QGIS Stretch..."
        std = band1.std()
        mean = band1.mean()
        stretch_range = (mean - (std * 2), mean + (std * 2))
        print "  - QGIS Range: {}".format(stretch_range)
        new_band1 = exposure.rescale_intensity(band1, in_range=(0, mean + (std * 2)), out_range='dtype')
        filename = os.path.splitext(os.path.basename(in_image))
        out_filename = os.path.join(os.path.dirname(in_image), "{}_Qgis{}".format(filename[0], filename[1]))
        if os.path.exists(out_filename):
            os.remove(out_filename)
        print "Writing... {}".format(out_filename)
        with rasterio.open(out_filename, 'w', **band1_profile) as dst:
            dst.write(new_band1, 1)

        print "----------------------------------------"

        # Histogram Stretch
        print "Performing Histogram Stretch..."
        # Ignore "nodata" pixels
        mask = band1 > 0
        img_eq_hist = exposure.equalize_hist(band1, mask=mask)
        img_eq_hist = img_as_ubyte(img_eq_hist)
        out_filename = os.path.join(os.path.dirname(in_image), "{}_Hist{}".format(filename[0], filename[1]))
        if os.path.exists(out_filename):
            os.remove(out_filename)
        print "Writing... {}".format(out_filename)
        with rasterio.open(out_filename, 'w', **band1_profile) as dst:
            dst.write(img_eq_hist, 1)
        
        print "----------------------------------------"

        # Percent Stretch
        print "Performing Percent Stretch..."
        p2, p98 = np.percentile(band1[mask], (2, 98))
        img_rescale = exposure.rescale_intensity(band1, in_range=(p2, p98))
        out_filename = os.path.join(os.path.dirname(in_image), "{}_Pct{}".format(filename[0], filename[1]))
        if os.path.exists(out_filename):
            os.remove(out_filename)
        print "Writing... {}".format(out_filename)
        with rasterio.open(out_filename, 'w', **band1_profile) as dst:
            dst.write(img_rescale, 1)

        print "----------------------------------------"

        # Sigmoid Stretch
        print "Performing Sigmoid Stretch..."
        sig = exposure.adjust_sigmoid(band1, cutoff=0.5, gain=10, inv=False)
        out_filename = os.path.join(os.path.dirname(in_image), "{}_Sig{}".format(filename[0], filename[1]))
        if os.path.exists(out_filename):
            os.remove(out_filename)
        print "Writing... {}".format(out_filename)
        with rasterio.open(out_filename, 'w', **band1_profile) as dst:
            dst.write(sig, 1)


if __name__ == '__main__':
    in_image = sys.argv[1]
    main(in_image)