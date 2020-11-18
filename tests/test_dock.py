import sys
import unittest

from PyQt5.QtWidgets import QApplication

from pygadmin.widgets.dock import DockWidget
from pygadmin.widgets.tree import TreeWidget


class TestDockWidgetMethods(unittest.TestCase):
    """
    Test the basic functionality of the dock widget.
    """

    def test_initial_attributes(self):
        """
        Test the initial attributes of the dock.
        """
        
        # Create an app, because this is necessary for testing a QWidget.
        app = QApplication(sys.argv)
        # Create a dock widget.
        dock_widget = DockWidget()
        # The tree of the dock widget should be a TreeWidget
        assert isinstance(dock_widget.tree, TreeWidget)

