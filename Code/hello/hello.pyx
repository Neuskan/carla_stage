# cython:language_level=3

""" To use this library, you just have to make an "import hello" in your
    python script, launch the start_threads method at the top of the script

"""

import numpy as np
from matplotlib import pyplot as plt
import logging
from threading import get_ident,Thread
from concurrent.futures import ThreadPoolExecutor
import concurrent
import time
import os
from multiprocessing import Process
import cv2

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

def start_threads():
    """ Function needed to be called before everything else in this library, to init global
        variables to use to add executors to our ThreadPools later. The max_workers variable
        fix the maximum amount of threads working at the same time in the same Pool.
    """
    global futures 
    futures = []
    global executor 
    executor = ThreadPoolExecutor(max_workers=5)
    executor_bis = ThreadPoolExecutor(max_workers=5)
    global obj
    obj = Local()
    return futures, executor, executor_bis, obj

def conv_timestamp_cy(dvs_t : np.int64) -> float:
    """ Simply converts the timestamp in the image because it is a float value that
        has been saved like an integer value just by removing the comma in the value.
    """
    str_dvs_t = str(dvs_t)
    delim = len(str_dvs_t) - 9
    str_int_dvs_t = str_dvs_t[:delim]
    str_float_dvs_t = str_dvs_t[delim:]
    res = float(str_int_dvs_t + "." + str_float_dvs_t)
    return res

def go_fast_cy(obj, arg_image_frame, arg_dvs_events):
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
        res = conv_timestamp_cy(time)
        dvs_events2[i][2] = res
    
    with open(f'_out/dvs_{image_frame}.dat', 'w') as f:
        np.savetxt(f, dvs_events2, '%d %d %f %d')

def go_fast_cy_bis(obj, arg_image_frame, arg_dvs_img):
    """ The function simply saving raw data of the image into a pnf file. """
    obj.set(0, arg_image_frame)
    obj.set(1, arg_dvs_img)
    image_frame = obj.get(0)
    dvs_img = obj.get(1)
    
    plt.imsave('_out/%08d.png' % image_frame, dvs_img)

def add_threads(t_obj, t_executor, t_executor_bis, t_futures, t_frame, t_dvs_events, t_dvs_img):           
    """ Function submiting a working thread for the two ThreadPools
    """    
    a_result = t_executor.submit((go_fast_cy, t_obj, t_frame, t_dvs_events, ))
    a_result_bis = t_executor_bis.submit((go_fast_cy_bis, t_obj, t_frame, t_dvs_img, ))
    t_futures.append(a_result)
    t_futures.append(a_result_bis)