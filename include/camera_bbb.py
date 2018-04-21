import base_camera
import cv2
import sys

class FrameRate(object):
    def __init__(self, buffer_size):
        self.buf_n  = buffer_size
        self.buf = np.zeros()

class BBBCam(base_camera.BaseCamera):

    def __init__(self, source):
        self.video_source = source
        super(BBBCam, self).__init__()

        self.error = {}
        self.error['disconnected'] = False # raised when a call to camera failed because it disconnected


    #def set_video_source(self, source):
    #    self.video_source = source
    
    def frames(self):
        try:
            camera_feed = cv2.VideoCapture(self.video_source)
            camera_feed.set(cv2.CAP_PROP_FRAME_WIDTH,320)
            camera_feed.set(cv2.CAP_PROP_FRAME_HEIGHT,240)
            #camera_feed.set(cv2.CAP_PROP_FPS, 10)
            if not camera_feed.isOpened():
                raise RuntimeError('Could not start camera.')
        except RuntimeError:
            print('Could not start camera.')
            yield None

        i = 0
        while True:
            # read current frame
            _, img = camera_feed.read()

            # encode as a jpeg image and return it
            if img is not None:
                temp = img
                i += 1
                try:
                    img = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 20])[1].tobytes()
                except:
                    print(temp)
                    import pdb; pdb.set_trace()
            else:
                print("camera_bbb.py: camera disconnected")
                self.kill_thread()
                self.raise_error('disconnected', sys.exc_info())
                img = None

            yield img

    def raise_error(self, name, value):
        self.error[name] = True
        self.error[name + '-value'] = value

    def get_error_status(self):
        return self.error

def main():
    c = BBBCam()
    

if __name__ == '__main__':
    main()
