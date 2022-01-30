from PyQt5.QtWidgets import QApplication
from gui.osmm_main import gui_main
import sys

"""
URLS to help :
 - https://realpython.com/python-pyqt-qthread/
 - https://realpython.com/python-menus-toolbars/#adding-widgets-to-a-toolbar
"""

sys._excepthook = sys.excepthook
def exception_hook(exctype, value, traceback):
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)
sys.excepthook = exception_hook

if __name__ == "__main__":
    app = QApplication(sys.argv)

    ex = gui_main()
    ex.show()
    sys.exit(app.exec_())
