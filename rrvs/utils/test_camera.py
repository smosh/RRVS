import sys
import struct
import os

import cv2
import numpy as np

ROOT_DIR = os.path.join(os.path.dirname(__file__), './')
sys.path.append(os.path.join(ROOT_DIR, '../include'))
#from camera_bbb import BBBCam as Camera
from cam_manager import CamManager as Video

def bytes2cv(buf):
    img = struct.unpack('B'*len(buf), buf)
    img = np.array(img, np.uint8)
    img = cv2.imdecode(img, cv2.IMREAD_UNCHANGED)

    return img

SELECTED_FEED = 'front'

def main(feed_id=SELECTED_FEED):
    video = Video()
    local = False

    if type(feed_id) == type(4):
        local = True

    print('test_camera.py: collecting camera data...')
    i = 0
    while (i <= 60) or True:
        if not local:
            img = video.get_frame(feed_id)
            img = bytes2cv(img)

        else:
            img = video.get_frame(feed_id)
            img = bytes2cv(img)

        i += 1

        cv2.imshow('frame', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            exit(0)



if __name__ == '__main__':
    if len(sys.argv) < 2:
        main()
    else:
        try:
            feed = int(sys.argv[1]) # 0 or 1 or ...
        except ValueError:
            feed = sys.argv[1] # 'back' or 'front' or ...
        main(feed)