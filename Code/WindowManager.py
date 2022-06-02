import faulthandler
from multiprocessing import Queue, JoinableQueue, Event, Process
import multiprocessing
import os
import queue
import signal
import sys
from time import sleep
from PIL import Image
import tkinter as tk
from PIL import ImageTk,Image
import psutil

class Window(Process):
    """ The class launching a new window which will wait to receive image to display them, and
        will send commands to the parent process when we use the same shortcuts that in the 
        script "improved_manual_control" to change camera positions and sensors. So press 'n'
        if you want to use the next sensor, and 'Tab' if you want to use the next camera position.
    """
    def __init__(self, exit_event: Event, img_queue: multiprocessing.JoinableQueue(), cmd_queue: multiprocessing.JoinableQueue(), parent_pid: int, title: str, width: int, height: int):
        """ Initialisize the class.

        Args:
            exit_event (Event): variable for queue synchronization 
            img_queue (multiprocessing.Queue): variable for queue synchronization
            cmd_queue (multiprocessing.Queue): variable for queue synchronization
            parent_pid (int): should be the pid of parent process to close everything after work
            title (str): title of the window to create
            width (int): width of the window to create
            height (int): height of the window to create
        """
        super(Window, self).__init__()
        self.exit_event = exit_event
        self.img_queue = img_queue
        self.cmd_queue = cmd_queue
        self.parent_pid = parent_pid
        self.title = title
        self.width = width
        self.height = height
        # ws and label are just the two components of the tkinter window
        self.ws = None # ws is the window itself
        self.label = None # label is the container for the incoming images
         
    def run(self):
        """ the method what the new process created for the Window class will launch
            to init
        """
        # We setup signals for closing properly by using our own close method
        signal.signal(signal.SIGINT, self.close)
        signal.signal(signal.SIGTERM, self.close)
        
        # We initialize tkinter window, define her name, size and define her behaviour when we try to 
        # closing it
        self.ws = tk.Tk() 
        self.ws.protocol("WM_DELETE_WINDOW", self.close)
        self.ws.title(self.title)
        geo = str(self.width) + "x" + str(self.height)
        self.ws.geometry(geo)
        
        # We initialize the label who'll display the images
        self.label = tk.Label(self.ws, image=None)
        self.label.pack()
        
        # We set the shortcuts on the tkinter window
        self.ws.bind('n', self.next_sensor)
        self.ws.bind('<Tab>', self.toggle_camera)
        self.ws.bind('<Escape>', self.close)
        
        # The method after allow us to launch a function a certain amount of time after the tkinter
        # window has been launched. So what we are doing here is simply launching our main loop for the
        # window class, update, 1 millisecond after the tkinter window has launched. In this way, we can
        # sort of override the usual window loop of tkinter. We need to do this to always receive
        # incoming images because we can't init a loop of that sort in the init method, because of the way
        # python launch process and the tkinter display loop work.
        self.ws.after(1, self.update)
        
        # The method mainloop is the actual method who launch the tkinter display window, so before this
        # call, there is no window visible, and 1 millisecond after this call, our method update will be
        # called.
        self.ws.mainloop()
        
        # Simply closing properly everything after the tkinter loop stopped, so after we closed the window
        self.close()
        
    def next_sensor(self, evt):
        """ We send the command "NEXT_SENSOR" to the parent process. We don't care about the evt
            variable but python force us to put it in the arguments because next_sensor will be called
            when we'll use the 'n' shortcut
        """
        try:
            if not self.exit_event.is_set():
                self.cmd_queue.put_nowait("NEXT_SENSOR")
        except:
            pass

    def toggle_camera(self, evt):
        """ We send the command "TOGGLE_CAMERA" to the parent process. 

        Args:
            evt (_type_): We don't care about the evt variable but python force us to put it in the 
                          arguments because next_sensor will be called when we'll use the 'Tab' shortcut
        """
        try:
            if not self.exit_event.is_set():
                self.cmd_queue.put_nowait("TOGGLE_CAMERA")
        except:
            pass
        
    def close(self, signum=None, frame=None):
        """ The method closing properly the Window class by setting the exit_event variable to true
            if it's not already setted to true, and then close the tkinter window with the destroy
            call. We need to use the exit_event variable to prevent the parent process to send an image
            to this class if we are trying to close the window. 

        Args:
            signum (_type_, optional): Python force us to put these variable because close can be called
                                       after a signal but we don't use it. Defaults to None.
            frame (_type_, optional): Python force us to put these variable because close can be called
                                      after a signal but we don't use it. Defaults to None.
        """
        if not self.exit_event.is_set():
            self.exit_event.set()
            self.ws.destroy()
        
    def update(self):
        """ The actual main loop of the window. We simply wait try to get an image in the image queue if she
            still open (we know it grace of the exit_event variable) and if we get an image, we update the
            label image of the window, and continue the loop. We use get_nowait() to don't wait for an image
            but instead try to get one and if the queue is empty, an exception is raised but we catch it
            (queue.Empty) and just continue the loop. We do this because there is a high chance of crash
            and severals problems in python when we mess with multiprocessing while we are waiting on queues.
        """
        while not self.exit_event.is_set():
            try:
                newData = self.img_queue.get_nowait()
                newData = newData.resize((self.width, self.height))
                img = ImageTk.PhotoImage(image=newData)
                self.label.config(image=img)
                self.label.update()
            except (queue.Empty):
                # print("empty")
                continue
            except:
                print("break")
                break
                
