from PyQt5.QtWidgets import QApplication
from osmm_gui import *
import sys

sys._excepthook = sys.excepthook
def exception_hook(exctype, value, traceback):
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)
sys.excepthook = exception_hook

if __name__ == "__main__":
    app = QApplication(sys.argv)

    ex = osmm_gui()
    ex.show()
    sys.exit(app.exec_())
