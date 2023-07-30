import qasync
import sys
from PyQt6.QtWidgets import QMainWindow
import asyncio
import qdarktheme
from PyQt6 import QtWidgets

# 这里是自己写的库
from PyUi.Uilist import settings


class Ui_MainWindow(object):

    def setText_ui(self, MainWindow):
        self.ui = settings.ui_set(MainWindow, loop)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    # app.setStyleSheet(qdarktheme.load_stylesheet())
    app.setStyleSheet(qdarktheme.load_stylesheet("light"))
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    mainwindows = QMainWindow()
    with loop:
        ui = Ui_MainWindow()
        ui.setText_ui(mainwindows)
        mainwindows.show()
        loop.run_forever()
