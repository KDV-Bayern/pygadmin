from PyQt5.QtWidgets import QProgressBar, QGridLayout, QLabel, QDialog
from PyQt5.QtCore import QBasicTimer, pyqtSlot

from pygadmin.connectionstore import global_connection_store
from pygadmin.widgets.widget_icon_adder import IconAdder


class StartProgressDialog(QDialog):
    """
    Create a dialog for the start of the application. The dialog shows the current progress of the loaded server nodes
    in the tree.
    """

    def __init__(self):
        """
        Initialize the user interface and the grid layout.
        """

        super().__init__()
        # Set the dialog modal, so until the start process is not done, the dialog is the primary widget.
        self.setModal(True)
        # Add the pygadmin icon as window icon.
        icon_adder = IconAdder()
        icon_adder.add_icon_to_widget(self)
        self.init_ui()
        self.init_grid()

    def init_ui(self):
        """
        Initialize the user interface.
        """

        # Set the size of the dialog.
        self.resize(400, 100)
        # Create a progress bar.
        self.progress_bar = QProgressBar(self)
        # Set the minimum size of the progress bar.
        self.progress_bar.setMinimumSize(300, 20)
        # Add a description label for describing the current process.
        self.description_label = QLabel("Pygadmin is currently starting and is loading the server nodes.")

        # Create a timer as required component for the progress bar.
        self.timer = QBasicTimer()

        # Set the current step to 0, so the bar shows 0% at the beginning.
        self.step = 0

        # Start the progress bar.
        self.start_progress_bar()

        self.setWindowTitle("Starting pygadmin...")
        self.show()

    def init_grid(self):
        """
        Initialize the grid layout.
        """

        grid_layout = QGridLayout(self)
        grid_layout.addWidget(self.description_label, 0, 0)
        grid_layout.addWidget(self.progress_bar, 1, 0)
        grid_layout.setSpacing(10)
        self.setLayout(grid_layout)

    def start_progress_bar(self):
        """
        Start the progress bar: Get the initial parameters for choosing a step size, based on the number of connections
        in the connection store, and start the timer.
        """

        # Load all current connection parameters in the yaml file.
        global_connection_store.get_connection_parameters_from_yaml_file()
        # Get the number of all current connection parameters.
        self.connection_number = global_connection_store.get_number_of_connection_parameters()

        # Set the maximum of the progress bar as current connection number.
        self.progress_bar.setMaximum(self.connection_number)

        # Set the step size as 1/n-th of the connection number, which is realized by setting the step size to 1, while
        # the maximum is the connection number.
        self.step_size = 1

        # Start the timer.
        self.timer.start(100, self)

    def timerEvent(self, event):
        """
        Implement the method for a timer event: If the timer reaches 100% (or above), stop the timer and abort the
        dialog.
        """

        # Check for 100% or more.
        if self.step >= self.connection_number:
            # Stop the timer.
            self.timer.stop()
            # Close the dialog, so the application can start smoothly.
            self.close()

    @pyqtSlot(bool)
    def get_new_step_size(self):
        """
        Increment the step size by signal.
        """

        # Add a new 1/n-th to the current float step, while the step size is actually 1, but the maximum is the
        # connection number
        self.step += self.step_size
        # Set the value as integer to the progress bar.
        self.progress_bar.setValue(self.step)

