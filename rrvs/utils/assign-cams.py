import glob
import subprocess
import os
import sys
import time
from collections import OrderedDict

ROOT_DIR = os.path.join(os.path.dirname(__file__), '../')
CFG_DIR = os.path.join(ROOT_DIR, 'cfg')

def get_camera_mappings():
    buf = ''
    mapping_file = os.path.join(CFG_DIR, 'mapping.cfg')
    with open(mapping_file, 'r') as f:
        for line in f:
            buf += line

    buf = buf.split('\n')
    
    mapping = OrderedDict()
    for line in buf:
        if line == '':
            continue
        dev_id, nickname = line.split(' :: ')
        mapping[dev_id] = nickname

    return mapping

def get_unique_camera_names():
    mapping = get_camera_mappings()
    names = mapping.values()
    names = list(set(names))
    return names

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

def get_list_connected_devices():
    detected_devices = []
    available_paths = glob.glob('/dev/video*')
    for path in available_paths:
        detected_devices.append( get_cam_dev_name(path) )
    return (detected_devices, available_paths)

def query(text):
    print(text)
    response = input('>> ')
    return response

class Mapping(object):
    def __init__(self):
        self.dev_name = None
        self.path = None
        self.stream_name = None
        self.search_string = None
        
    def print(self):
        msg = ("dev_name: %s\n" % self.dev_name) \
            + ("path: %s\n" % self.path) \
            + ("stream_name: %s\n" % self.stream_name) \
            + ("search_string: %s\n" % self.search_string)

        print(msg)


