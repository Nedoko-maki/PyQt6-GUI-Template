# PyQt6-GUI-Template
A few convenience classes that speeds up the development of PyQt6 GUI applications.

To use:

1. make a main.py file and import gui.
2. make a class and inherit from MainWindowBase and initialise parent class (super().__init__()), and pass the file path for a gui config json file.
3. Add any widgets/settings in the json file and any methods you want to add in the child class.
4. Run with MainWindow.init_ui() and .show() methods. 
