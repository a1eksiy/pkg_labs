import numpy as np

def channel_histograms(image):
    return [np.bincount(image[:,:,c].ravel(),minlength=256) for c in range(3)]

def histogram_data(image):
    return channel_histograms(image)
