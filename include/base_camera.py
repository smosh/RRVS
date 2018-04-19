import time
import logging
import threading
try:
    from greenlet import getcurrent as get_ident
except ImportError:
    try:
        from thread import get_ident
    except ImportError:
        from _thread import get_ident

# configure logging system
logging.basicConfig(format='%(asctime)s :: %(message)s',
    filename='log.txt', 
    level=logging.DEBUG,
    datefmt='%m/%d/%Y %I:%M:%S %p')
        

READ_FRAME_TIMER = time.time()
READ_FRAME_COUNTER = 0
READ_FRAME_RATEMEAS = 0.0

class CameraEvent(object):
    """An Event-like class that signals all active clients when a new frame is
    available.
    """
    def __init__(self):
        self.events = {}

    def wait(self):
        """Invoked from each client's thread to wait for the next frame."""
        ident = get_ident()
        if ident not in self.events:
            # this is a new client
            # add an entry for it in the self.events dict
            # each entry has two elements, a threading.Event() and a timestamp
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait()

    def set(self):
        """Invoked by the camera thread when a new frame is available."""
        now = time.time()
        remove = None
        for ident, event in self.events.items():
            if not event[0].isSet():
                # if this client's event is not set, then set it
                # also update the last set timestamp to now
                event[0].set()
                event[1] = now
            else:
                # if the client's event is already set, it means the client
                # did not process a previous frame
                # if the event stays set for more than 5 seconds, then assume
                # the client is gone and remove it
                if now - event[1] > 5:
                    remove = ident
        if remove:
            del self.events[remove]

    def clear(self):
        """Invoked from each client's thread after a frame was processed."""
        self.events[get_ident()][0].clear()


class BaseCamera(object):
    event = CameraEvent()

    def __init__(self):
        self.thread = None  # background thread that reads frames from camera
        self.frame = None  # current frame is stored here by background thread
        self.last_access = 0  # time of last client access to the camera

        self.rlock = threading.RLock()

        self.settings = {}
        self.settings['timeout'] = 100.0

        """Start the background camera thread if it isn't running yet."""
        if self.thread is None: #TODO: delete this code
            # start background frame thread
            self.start_camera()
 
            # wait until frames are available
            while self.get_frame() is None:
                time.sleep(0)
        

    def start_camera(self):
        self.last_access = time.time()

        # start background frame thread
        self.thread = threading.Thread(target=self._thread)
        self.thread.start()

    def get_frame(self):
        """Return the current camera frame."""

        # auto-start the camera as needed
        self.rlock.acquire()
        if self.thread is None:
            self.start_camera()
        if not self.thread.isAlive():
            self.thread.start()
        self.rlock.release()


        # wait for a signal from the camera thread
        self.last_access = time.time()
        BaseCamera.event.wait()
        BaseCamera.event.clear()

        # self.frame was updated in the background thread
        return self.frame

    def frames(self):
        """"Generator that returns frames from the camera."""
        raise RuntimeError('Must be implemented by subclasses.')

    def _thread(self):
        """Camera background thread."""
        print('Starting camera thread.')

        global READ_FRAME_TIMER, READ_FRAME_COUNTER, READ_FRAME_RATEMEAS


        frames_iterator = self.frames()
        for frame in frames_iterator:
            if frame is not None:

                # shared variable: image data
                self.frame = frame 

                # signal to baseclass that the frame has been captured, 
                # and that self.frame contains fresh data
                BaseCamera.event.set() 

                # if there hasn't been any clients asking for frames in
                # the last x seconds then stop the thread
                if (time.time() - self.last_access) > self.settings['timeout']:
                    print('Stopping camera thread due to inactivity.')
                    frames_iterator.close()
                    break

                # print out rate data
                delta_time = time.time() - READ_FRAME_TIMER
                READ_FRAME_RATEMEAS += (1/delta_time) / (30*5)
                READ_FRAME_TIMER = time.time()
                READ_FRAME_COUNTER += 1

                if READ_FRAME_COUNTER >= (30*5):
                    print('base_camera.py: reading data at %.1fHz' % (READ_FRAME_RATEMEAS))
                    logging.debug("rate = %.1fHz" % (READ_FRAME_RATEMEAS) )
                    READ_FRAME_COUNTER = 0
                    READ_FRAME_RATEMEAS = 0.0
                    READ_FRAME_TIMER = time.time()



            else:
                self.frame = None
                BaseCamera.event.set()  # send signal to clients
                
                frames_iterator.close()
                print('base_camera.py:Error. Killing camera thread.')
                break


        self.rlock.acquire()
        self.thread = None
        self.rlock.release()
