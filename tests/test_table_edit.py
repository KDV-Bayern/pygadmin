import sys
import unittest

from PyQt5.QtWidgets import QApplication

from pygadmin.models.treemodel import TableNode
from pygadmin.widgets.table_edit import TableEditDialog
from pygadmin.configurator import global_app_configurator


class TestTableEditDialogMethods(unittest.TestCase):
    """
    Test the basic methods and the behavior of the table edit dialog.
    """

    def test_dialog_without_node(self):
        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)

        # Add None instead of a node to the dialog.
        table_edit_dialog = TableEditDialog(None)
        # The window title of the dialog should be a string with an error.
        assert table_edit_dialog.windowTitle() == "Node Input Error"

    def test_initial_attributes(self):
        """
        Test the existence of some relevant attributes of the dialog.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)

        # Create an existing and valid table node for testing.
        table_node = TableNode("test", "localhost", "testuser", "testdb", 5432, 10000)

        # Add the table node to the dialog.
        table_edit_dialog = TableEditDialog(table_node)

        # The selected table node should be the used table node.
        assert table_edit_dialog.selected_table_node == table_node
        # The database connection of the dialog should be the connection of the table node.
        assert table_edit_dialog.database_connection == table_node._database_connection

    def test_checkbox_initialization(self):
        """
        Test the correct initialization of the checkbox.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)

        # Create an existing and valid table node for testing.
        table_node = TableNode("test", "localhost", "testuser", "testdb", 5432, 10000)

        # Add the table node to the dialog.
        table_edit_dialog = TableEditDialog(table_node)

        # Get the current configuration of the checkbox.
        checkbox_configuration = global_app_configurator.get_single_configuration(
            table_edit_dialog.checkbox_configuration_name)

        # If the configuration is True, the checkbox should be checked.
        if checkbox_configuration is True:
            assert table_edit_dialog.update_immediately_checkbox.isChecked() is True

        # If the configuration is False or None, the checkbox should not be checked.
        else:
            assert table_edit_dialog.update_immediately_checkbox.isChecked() is False

    def test_get_select_query(self):
        """
        Test the function for getting the select query with an empty condition in the condition line edit and with a
        text in the line edit.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)

        # Create an existing and valid table node for testing.
        table_node = TableNode("test", "localhost", "testuser", "testdb", 5432, 10000)

        # Add the table node to the dialog.
        table_edit_dialog = TableEditDialog(table_node)

        # The current select query should contain a statement for selecting all values with limit 1000 in the given
        # table.
        assert table_edit_dialog.get_select_query() == "SELECT * FROM {} LIMIT 1000".format(
            table_edit_dialog.selected_table_node.name)

        # Define a where condition for further testing.
        test_where_condition = "test_column='test_value'"
        # Set the where condition in the line edit.l
        table_edit_dialog.condition_line_edit.setText(test_where_condition)

        # The current select query should contain the where condition in addition to the previous select query.
        assert table_edit_dialog.get_select_query() == "SELECT * FROM {} WHERE {} LIMIT 1000".format(
            table_edit_dialog.selected_table_node.name, test_where_condition)

    def test_update_statement(self):
        """
        Test the current state of the update label, which contains the update query.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)

        # Create an existing and valid table node for testing.
        table_node = TableNode("test", "localhost", "testuser", "testdb", 5432, 10000)

        # Add the table node to the dialog.
        table_edit_dialog = TableEditDialog(table_node)

        # The update label contains the update statement. Without changing a value in the table, the label contains
        # just an UPDATE with the name of the table.
        assert table_edit_dialog.update_label.text() == "UPDATE {}".format(table_edit_dialog.selected_table_node.name)

    def test_checkbox_change(self):
        """
        Test the check changes in the checkbox for updating the table immediately.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)

        # Create an existing and valid table node for testing.
        table_node = TableNode("test", "localhost", "testuser", "testdb", 5432, 10000)

        # Add the table node to the dialog.
        table_edit_dialog = TableEditDialog(table_node)

        # Set the checkbox to checked.
        table_edit_dialog.update_immediately_checkbox.setChecked(True)

        # The update elements should be invisible now.
        assert table_edit_dialog.update_label.isVisible() is False
        assert table_edit_dialog.update_button.isVisible() is False

        # Set the checkbox to unchecked.
        table_edit_dialog.update_immediately_checkbox.setChecked(False)

        # The update elements should be visible now.
        assert table_edit_dialog.update_label.isVisible() is True
        assert table_edit_dialog.update_button.isVisible() is True



