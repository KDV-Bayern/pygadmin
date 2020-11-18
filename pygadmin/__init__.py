import signal
import sys
import os

from PyQt5.QtWidgets import QApplication

from pygadmin.logger import setup_logging_configuration
from pygadmin.widgets.main_window import MainWindow

__version__ = '0a0'


def main():
    """
    Define a function, which describes the main part of the program, so every part is executed.
    """

    # Define the path of the configuration file os independent.
    configuration_path = os.path.join(os.path.dirname(__file__), "logging.yaml")
    # Get the logging configuration.
    setup_logging_configuration(configuration_file_path=configuration_path)
    # Enable a possibility for easy handling to end the program.
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    # Activate the program as QApplication.
    app = QApplication(sys.argv)
    # Use the main window as central element of the application and the user interface.
    main_window = MainWindow()
    # Execute the application.
    sys.exit(app.exec())
