import glob
import subprocess
import os
import time

from camera_bbb import BBBCam as Camera

ROOT_DIR = os.path.join(os.path.dirname(__file__), '../')
CFG_DIR = os.path.join(ROOT_DIR, 'cfg')

def get_camera_mappings():
    buf = ''
    mapping_file = os.path.join(CFG_DIR, 'mapping.cfg')
    with open(mapping_file, 'r') as f:
        for line in f:
            print(repr(line))
            if line == '':
                continue
            buf += line

    buf = buf.split('\n')
    buf = list(filter(lambda a: a != '', buf))
    
    mapping = {}
    for line in buf:
        dev_id, nickname = line.split(' :: ')
        mapping[dev_id] = nickname

    return mapping

def get_unique_camera_names():
    mapping = get_camera_mappings()
    names = mapping.values()
    names = list(set(names))
    return names

camera_names = get_unique_camera_names()

def get_cam_info(path):
    '''
    issues a the following command:
        v4l2-ctl -d <campath> --info

    and returns the results
    '''
    p = subprocess.Popen(['v4l2-ctl', '-d', path, '--info'], stdout=subprocess.PIPE)
    out, _ = p.communicate()
    return out

def get_cam_dev_name(path):
    info = b''; trys = 0
    while (info==b'') and (trys < 20):
        info = get_cam_info(path)
        trys += 1
        if (info==b''):
            time.sleep(0.1)

    info = info.translate(None, b'\t')
    info = info.split(b'\n')

    for line in info:
        if b'Card type' in line:
            dev_name = line.split(b': ')[1]
            break

    return dev_name


class Feed(object):
    def __init__(self, name, path):
        self.name = name
        self.path = path

        video_idx = path.split('video')[-1]
        video_idx = int(video_idx)

        # info
        out = get_cam_info(self.path)
        out = out.translate(None, b'\t')
        out = out.split(b'\n')

        for line in out:
            #print(line)
            if b'Card type' in line:
                self.dev_name = line.split(b': ')[1]

        print("associated %s (%s) with cv option %d" % (path, self.dev_name.decode('utf-8'), video_idx))

        self.camera = Camera(video_idx)



    def get_frame(self):
        return self.camera.get_frame()


    def __del__(self):
        del self.camera

class CamManager(object):
    def __init__(self):
        self.feed = {}
        self.active_ports = []

        # check for fresh feeds
        self.refresh_feeds()

    def get_frame(self, name):
        if name in self.feed.keys():
            return self.feed[name].get_frame()
        else:
            return None

    def print_camera_ctrls(self, name):
        print(name)


    # #####################
    # ### UGLY Functions ##
    # #####################

    def autostart_feed(self, path):
        # init
        selected_name = ''

        # generate data
        used_names = self.feed.keys()
        full_dev_name = get_cam_dev_name(path).decode('utf-8')
        mapping = get_camera_mappings()
        
        # attempt to select name based on the mapping file
        for key in mapping.keys():
            if key in full_dev_name:
                selected_name = mapping[key]

        if selected_name is not '':
            self.feed[selected_name] = Feed(selected_name, path)
            return
        
        # If fail, attemp to select a name based on availability
        for suggested_name in camera_names:
            if suggested_name in used_names:
                selected_name = ''
            else:
                selected_name = suggested_name
                break

        if selected_name is not '':
            self.feed[selected_name] = Feed(selected_name, path)
            return
        
        # nothing worked. generate an error
        print("cam_manager.py: unable to find a free feed name!")
        raise RuntimeError("Unable map device to a unique camera feed.")

    def kill_feed(self, name):
        for feed in list(self.feed.values()):

            if name == feed.name:
                feed.camera.cleanup()
                del self.feed[feed.name]

    def refresh_feeds(self):
        available_paths = glob.glob('/dev/video*')
        list_of_active_feeds = list(self.feed.values())
        print(available_paths)

        # kill inactive feeds
        for feed in list_of_active_feeds:
            if feed.path in available_paths:
                # good, feed is active
                pass
            else:
                # feed is no longer active. kill it
                self.kill_feed(feed.name)

        # update lise of active feeds
        list_of_active_feeds = self.feed.values()
        
        # create new feeds
        for path in available_paths:
            if path not in [feed.path for feed in list_of_active_feeds]:
                self.autostart_feed(path)
            else:
                pass
