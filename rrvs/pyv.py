import argparse
import sys
import pdb
import subprocess, signal
import os

ROOT_DIR = os.path.join(os.path.dirname(__file__), './')
#INCLUDE_DIR = os.path.join(ROOT_DIR, 'include')
#sys.path.append(INCLUDE_DIR)

def usage():
    msg = '''
    --> pyv cmd *args

    EXAMPLES:
     * pyv restart_server
     * pyv kill_server
     * pyv test_performance
     * pyv watch 0
     * pyv assign 0 front
     * pyv watch front
     * pyv list
    '''

    print(msg)

def get_pid(name):
    if type(name) is not bytes:
        name = bytes(name, 'utf-8')

    p = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
    out, err = p.communicate()
    pid = 0

    for line in out.splitlines():
        pname = b' '.join(line.split(None)[10:])

        if name in pname:
            pid = int(line.split(None)[1])
            break

    if pid > 0:
        return pid
    else:
        return None

def kill_if_running(name):
    if type(name) is not bytes:
        name = bytes(name, 'utf-8')

    # init
    process_killed = False


    # kill all instances of the process
    pid = get_pid(name)
    while pid is not None:
        os.kill(pid, signal.SIGKILL)
        pid = get_pid(name)
        process_killed = True

    
    return process_killed
    

    
def main():
    if len(sys.argv) < 2:
        print("not enough input arguments")
        exit()

    program = sys.argv[1]

    if program == 'restart_server':
        # kill the server if it's running
        killed = kill_if_running('server.py')

        # run the server. 
        os.system('python %s > /dev/null 2>&1 &' % os.path.join(ROOT_DIR,'server.py'))
        
        if killed:
            print("restarted the server")
        else:
            print("server started")


    elif program == 'kill_server':
        # kill the server if it's running
        killed = kill_if_running('server.py')

        if killed:
            print("killed the server")
        else:
            print("server already killed")

    elif program == 'test_camera':
        os.system('python %s' % os.path.join(ROOT_DIR, 'test_camera.py'))

    elif program == 'watch':
        if len(sys.argv) < 3:
            print("usage:\n\twatch <ip> <stream-name>\n\t\tor\n\twatch <idx>")
            exit()
        
        if len(sys.argv) == 4:
            ip = sys.argv[2]
            stream_name = sys.argv[3]
            os.system('python  %s %s %s' % (os.path.join(ROOT_DIR, 'utils/watch-stream.py'), ip, stream_name))
        elif len(sys.argv) == 3:
            idx = sys.argv[2]
            os.system('python  %s %s' % (os.path.join(ROOT_DIR, 'utils/test_camera.py'), idx))
        


    elif program == 'assign':
        os.system('python %s' % os.path.join(ROOT_DIR, 'utils/assign-cams.py') )



    else:
        usage()



if __name__ == '__main__':
    main()
