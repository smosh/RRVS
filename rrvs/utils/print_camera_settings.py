import sys
import struct

import cv2
import numpy as np

sys.path.append('./include')
from cam_manager2 import CamManager as Video


def main():
    import pdb; pdb.set_trace()
    video = Video()
    video.refresh_feeds()

    feeds = video.get_active_feeds()

    for feed in feeds:
        video.print_camera_ctrls(feed)


if __name__ == '__main__':
    main()