from PyQt5.QtWidgets import QDialog, QLabel, QGridLayout
import pygadmin
from pygadmin.widgets.widget_icon_adder import IconAdder


class VersionInformationDialog(QDialog):
    """
    Create a dialog for showing the current version of pygadmin.
    """

    def __init__(self):
        """
        Use the methods for initializing the dialog.
        """

        super().__init__()
        # Add the pygadmin icon as window icon.
        icon_adder = IconAdder()
        icon_adder.add_icon_to_widget(self)
        self.init_ui()
        self.init_grid()

    def init_ui(self):
        """
        Create a user interface.
        """

        # Create a label for showing the current version.
        self.version_label = QLabel()
        # Set the current version to the label.
        self.set_version_to_label()
        self.setMaximumSize(200, 60)
        self.setWindowTitle("Current Version")
        self.show()

    def init_grid(self):
        """
        Create a grid layout.
        """

        grid_layout = QGridLayout(self)
        grid_layout.addWidget(self.version_label, 0, 0)
        grid_layout.setSpacing(10)
        self.setLayout(grid_layout)

    def set_version_to_label(self):
        """
        Set the current version of pygadmin as label text.
        """

        self.version_label.setText("You are currently using version {} of pygadmin.".format(pygadmin.__version__))
