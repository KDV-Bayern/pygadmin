import sys
import unittest

from PyQt5.QtWidgets import QApplication

from pygadmin.widgets.node_create_information import NodeCreateInformationDialog
from pygadmin.models.treemodel import DatabaseNode, TableNode, ViewNode


class TestNodeCreateInformationMethods(unittest.TestCase):
    """
    Test the functionality and methods of node create information dialog.
    """

    def test_dialog_without_node(self):
        """
        Test the reaction of the dialog to the input of None instead of a node.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create an information dialog without a node.
        node_information_dialog = NodeCreateInformationDialog(None)

        # The window title should assume an error.
        assert node_information_dialog.windowTitle() == "Node Input Error"

    def test_dialog_with_valid_database_node(self):
        """
        Test the node information dialog with a database node.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a database node for the dialog.
        database_node = DatabaseNode("testdb", "localhost", "testuser", "testdb", 5432, 10000)
        # Create an information dialog with the database node.
        node_information_dialog = NodeCreateInformationDialog(database_node)
        # The selected node should be the database node.
        assert node_information_dialog.selected_node == database_node

        # Get the create statement of the node.
        create_statement = node_information_dialog.get_node_create_statement()
        self.check_create_statement(create_statement)

    def test_dialog_with_valid_table_node(self):
        """
        Test the node information dialog with a table node.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a table node for the dialog.
        table_node = TableNode("test", "localhost", "testuser", "testdb", 5432, 10000)
        # Create an information dialog with the table node.
        node_information_dialog = NodeCreateInformationDialog(table_node)
        # The selected node should be the table node.
        assert node_information_dialog.selected_node == table_node

        # Get the create statement of the node.
        create_statement = node_information_dialog.get_node_create_statement()
        self.check_create_statement(create_statement)

    def test_dialog_with_valid_view_node(self):
        """
        Test the node information dialog with a view node.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a view node for the dialog.
        view_node = ViewNode("testview", "localhost", "testuser", "testdb", 5432, 10000)
        # Create an information dialog with view node.
        node_information_dialog = NodeCreateInformationDialog(view_node)
        # The selected node should be the view node.
        assert node_information_dialog.selected_node == view_node

        # Get the create statement of the node.
        create_statement = node_information_dialog.get_node_create_statement()
        self.check_create_statement(create_statement)

    def test_dialog_with_invalid_node(self):
        """
        Test the dialog with an invalid database node as error case.
        """

        # Create an app, because this is necessary for testing a QDialog.
        app = QApplication(sys.argv)
        # Create a database node with invalid connection parameters. In this case, the port is invalid.
        database_node = DatabaseNode("testdb", "localhost", "testuser", "testdb", 1337, 10000)
        node_information_dialog = NodeCreateInformationDialog(database_node)
        # The selected node should be the database node.
        assert node_information_dialog.selected_node == database_node
        # Get the create statement of the node.
        create_statement = node_information_dialog.get_node_create_statement()
        self.check_create_statement(create_statement)

    @staticmethod
    def check_create_statement(create_statement):
        """
        Define a method for checking the create statement of a node. The statement should contain at least one specified
        word in a list.
        """

        # The create statement should not be empty.
        assert create_statement != ""

        # Define a list with possible sub strings for a create statement. The string "failed" is in the list for the
        # error case.
        statement_can_contain_list = ["\nWITH", "\nENCODING", "\nLC_COLLATE", "\nLC_CTYPE", "\nLC_TYPE", "\nALTER",
                                      "CREATE", "failed"]

        # Define a boolean for checking the existence of a word in the list. This boolean is used in the for loop and
        # after the loop, it should be True.
        contains_string = False

        # Check for the existence of at least one word of the list.
        for possible_string in statement_can_contain_list:
            # Check for the string, which could be part of the create statement.
            if possible_string in create_statement:
                # Change the check boolean to True.
                contains_string = True

        # After iterating over the list with words, the boolean for checking should be True.
        assert contains_string is True
