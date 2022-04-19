import logging

import gui
import PyQt6.QtWidgets as Widgets
import sys


class MainWindow(gui.MainWindowBase):
    def __init__(self):
        super().__init__(config_filepath="gui_config.json")
        self.thread_manager = gui.ThreadManager()

    def do_this(self):
        self.thread_manager.add_thread(thread_name="square_thread", function=self.print_squares, args=(20,))
        self.thread_manager.start_thread("square_thread")

    def print_ans(self):
        self.print_log(self.thread_manager.wait_thread("square_thread"))

    @staticmethod
    def print_squares(n):
        ret = []
        for i in range(1, n+1):
            ret.append(i**2)

        return ret


def main():
    app = Widgets.QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
