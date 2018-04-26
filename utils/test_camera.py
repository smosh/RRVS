import sys
import struct

import cv2
import numpy as np

sys.path.append('../include')
#from camera_bbb import BBBCam as Camera
from cam_manager import CamManager as Video

def bytes2cv(buf):
    img = struct.unpack('B'*len(buf), buf)
    img = np.array(img, np.uint8)
    img = cv2.imdecode(img, cv2.IMREAD_UNCHANGED)

    return img

SELECTED_FEED = 'front'

def main():
    video = Video()

    print('test_camera.py: collecting camera data...')
    i = 0
    while (i <= 60) or True:
        img = video.get_frame(SELECTED_FEED)
        img = bytes2cv(img)
        i += 1

        cv2.imshow('frame', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            exit(0)



if __name__ == '__main__':
    main()