# cython:language_level=3

""" To use this library, you just have to make an "import data_saving" in your
    python script, launch the starting_threads method at the top of the script

"""

import numpy as np
from matplotlib import pyplot as plt
from threading import get_ident,Thread
from concurrent.futures import ThreadPoolExecutor
import os
import concurrent
import time
from multiprocessing import Process

class Local(object):
    """ Define a class dictionary in order to use local variables for
        the threads because otherwise, every variable will be shared beetween them.
        This works because every threads will have their own Local object.
    """
    storage = {}
    
    def set(self, k, v):
        ident = get_ident()
        if ident in Local.storage:
            Local.storage[ident][k] = v
        else:
            Local.storage[ident] = {k: v}
            
    def get(self, k):
        ident = get_ident()
        return Local.storage[ident][k]

def starting_threads(max_workers=5):
    """ Function needed to be called before everything else in this library, to init global
        variables to use to add executors to our ThreadPools later. The max_workers variable
        fix the maximum amount of threads working at the same time in the same Pool.
    """
    global futures 
    futures = []
    global data_executor 
    data_executor = ThreadPoolExecutor(max_workers)
    img_data_executor = ThreadPoolExecutor(max_workers)
    global obj
    obj = Local()
    return futures, data_executor, img_data_executor, obj

def conv_timestamp(dvs_t : np.int64):
    """ Simply converts the timestamp in the image because it is a float value that
        has been saved like an integer value just by removing the comma in the value.
    """
    str_dvs_t = str(dvs_t)
    delim = len(str_dvs_t) - 9
    str_int_dvs_t = str_dvs_t[:delim]
    str_float_dvs_t = str_dvs_t[delim:]
    res = float(str_int_dvs_t + "." + str_float_dvs_t)
    return res

def saving_dvs_data(obj, arg_image_frame, arg_dvs_events):
    """ The function saving the data of the dvs camera in a ".dat" file. That means
        the timestamp of every pixel of a frame beetween two processed images on the
        simulator, with the coordonates of the pixel and his polarity.
    """
    obj.set(0, arg_image_frame)
    obj.set(2, arg_dvs_events)
    image_frame = obj.get(0)
    dvs_events = obj.get(2)

    obj.set(3, 
    (dvs_events.copy().astype([('x', np.uint16), ('y', np.uint16), ('t', float), ('pol', int)]))
    )
    dvs_events2 = obj.get(3)
    
    shape = dvs_events2.shape
    for i in range(shape[0]):
        time = dvs_events[i][2]
        res = conv_timestamp(time)
        dvs_events2[i][2] = res

    os.makedirs(os.path.dirname("_out/dvs"), exist_ok=True)
    with open(f'_out/dvs_{image_frame}.dat', 'w') as f:
        np.savetxt(f, dvs_events2, '%d %d %f %d')

def saving_img(obj, arg_image_frame, arg_dvs_img):
    """ The function simply saving raw data of the image into a pnf file. """
    obj.set(0, arg_image_frame)
    obj.set(1, arg_dvs_img)
    image_frame = obj.get(0)
    dvs_img = obj.get(1)
    os.makedirs(os.path.dirname("_out/img"), exist_ok=True)
    plt.imsave('_out/%08d.png' % image_frame, dvs_img)

def update_data_threads(th_obj, th_data_executor, th_futures, th_frame, th_dvs_events):       
    """ Function submiting a working thread to the data_executor pool
    """    
    th_result = th_data_executor.submit((saving_dvs_data, th_obj, th_frame, th_dvs_events, ))
    th_futures.append(th_result)

def update_img_threads(th_obj, th_img_data_executor, th_futures, th_frame, th_img):
    """ Function submiting a working thread to the data_executor pool
    """
    th_result = th_img_data_executor.submit((saving_img, th_obj, th_frame, th_img, ))
    th_futures.append(th_result)