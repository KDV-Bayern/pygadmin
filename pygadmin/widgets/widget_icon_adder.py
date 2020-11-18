import logging
import os

from PyQt5.QtGui import QIcon, QPixmap

import pygadmin


class IconAdder:
    """
    Create a class for adding the pygadmin icon as window icon for the given widget.
    """

    def __init__(self):
        """
        Define the icon path and get the icon.
        """

        # Define the icon path. The pygadmin icon can be found in this path.
        icon_path = os.path.join(os.path.dirname(pygadmin.__file__), "icons", "pygadmin.svg")

        # Check for the existence of the path.
        if os.path.exists(icon_path):
            # Create a QIcon as window icon.
            self.window_icon = QIcon()
            # Add the pygadmin logo as pixmap to the icon.
            self.window_icon.addPixmap(QPixmap(icon_path))

        # Define a behavior for a missing path.
        else:
            # Set the window icon to an empty icon.
            self.window_icon = QIcon()
            # Show a warning.
            logging.warning("The window icon could not be found in {}".format(icon_path))

    def add_icon_to_widget(self, widget):
        """
        Get a widget and add the pygadmin icon as window icon.
        """

        # Set the icon as window icon.
        widget.setWindowIcon(self.window_icon)
