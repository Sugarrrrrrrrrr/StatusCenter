import threading
from parse import mavutil

class LinkInterface(threading.Thread):
    def __init__(self, link_name):
        super().__init__()
        self.link_name = link_name

        # link_name = 10.168.103.72:14550
        # mav = mavutil.mavlink_connection('network:10.168.103.0', ip_list=['10.168.103.72'], port=53)

        self.start()

    def run(self):
        pass
