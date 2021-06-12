import sys

from PyQt5.QtCore import Qt
from parse_winget_cli import WinGet
from PyQt5 import QtWidgets, QtCore
from main_form import Ui_WinGetGui


class MyWindow(QtWidgets.QMainWindow, QtCore.QObject):
    upgrade_apps = QtCore.pyqtSignal(list)
    remove_apps = QtCore.pyqtSignal(list)
    add_to_ignore = QtCore.pyqtSignal(list)

    def __init__(self):
        super(MyWindow, self).__init__()
        self.ui = Ui_WinGetGui()
        self.ui.setupUi(self)
        self.show()
        # настройка интерфейса

        # запуск загрузки в новом потоке
        self.thread = QtCore.QThread()
        self.winget_cmd = WinGet()
        self.winget_cmd.moveToThread(self.thread)
        self.winget_cmd.data_loaded.connect(self.refresh_list)
        self.winget_cmd.finished.connect(self.quit_thread)
        self.winget_cmd.log_message.connect(self.print_log)
        self.thread.started.connect(self.winget_cmd.load_updates)
        self.thread.start()
        # привязка слотов
        self.upgrade_apps.connect(self.winget_cmd.upgrade)
        self.remove_apps.connect(self.winget_cmd.uninstall)
        self.add_to_ignore.connect(self.winget_cmd.add_to_ignore)
        # настройка кнопок
        self.ui.pb_refresh.clicked.connect(self.winget_cmd.load_updates)
        self.ui.pb_update.clicked.connect(self.upgrade_apps_fn)
        self.ui.pb_remove.clicked.connect(self.remove_apps_fn)
        self.ui.pb_add_to_ignore.clicked.connect(self.add_to_ignore_fn)

    def add_to_ignore_fn(self):
        apps = []
        for i in range(self.ui.tableWidget.rowCount()):
            if self.ui.tableWidget.item(i, 0).checkState():
                apps.append(self.ui.tableWidget.item(i, 0).text())
        self.add_to_ignore.emit(apps)

    def upgrade_apps_fn(self):
        apps = []
        for i in range(self.ui.tableWidget.rowCount()):
            if self.ui.tableWidget.item(i, 0).checkState():
                apps.append(self.ui.tableWidget.item(i, 0).text())
        self.upgrade_apps.emit(apps)

    def remove_apps_fn(self):
        apps = []
        for i in range(self.ui.tableWidget.rowCount()):
            if self.ui.tableWidget.item(i, 0).checkState():
                apps.append(self.ui.tableWidget.item(i, 0).text())
        self.remove_apps.emit(apps)

    @QtCore.pyqtSlot()
    def quit_thread(self):
        self.thread.quit()

    @QtCore.pyqtSlot(str)
    def print_log(self, text: str):
        self.ui.textBrowser.append(text)

    @QtCore.pyqtSlot(list)
    def refresh_list(self, packages: list):
        self.ui.tableWidget.setRowCount(0)
        for i, package in enumerate(packages):
            pack = QtWidgets.QTableWidgetItem(package['Id'])
            pack.setCheckState(Qt.Unchecked)
            self.ui.tableWidget.setRowCount(self.ui.tableWidget.rowCount() + 1)
            self.ui.tableWidget.setItem(i, 0, pack)
            self.ui.tableWidget.setItem(i, 1, QtWidgets.QTableWidgetItem(package['Name']))
            self.ui.tableWidget.setItem(i, 2, QtWidgets.QTableWidgetItem(package['Version']))
            self.ui.tableWidget.setItem(i, 3, QtWidgets.QTableWidgetItem(package['Available']))
        self.ui.tableWidget.resizeColumnsToContents()


def start_ui():
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    app.aboutToQuit.connect(window.thread.quit)
    sys.exit(app.exec())


if __name__ == '__main__':
    start_ui()
