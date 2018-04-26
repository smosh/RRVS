import os
import sys

ROOT_DIR = os.path.join(os.path.dirname(__file__), '../')

sys.path.append(ROOT_DIR)
from client import Client

def main():
    if len(sys.argv) < 3:
        print('usage:\n\tclient.py <ip> <stream_name>')
        exit()
    ip = sys.argv[1]
    stream_name = sys.argv[2]



    client = Client()
    client.attach_IP(ip)
    client.attach_stream(stream_name)
    client.enable_gui(True)
    client.run()

main()