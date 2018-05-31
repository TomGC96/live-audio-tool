from clipper import Clipper
from recorder import Recorder
from ui import UI

from PyQt5.QtWidgets import QApplication

import sys
import time


def main():
    # Load recorder config from file and update displayed status on UI
    recr = Recorder()
    recr.read_config()
    recr.update_status()

    # Load clipper config from file and update displayed status on UI
    clpr = Clipper()
    clpr.read_config()
    clpr.update_status()

    app = QApplication(sys.argv)
    app.setApplicationName('Live Audio Tool')
    app.setApplicationDisplayName('Live Audio Tool')

    ex = UI(clpr, recr)
    ex.show()
    app.exec_()

    # Ensure recorder is stopped
    recr.is_recording = False

    # Wait to ensure all clip exports are finished
    time.sleep(clpr.post_buffer)

    sys.exit()


if __name__ == "__main__":
    main()
