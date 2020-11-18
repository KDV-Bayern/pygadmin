import unittest
import signal
import sys

import faulthandler

from PyQt5.QtWidgets import QApplication

from pygadmin.widgets.main_window import MainWindow

faulthandler.enable()


class TestStartMethods(unittest.TestCase):
    """
    Test the correct start of the application.
    """

    def test_start(self):
        """
        Simulate the start of the application like in the main function in __init__.py, but without app.exec(), so a
        user does not have to end the application manually.
        """

        # Define easier ending of the application.
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        # Define an app.
        app = QApplication(sys.argv)
        # Create a main window.
        main_window = MainWindow()
        # Show the main window, but the application just ends.
        main_window.show()

    def test_start_multiple_times(self):
        """
        Simulate the start multiple times.
        """

        for i in range(500):
            print("Start test {}".format(i))
            self.test_start()
            print("Still alive")


if __name__ == "__main__":
    unittest.main()