class WindowClosed(Exception):
    """ Custom exception that does nothing, made to handle the case of the window
        closed by the user, in the parent process, with the "try / except" tool.
    """
    pass

class WindowManager(object):
    """ The starting point of the library. To use get our new window and use it, we
        we need firstly to launch this class and then use the recv_cmd_and_send_img
        method on this object to send an image. But we need to catch every exception when
        we do this in order to close everything properly, like we did in the
        main function.
    """
    
    def __init__(self, title="Other Camera", width=640, height=360, camera=None):
        """ Initialize the class.

        Args:
            title (str, optional): title of the window to create. Defaults to "Other Camera".
            width (int, optional): width of the window to create. Defaults to 640.
            height (int, optional): height of the window to create. Defaults to 360.
            camera (_type_, optional): the CameraManager object that we will
            give from the improved_manual_control script. Defaults to None.
        """
        self.exit_event = Event()
        self.img_queue = JoinableQueue()
        self.cmd_queue = JoinableQueue()
        self.camera = camera
        
        # Creating the window
        self.p = Window(self.exit_event, self.img_queue, self.cmd_queue, 
                        os.getpid(), title, width, height)
        
        # Launching the run method of the Window object
        self.p.start()

    def recv_cmd_and_send_img(self, img):
        """ The main method which consists in sending the images and receiving
            commands to change the state of the CameraManager, and also
            rasing a custom exception (WindowClosed) when the Window has been close.
            We know it when we get an exception by tring to do "psutil.Process(self.p.pid)"
            which should return the Window child process if it still running.

        Args:
            img (_type_): the image to send and display

        Raises:
            WindowClosed: custom exception created above
        """
        try:
            psutil.Process(self.p.pid)
        except:
            raise WindowClosed
        else:
            try:
                # If the queue still exist, we try to get a command that could
                # have been sent
                if not self.exit_event.is_set():
                    cmd = self.cmd_queue.get_nowait()
                    self.treat_cmd(cmd)
            except (queue.Empty):
                pass
            finally:
                try:
                    # If the queue still exist, we try to send the image
                    # have been sent
                    if not self.exit_event.is_set():
                        self.img_queue.put_nowait(img)
                except (queue.Full):
                    pass
            
    def treat_cmd(self, cmd):
        """ We treat the command sent by the child process and we call the
            corresponding method on the CameraManager object, to change the
            position of the camera and her sensors.

        Args:
            cmd (_type_): a simple string to determine which method we should
                          call on the CameraManager object
        """
        print(self.camera)
        print(cmd)
        if self.camera is not None:
            if cmd == "QUIT":
                self.camera.destroy()
            elif cmd == "NEXT_SENSOR":
                print("NEXT_SENSOR")
                self.camera.next_sensor()
            elif cmd == "TOGGLE_CAMERA":
                self.camera.toggle_camera()
            elif cmd == "PAUSE":
                self.camera.pause = not self.camera.pause
            elif cmd == "RECORD":
                self.camera.toggle_recording()
        else:
            print("Camera is not setted")

    def close_window(self):
        """ The method closing properly the WindowManager class by sending a kill
            signal to the child process only if he's still alive, and then join
            the child process to make sure everything has been freed.
        """
        try:
            psutil.Process(self.p.pid)
        except:
            pass
        else:
            os.kill(self.p.pid, signal.SIGINT)
        finally:
            self.p.join()
    
def main():    
    """ Just a little function to test the library alone (change the images paths
        for value1, value2 and value3).
    """
    m = WindowManager()
    value1 = Image.open('_out/img_00035867.png')
    value2 = Image.open('_out/img_00035870.png')
    value3 = Image.open('_out/img_00035874.png')
    while 1:
        try:
            m.recv_cmd_and_send_img(value1)
            m.recv_cmd_and_send_img(value2)
            m.recv_cmd_and_send_img(value3)
        except:
            m.close_window()
            break

if __name__ == '__main__':
    """ Launching the function of test if we run the program alone
    """
    if sys.__stderr__ is not None:
        faulthandler.enable(sys.__stderr__)
    main()