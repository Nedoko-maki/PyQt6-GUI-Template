from gui import MainWindowBase
import PyQt5.QtWidgets as Widgets
import sys


class MainWindow(MainWindowBase):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def do_this(self):
        print("do that!")


def main():
    app = Widgets.QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
