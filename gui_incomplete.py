import json
import sys
import traceback
import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as Widgets
from pathlib import Path


# NOT WORKING SINCE MEMBER CONTAINER NEEDS TO BE ITERABLE!


def parse_args(args):
    out = list()
    for arg in args:
        if arg.startswith("var:"):
            out.append(locals()[arg[len("var:"):]])
        elif arg.startswith("wfunc:"):
            out.append(getattr(Widgets, arg[len("wfunc:"):])())
        else:
            out.append(arg)
    return out


class MainWindow(Widgets.QMainWindow):
    def __init__(self, worker_function):
        super().__init__()
        self.worker_function = worker_function

        try:
            with open("gui_config.json") as json_file:
                self.config = json.load(json_file)
        except FileNotFoundError:
            print("gui_config.json file missing!")
            exit()
        except PermissionError:
            print("Could not open gui_config.json!")
            exit()

        self.layout = getattr(Widgets, self.config["layout"])()  # calling a function from a module by string name.
        self.window = Widgets.QWidget()
        self.log = str()

        self.widgets = MemberContainer(self.config["widgets"], exclude_level=[0])

        for widget_name in self.widgets:  # takes widgets from config and calls them and keeps them in a dict.
            self.widgets[widget_name].wgt = \
                getattr(Widgets, self.widgets[widget_name].wgt_name)(*parse_args(self.widgets[widget_name].args))
            self.widgets[widget_name].pos += self.widgets[widget_name].dim

        # {k: {"wgt": getattr(Widgets, v["w_name"])(*parse_args(v["args"])),
        #      "pos": v["pos"] + v["dim"]} for (k, v) in self.config["widgets"].items()
        #  }
        # self.widget_pos = {k: v["pos"] + v["dim"] for (k, v) in self.config["widgets"].items()}

        self.thread, self.worker = None, None
        self.settings, self.filepath = None, None
        self.worker_running = False

        self.init_ui()

    def init_ui(self):
        # Connect signal to our methods.

        # self.widgets["button_confirm"].clicked.connect(self.button_confirm_pressed)
        # self.widgets["button_browse"].clicked.connect(self.button_browse_pressed)

        for w_name in self.widgets:
            if self.widgets[w_name].wgt_name in ["QPushButton"]:
                self.widgets[w_name]["wgt"].clicked.connect(
                    getattr(self, self.widgets[w_name].connect_function))

        self.window.setWindowTitle(self.config["window_name"])

        if self.config["window_icon"]:  # if window icon is written in config, set icon.
            self.window.setWindowIcon(self.config["window_icon"])

        qtRectangle = Widgets.QWidget.frameGeometry(self)  # this code is to attempt to centre the window.
        centerPoint = Widgets.QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        window_position = (qtRectangle.topLeft().x(), qtRectangle.topLeft().y())  # up to here.
        self.window.setGeometry(*window_position, *self.config["window_size"])

        self.widgets["example_textlog"].wgt.setLineWrapMode(Widgets.QTextEdit.NoWrap)

        for w_name in self.widgets:
            if self.widgets[w_name]["pos"]:  # if pos is not empty, add the widget.
                self.layout.addWidget(self.widgets[w_name].wgt, *self.widgets[w_name].pos)

        self.window.setLayout(self.layout)
        self.window.show()

    def print_log(self, text):
        self.log += str(text) + "\n"
        self.widgets["example_textlog"]["wgt"].setText(self.log)

    def progress_update(self, percentage: int):
        self.widgets["progress_bar"].setValue(percentage)

    def file_dialog(self):
        self.filepath = Widgets.QFileDialog.getOpenFileName(self, 'Open file',
                                                            str(Path(Path.cwd())), "All files (.*)")
        # self.widgets["textbox_file"].setText(self.filepath[0])

    def example_button_press(self):
        self.print_log("example button pressed!")

    def run_worker(self):
        if not self.worker_running:
            self.log = str()  # clearing log
            self.widgets["example_textlog"].wgt.setText(self.log)

            try:
                self.settings = ()  # pass any arguments into the worker function here.
                self._run_worker()

            except ValueError:
                self.print_log("Invalid input!\n")
                self.print_log(traceback.format_exc())

        else:
            self.print_log("Still running child process!")

    def _run_worker(self):
        self.thread = QtCore.QThread()
        self.worker = Worker(self.worker_function, self.settings)

        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.worker_status)
        self.worker.progress_update.connect(self.progress_update)
        self.worker.log_update.connect(self.print_log)
        self.thread.start()

        self.worker_status()

    def worker_status(self):
        self.worker_running = False if self.worker_running else True


class Worker(QtCore.QObject):
    finished = QtCore.pyqtSignal()  # signalling code for signalling to mother process of GUI.
    progress_update = QtCore.pyqtSignal(int)
    log_update = QtCore.pyqtSignal(str)

    def __init__(self, worker_function, settings):
        super().__init__()
        self.worker_function = worker_function
        self.settings = settings

    def run(self):
        pyqt_signal_dict = {"progress_bar": self.progress_update,
                            "text_log": self.log_update}

        self.worker_function(self.settings)

        self.log_update.emit("Finished!")
        self.finished.emit()


class MemberContainer:
    def __init__(self, input_dict: dict, exclude_level: list = None, current_level: int = 0):

        self._dict = {k: v for (k, v) in input_dict.items() if type(v) != dict and current_level in exclude_level}

        for (key, val) in input_dict.items():
            if type(val) == dict:
                val = MemberContainer(val, exclude_level=exclude_level, current_level=current_level + 1)

            if current_level not in exclude_level and key not in self._dict.keys():
                self.__setattr__(key, val)
            else:
                self._dict[key] = val

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, val):
        self._dict[key] = val

    def __delitem__(self, key):
        del self._dict[key]

    def __len__(self):
        return len(self.__dict__) - 1  # -1 for _dict

    def __str__(self):
        return str(
            [{key: value} if type(self.__dict__[key]) != type(self) else {key: value.__str__()} for (key, value) in
             self.__dict__.items()])


def init(worker_function):
    app = Widgets.QApplication(sys.argv)
    w = MainWindow(worker_function)
    sys.exit(app.exec_())
