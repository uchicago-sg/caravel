import threading
import time
import urllib
import re

EXIT_NODES_URL = "https://check.torproject.org/exit-addresses"

class TorDetector(object):
    def __init__(self):
        """
        Initializes this Tor detector object.
        """

        self.lock = threading.Lock()
        self.exit_nodes = []
        self.last_update = None

    def _update(self):
        """
        Updates the list of Tor exit nodes from the Tor project.
        """

        if not self.last_update or (time.time() - self.last_update) > 3600:
            data = urllib.urlopen(EXIT_NODES_URL).read()
            matches = re.finditer(r'ExitAddress ([^ ]+)', data)

            self.exit_nodes = set([x.group(1) for x in matches])
            self.last_update = time.time()

    def is_tor_exit_node(self, ip_address):
        """
        Returns True if the given IP address is a Tor exit node.
        """

        with self.lock:
            self._update()
            return ip_address in self.exit_nodes
