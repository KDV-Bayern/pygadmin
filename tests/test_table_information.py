import sys
import unittest

from PyQt5.QtWidgets import QApplication

from pygadmin.widgets.table_information import TableInformationDialog
from pygadmin.models.treemodel import TableNode


class TestTableInformationDialogMethods(unittest.TestCase):
    """
    Test the functionality and methods of the table information dialog.
    """

    def test_dialog_without_node(self):
        """
        Test the dialog without a valid node and None instead.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a table information dialog with None as node, which is invalid.
        table_information_dialog = TableInformationDialog(None)

        # The window title of the widget should show an error.
        assert table_information_dialog.windowTitle() == "Node Input Error"

    def test_initial_attributes_with_node(self):
        """
        Test the initial attributes of the dialog with a valid table node.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Define a valid table node.
        table_node = TableNode("test", "localhost", "testuser", "testdb", 5432, 10000)
        # Create a table information dialog with the table node.
        table_information_dialog = TableInformationDialog(table_node)

        # The selected table node of the dialog should be the created table node.
        assert table_information_dialog.selected_table_node == table_node
        # The parameter for full definition is not filled, so it should use the default value True.
        assert table_information_dialog.full_definition is True
