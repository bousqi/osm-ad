import sys

from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QSplashScreen

from package.api.config import AppConfig
from package.main_window import MainWindow

GUI_VERSION = "1.0.6"

sys._excepthook = sys.excepthook
def exception_hook(exctype, value, traceback):
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)
sys.excepthook = exception_hook


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # splashscreen
    pixmap = QPixmap(":/img/resources/base/maps.png").scaledToWidth(384, QtCore.Qt.SmoothTransformation)
    splash = QSplashScreen(pixmap)
    splash.show()

    # loading config
    AppConfig.load()

    # Creating main window
    ex = MainWindow(app)
    ex.show()
    splash.finish(ex)

    sys.exit(app.exec_())
