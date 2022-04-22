import sys
import PyQt6.QtWidgets as Widgets
import gui


class MainWindow(gui.MainWindowBase):
    def __init__(self):
        super().__init__(config_path="gui_config.json")
        self.init_ui()  # I could hide these method calls in the parent class, but I think having the flexibility of
        # initialising the object at different times is nice.
        self.show()
        self.thread_manager = gui.ThreadManager()

    def do_this(self):
        self.thread_manager.add_thread(thread_name="square_thread", function=self.print_squares, args=(20,))
        self.thread_manager.start_thread("square_thread")

    def print_ans(self):
        self.log_print(self.thread_manager.wait_thread("square_thread"))

    @staticmethod
    def print_squares(n):
        return [i ** 2 for i in range(1, n + 1)]


def main():
    app = Widgets.QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