class Wizard(object):
    def __init__(self):
        self.state = 'init'
        self.next_state = 'init'

        self.tests = None
        self.items_to_check = []
        self.mapping = []
        self.current_test = None

        self.system = {}
        self.system['mappings'] = None

        self.user = {}
        self.user['selected-device-name'] = None
        self.user['selected-path'] = None
        self.user['selected-stream-name'] = None
        self.user['selected-search-string'] = None

    def clear_user_data(self):
        for key in self.user.keys():
            self.user[key] = None

    def print_splash(self):
        msg = \
        "---------------------------------------\n"\
        "------- Camera Mapping Utility --------\n"\
        "---------------------------------------\n"


        print(msg)

    def run(self):
        while (self.state != 'exit'):
            state = self.state
            if state == 'init':
                self.print_splash()

                # collect data
                mapping_dict = get_camera_mappings()
                (detected_devices, detected_paths) = get_list_connected_devices()

                # collect tests
                self.mapping = []
                i = -1
                for item in mapping_dict.items():
                    i += 1

                    # append
                    self.mapping.append( Mapping() )

                    # collect data
                    (search_str, stream_name) = item

                    # append data
                    self.mapping[i].search_string = search_str
                    self.mapping[i].stream_name = stream_name
                

                # Append devices to test if necessary
                i_device_num = -1
                for device in detected_devices:
                    i_device_num += 1
                    device = device.decode('utf-8')
                    add_to_test = 1
                    for mapping in self.mapping:
                        if mapping.search_string in device:
                            mapping.path = detected_paths[i_device_num]
                            mapping.dev_name = device
                            add_to_test = 0
                            
                    if add_to_test:
                        self.mapping.append( Mapping() )
                        self.mapping[-1].path = detected_paths[i_device_num]
                        self.mapping[-1].dev_name = device


                # commit the list of mappings to test
                self.tests = list(range(len(self.mapping)))

                # prepare for next test
                self.next_state = 'next-test'

            elif state == 'next-test':
                # init user data
                self.clear_user_data()
                
                # leave and go to next state if we are done here
                if len(self.tests) == 0:
                    self.next_state = 'commit'
                else:
                    # pop off an entry
                    test = self.tests.pop(0)
                    key = self.mapping[test].search_string
                    value = self.mapping[test].stream_name

                    # freeze user data
                    self.user['selected-search-string'] = self.mapping[test].search_string
                    self.user['selected-stream-name'] = self.mapping[test].stream_name
                    self.user['selected-device-name'] = self.mapping[test].dev_name
                    self.user['selected-path'] = self.mapping[test].path
                    self.current_test = test

                    # update state
                    self.next_state = 'modify-stream-info'
            
            elif state == 'modify-stream-info':
                self.process_entry()

                # next state
                self.next_state = 'next-test'

            elif state == 'commit':
                os.system('clear')
                self.update_mapping_file()
                self.next_state = 'exit'
            
            else:
                print('END OF PROGRAM')
                exit()


            
            #-#-#- update state variable -#-#-#
            self.state = self.next_state

    def update_mapping_file(self):
        hidden_mapping_file = os.path.join(CFG_DIR, '.mapping.cfg')
        mapping_file = os.path.join(CFG_DIR, 'mapping.cfg')

        # write the mapping file
        with open(hidden_mapping_file, 'w') as f:
            msg = []
            for mapping in self.mapping:
                if mapping.search_string is None:
                    continue

                msg.append( mapping.search_string + ' :: ' + mapping.stream_name )
            
            f.write('\n'.join(msg))

        # read the mapping file
        print("\nThis is your new mapping file:\n")
        print('--- mapping.cfg ----\n')
        with open(hidden_mapping_file, 'r') as f:
            for line in f:
                sys.stdout.write(line)
                sys.stdout.flush()

        print('\n--- END FILE ----')

        response = query('\nDo you like it? y/N').lower()

        if 'y' in response:
            os.system('mv %s %s' % (hidden_mapping_file, mapping_file))
            return 1
        else:
            os.system('rm %s' % (hidden_mapping_file))
            return 0

    def process_entry(self):
        q = 0; option = 0
        header = 'MODIFY STREAM %d/%d' % (self.current_test+1,len(self.mapping))
        iterations = 0
        while(q == 0):
            # print header
            if (iterations > 0) or (self.current_test > 0):
                os.system('clear')
            print('---------')
            print(header)

            # print device info
            msg = 'Source Device Name: %s' % (self.user['selected-device-name'])
            print(msg)
            msg = 'Filestream Path: %s' % (self.user['selected-path'])
            print(msg)
            msg = 'Stream Name: %s' % (self.user['selected-stream-name'])
            print(msg)
            msg = 'Device Search Str: %s' % (self.user['selected-search-string'])
            print(msg)
            print('')

            if option == 0:
                msg = \
                'Select an option\n'\
                '    1) Modify Stream Name\n'\
                '    2) Modify Search String\n'\
                '    3) Done/Proceed\n'\
                '    4) Delete this entry\n'\
                '    5) Quit this program'
                response = query(msg)

                if response == '1':
                    option = 1
                    
                elif response == '2':
                    option = 2
                elif response == '3':
                    option = 3
                elif response == '4':
                    option = 4
                elif response == '5':
                    exit()
                else:
                    option = 99

            elif option == 1:
                msg = \
                'What is the new name you would like to call this stream?'

                response = query(msg)
                if response is not '':
                    self.user['selected-stream-name'] = response
                option = 0
                
            elif option == 2:
                msg = 'What should the new search string be?'
                response = query(msg)

                if response is not '':
                    self.user['selected-search-string'] = response
                option = 0
            
            elif option == 3:
                test = self.current_test
                self.mapping[test].search_string = self.user['selected-search-string']
                self.mapping[test].stream_name = self.user['selected-stream-name']
                q = 1

            elif option == 4:
                self.user['selected-stream-name'] = None
                self.user['selected-search-string'] = None

                option = 0
                

            else:
                print('invalid option')
                time.sleep(0.5)
                print('returning back to main menu')
                time.sleep(1.0)

                option = 0

            iterations += 1


def main():
    wizard = Wizard()
    wizard.run()

main()