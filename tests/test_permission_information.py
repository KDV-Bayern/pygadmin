import sys
import unittest

from PyQt5.QtWidgets import QApplication

from pygadmin.widgets.permission_information import PermissionInformationDialog
from pygadmin.models.treemodel import DatabaseNode, TableNode


class TestPermissionInformationMethods(unittest.TestCase):
    """
    Test the functionality and methods of node create information dialog.
    """

    def test_dialog_without_node(self):
        """
        Test the reaction of the dialog to the input of None instead of a node.
        """

        app = QApplication(sys.argv)
        permission_information_dialog = PermissionInformationDialog(None)
        assert permission_information_dialog.windowTitle() == "Node Input Error"

    def test_dialog_with_node(self):
        """
        Test the dialog with an existing node.
        """

        app = QApplication(sys.argv)
        database_node = DatabaseNode("testdb", "localhost", "testuser", "testdb", 5432, 10000)
        permission_information_dialog = PermissionInformationDialog(database_node)
        assert permission_information_dialog.selected_node == database_node
