import sys
import unittest

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget

from pygadmin.widgets.widget_icon_adder import IconAdder


class TestWidgetIconAdderMethods(unittest.TestCase):
    """
    Test the functionality of the widget icon adder.
    """

    def test_initial_attributes(self):
        """
        Test the initial attributes of the icon adder.
        """

        # Create an app, because this is necessary for testing a Qt elements.
        app = QApplication(sys.argv)
        # Create an icon adder.
        icon_adder = IconAdder()
        # The icon should be a QIcon.
        assert isinstance(icon_adder.window_icon, QIcon)

    def test_add_icon(self):
        """
        Test the method for adding an icon.
        """

        # Create an app, because this is necessary for testing a Qt elements.
        app = QApplication(sys.argv)
        # Create an icon adder.
        icon_adder = IconAdder()
        # Create a test widget.
        test_widget = QWidget()
        # Add an icon to the test widget.
        icon_adder.add_icon_to_widget(test_widget)
        # The name of the window icon of the test widget and of the icon adder should be the same.
        assert test_widget.windowIcon().name() == icon_adder.window_icon.name()
