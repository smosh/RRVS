import base_camera
import cv2

class FrameRate(object):
    def __init__(self, buffer_size):
        self.buf_n  = buffer_size
        self.buf = np.zeros()

class BBBCam(base_camera.BaseCamera):
    video_source = 0

    def __init__(self):
        super(BBBCam, self).__init__()

    @staticmethod
    def set_video_source(source):
        BBBCam.video_source = source
    
    @staticmethod
    def frames():
        camera_feed = cv2.VideoCapture(BBBCam.video_source)
        camera_feed.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH,320)
        camera_feed.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT,240)
        if not camera_feed.isOpened():
            raise RuntimeError('Could not start camera.')

        while True:
            # read current frame
            _, img = camera_feed.read()

            # encode as a jpeg image and return it
            yield cv2.imencode('.jpg', img)[1].tobytes()


def main():
    c = BBBCam()
    

if __name__ == '__main__':
    main()
