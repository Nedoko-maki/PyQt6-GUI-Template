import json
import logging
import queue
import threading
from pathlib import Path

import PyQt6.QtGui as QtGui
import PyQt6.QtWidgets as Widgets

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s',
    level=logging.INFO,
    datefmt='%H:%M:%S')


class _Widget:
    def __init__(self, attributes: dict):
        self.widget = getattr(Widgets, attributes["wgt_name"])
        self.args = attributes["args"]
        self.pos = attributes["pos"] + attributes["dim"]
        if "connect_function" in attributes:
            self.connecting_function = attributes["connect_function"]

    def __getitem__(self, item):
        return self.__dict__[item]

    def init_widget(self):
        self.widget = self.widget(*self.args)


class _WidgetsContainer:
    def __init__(self, widgets_dict: dict):
        for widget_name, widget_attrs in widgets_dict.items():
            setattr(self, widget_name, _Widget(widget_attrs))

    def __getitem__(self, item: str):

        if item not in self.__dict__:
            raise KeyError("Item not in WidgetContainer.")

        return self.__dict__[item]

    def __setitem__(self, key: str, value):
        self.__dict__[key] = value

    def __iter__(self):
        return self.__dict__.__iter__()

    def init_widgets(self):
        for widget_name in self.__dict__:  # tested briefly, only user made attrs are returned (?) (can't be sure...).
            getattr(self, widget_name).init_widget()


class ThreadManager:
    def __init__(self):
        """
        Basic thread managing class, adds new threads to a dictionary and only returns values if the return value is
        not None using the thread_wait() method.
        """

        self.threads = {}

    @staticmethod
    def _wrapper(function, args, kwargs, ret_queue):
        retval = function(*args, **kwargs)

        if retval is not None:
            ret_queue.put(retval)

    def add_thread(self,
                   thread_name: str | None,
                   function,
                   args: tuple = (),
                   kwargs: dict = None) -> None:

        if kwargs is None:
            kwargs = {}
            #  handling the case when kwargs is None (**kwargs).

        ret_queue = queue.Queue()
        thread = threading.Thread(target=self._wrapper, args=(function, args, kwargs, ret_queue), name=thread_name,
                                  daemon=True)

        self.threads[thread_name] = {"thread": thread, "queue": ret_queue}

    def start_thread(self, thread_name):
        try:
            self.threads[thread_name]["thread"].start()
        except KeyError as err:
            logging.error(f"{err}: there is no thread named '{thread_name}'.")
        except RuntimeError as err:
            logging.error(f"{err}.")

    def wait_thread(self, thread_name: str | None, blocking=True):
        if thread_name not in self.threads:
            raise KeyError(f"Thread '{thread_name}' not in ThreadManager!")

        retval = self.threads[thread_name]["queue"].get(block=blocking)
        del self.threads[thread_name]
        return retval


class MainWindowBase(Widgets.QMainWindow):
    def __init__(self, config_path: Path | str = None):
        super().__init__()

        self._config = self._load_config(config_path)
        self._layout = getattr(Widgets, self._config["layout"])()  # calling a function from a module by string name.
        # bad practice I think.
        self._window = Widgets.QWidget()
        self._log = str()

        self.widgets = _WidgetsContainer(self._config["widgets"])
        self.widgets.init_widgets()

        self.settings, self.filepath = None, None

    @staticmethod
    def _load_config(config_fp: Path):
        try:
            with open(config_fp) as json_file:
                config = json.load(json_file)
        except TypeError as e:
            logging.error(f"Wrong input type! {e}")
        except FileNotFoundError:
            logging.error(f"Could not find {config_fp.absolute()}!")
        except PermissionError:
            logging.error(f"Could not open {config_fp.absolute()}!")

        return config

    def _connect_button_widgets(self):
        for w_name in self.widgets:  # connecting buttons to respective functions.
            if isinstance(self.widgets[w_name].widget, (Widgets.QPushButton,)):

                if self.widgets[w_name]["connecting_function"] not in dir(self):  # I would've used self.__dict__, but
                    #  it was behaving oddly and not returning the child class' attributes.
                    raise NotImplementedError(
                        f"Connect function '{self.widgets[w_name]['connecting_function']}' "
                        f"for the button '{w_name}' does not exist.")

                self.widgets[w_name].widget.clicked.connect(
                    getattr(self, self.widgets[w_name]["connecting_function"]))

    def _centre_window(self):
        qtRectangle = Widgets.QWidget.frameGeometry(self)  # this code is to attempt to centre the window.
        centerPoint = QtGui.QGuiApplication.primaryScreen().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        window_position = (qtRectangle.topLeft().x(), qtRectangle.topLeft().y())  # up to here.
        self._window.setGeometry(*window_position, *self._config["window_size"])

    def _add_widgets(self):
        for w_name in self.widgets:
            if self.widgets[w_name]["pos"]:  # if pos is not empty, add the widget.
                self._layout.addWidget(self.widgets[w_name]["widget"], *self.widgets[w_name]["pos"])

    def init_ui(self):

        self._connect_button_widgets()
        self._window.setWindowTitle(self._config["window_name"])

        if self._config["window_icon"]:  # if window icon is written in config, set icon.
            self._window.setWindowIcon(self._config["window_icon"])

        self._centre_window()

        self.widgets["log"].widget.setLineWrapMode(Widgets.QTextEdit.LineWrapMode(0))

        self._add_widgets()

        self._window.setLayout(self._layout)

    def show(self):
        self._window.show()

    def log_print(self, text):
        self._log += str(text) + "\n"
        self.widgets["log"].widget.setText(self._log)

    def progress_update(self, percentage: int):
        self.widgets["progress_bar"].setValue(percentage)

    def file_dialog(self):
        self.filepath = Widgets.QFileDialog.getOpenFileName(self, 'Open file',
                                                            str(Path(Path.cwd())), "All files (.*)")
