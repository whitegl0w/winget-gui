import sys

from PyQt5.QtCore import Qt
from waitingspinnerwidget import QtWaitingSpinner

from parse_winget_cli import WinGet
from PyQt5 import QtWidgets, QtCore
from main_form import Ui_WinGetGui


class MyWindow(QtWidgets.QMainWindow, QtCore.QObject):
    upgrade_apps = QtCore.pyqtSignal(list)
    remove_apps = QtCore.pyqtSignal(list)
    change_ignore = QtCore.pyqtSignal(list, str)
    load_app_list = QtCore.pyqtSignal(str)

    def __init__(self):
        super(MyWindow, self).__init__()
        self.ui = Ui_WinGetGui()
        self.ui.setupUi(self)
        # загрузка таблицы стилей
        with open('Ubuntu.qss', 'r') as f:
            self.setStyleSheet(f.read())
        # настройка интерфейса
        self.spinner = QtWaitingSpinner(self)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.spinner)
        self.ui.tableWidget.setLayout(layout)
        self.mode = 'upgrade'
        self.ui.rb_updates.setChecked(True)
        # запуск загрузки в новом потоке
        self.thread = QtCore.QThread()
        self.winget_cmd = WinGet()
        self.winget_cmd.moveToThread(self.thread)
        self.winget_cmd.data_loaded.connect(self.refresh_list)
        self.winget_cmd.finished.connect(self.quit_thread)
        self.winget_cmd.log_message.connect(self.print_log)
        self.winget_cmd.load_spinner.connect(self.load_spinner)
        self.thread.started.connect(lambda: self.load_app_list.emit(self.mode))
        self.thread.start()
        # привязка слотов
        self.upgrade_apps.connect(self.winget_cmd.upgrade)
        self.remove_apps.connect(self.winget_cmd.uninstall)
        self.change_ignore.connect(self.winget_cmd.change_ignore)
        self.load_app_list.connect(self.winget_cmd.load_list)
        # настройка кнопок
        self.ui.pb_refresh.clicked.connect(lambda: self.load_app_list.emit(self.mode))
        self.ui.pb_update.clicked.connect(self.upgrade_apps_fn)
        self.ui.pb_remove.clicked.connect(self.remove_apps_fn)
        self.ui.pb_add_to_ignore.clicked.connect(self.add_to_ignore_fn)
        self.ui.rb_ignore_list.clicked.connect(self.change_mode)
        self.ui.rb_installed.clicked.connect(self.change_mode)
        self.ui.rb_updates.clicked.connect(self.change_mode)
        # отображение окна
        self.show()

    def change_mode(self):
        self.ui.pb_add_to_ignore.setText('Add to ignore list')
        self.ui.pb_add_to_ignore.setEnabled(True)
        if self.ui.rb_updates.isChecked():
            self.mode = 'upgrade'
        elif self.ui.rb_installed.isChecked():
            self.mode = 'list'
            self.ui.pb_add_to_ignore.setEnabled(False)
        elif self.ui.rb_ignore_list.isChecked():
            self.mode = 'ignore_list'
            self.ui.pb_add_to_ignore.setText('Delete from ignore list')
        self.load_app_list.emit(self.mode)

    def add_to_ignore_fn(self):
        apps = []
        for i in range(self.ui.tableWidget.rowCount()):
            if self.ui.tableWidget.item(i, 0).checkState():
                apps.append(self.ui.tableWidget.item(i, 0).text())
        if self.mode == 'ignore_list':
            self.change_ignore.emit(apps, 'delete')
        else:
            self.change_ignore.emit(apps, 'add')

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

    @QtCore.pyqtSlot(bool)
    def load_spinner(self, status: bool):
        if status:
            self.ui.tableWidget.setRowCount(0)
            self.spinner.start()
        else:
            self.ui.horizontalLayout.setEnabled(True)
            self.spinner.stop()

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
