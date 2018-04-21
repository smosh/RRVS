import glob
import subprocess
from camera_bbb import BBBCam as Camera

camera_names = ['primary', 'secondary']
def get_cam_info(path):
    '''
    issues a the following command:
        v4l2-ctl -d <campath> --info

    and returns the results
    '''
    p = subprocess.Popen(['v4l2-ctl', '-d', path, '--info'], stdout=subprocess.PIPE)
    out, _ = p.communicate()
    return out

class Feed(object):
    def __init__(self, name, path):
        self.name = name
        self.path = path

        video_idx = path.split('video')[-1]
        video_idx = int(video_idx)
        self.camera = Camera(video_idx)

        # info
        out = get_cam_info(self.path)
        out = out.translate(None, b'\t')
        out = out.split(b'\n')

        for line in out:
            #print(line)
            if b'Card type' in line:
                self.dev_name = line.split(b': ')[1]


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
        # generate name
        used_names = self.feed.keys()
        
        # select a name, if any of them are free
        for suggested_name in camera_names:
            if suggested_name in used_names:
                selected_name = ''
            else:
                selected_name = suggested_name
                break

        if selected_name is not '':
            self.feed[selected_name] = Feed(selected_name, path)
        else:
            print("cam_manager.py: unable to find a free feed name!")

    def kill_feed(self, name):
        for feed in list(self.feed.values()):

            if name == feed.name:
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
