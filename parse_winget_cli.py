import json
import subprocess as sbp
import re

from PyQt5 import QtCore


class WinGet(QtCore.QObject):
    running = False
    data_loaded = QtCore.pyqtSignal(list)
    log_message = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()
    load_spinner = QtCore.pyqtSignal(bool)

    @QtCore.pyqtSlot(str)
    def load_list(self, cmd: str) -> None:
        self.load_spinner.emit(True)
        ignore_mode = False
        if cmd == 'ignore_list':
            cmd = 'upgrade'
            ignore_mode = True
        result = str(sbp.run(f'winget {cmd}', stdout=sbp.PIPE, shell=True)
                     .stdout, encoding='utf-8').split('\r\n')
        header = result[0]
        columns = []
        match = re.finditer(r'(\w+)', header)
        for i in match:
            if len(columns) > 0:
                columns[-1][2] = i.start()
            columns.append([i.group(), i.start(), 0])

        columns[-1][2] += len(header)
        columns = list(map(
            lambda c: (c[0], c[1] - columns[0][1], c[2] - columns[0][1]), columns
        ))
        lines = result[2:-1]

        with open('ignore_list.json', 'r', encoding='UTF-8') as f:
            ignore_list = json.load(f)
        apps = []
        for line in lines:
            app = dict()
            for col in columns:
                app[col[0]] = re.sub(r'\s{2,}', '', line[col[1]:col[2]])
            if ignore_mode:
                if app['Id'] in ignore_list:
                    apps.append(app)
            else:
                if app['Id'] not in ignore_list:
                    apps.append(app)
        self.load_spinner.emit(False)
        self.data_loaded.emit(apps)

    @QtCore.pyqtSlot(list)
    def upgrade(self, apps: list[str]) -> None:
        for app in apps:
            self.log_message.emit(f"Starting upgrade {app}")
            sbp.run(f'winget upgrade {app}', shell=True)
            self.log_message.emit(f"Upgraded {app}\n")
        self.log_message.emit("\nAll Upgrades Done!!!")
        self.load_list('upgrade')

    @QtCore.pyqtSlot(list, str)
    def change_ignore(self, apps: list[str], mode: str) -> None:
        with open('ignore_list.json', 'r', encoding='UTF-8') as f:
            ignore_list = json.load(f)
        if mode == 'add':
            ignore_list.extend(apps)
        else:
            for app in apps:
                ignore_list.remove(app)
        with open('ignore_list.json', 'w', encoding='UTF-8') as f:
            json.dump(ignore_list, f)

        if mode == 'add':
            self.log_message.emit(f'Added to ignore list: {", ".join(apps)}')
            self.load_list('upgrade')
        else:
            self.log_message.emit(f'Deleted from ignore list: {", ".join(apps)}')
            self.load_list('ignore_list')

    @QtCore.pyqtSlot(list)
    def uninstall(self, apps: list[str]) -> None:
        for app in apps:
            self.log_message.emit(f"Starting uninstall {app}")
            sbp.run(f'winget uninstall {app}', shell=True)
            self.log_message.emit(f"Uninstalled {app}\n")
        self.log_message.emit("\nAll Removes Done!!!")
        self.load_list('upgrade')
