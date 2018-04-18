import base_camera
import cv2

class FrameRate(object):
    def __init__(self, buffer_size):
        self.buf_n  = buffer_size
        self.buf = np.zeros()

class BBBCam(base_camera.BaseCamera):

    def __init__(self, source):
        self.video_source = source
        super(BBBCam, self).__init__()


    #def set_video_source(self, source):
    #    self.video_source = source
    
    def frames(self):
        try:
            camera_feed = cv2.VideoCapture(self.video_source)
            camera_feed.set(cv2.CAP_PROP_FRAME_WIDTH,480)
            camera_feed.set(cv2.CAP_PROP_FRAME_HEIGHT,360)
            if not camera_feed.isOpened():
                raise RuntimeError('Could not start camera.')
        except RuntimeError:
            print('Could not start camera.')
            yield None


        while True:
            # read current frame
            _, img = camera_feed.read()

            # encode as a jpeg image and return it
            try:
                img = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 20])[1].tobytes()
            except:
                img = None

            yield img

def main():
    c = BBBCam()
    

if __name__ == '__main__':
    main()
