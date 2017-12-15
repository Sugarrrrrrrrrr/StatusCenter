from scToolbox import scToolbox
from comm.LinkInterface import LinkInterface


class LinkManager(scToolbox):
    def __init__(self, app, parent):
        super().__init__(app, parent)

        self.links_name = []
        self.links = []

        self.update_links_name()

        for link_name in self.links_name:
            link = LinkInterface(link_name)
            self.links.append(link)

    def update_links_name(self):
        self.links_name.append("10.168.103.72:14550")


