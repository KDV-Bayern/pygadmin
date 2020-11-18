import sys
import unittest

from PyQt5.QtWidgets import QApplication

from pygadmin.widgets.tree import TreeWidget
from pygadmin.connectionstore import global_connection_store
from pygadmin.models.treemodel import ServerNode


class TestTreeWidgetMethods(unittest.TestCase):
    """
    Test the basic functionality, correct behavior and some functions of the tree widget.
    """

    def test_initial_attributes(self):
        """
        Test some of the initial attributes of the widget.
        """

        # Create an app, because this is necessary for testing a QWidget.
        app = QApplication(sys.argv)
        # Create a tree widget.
        tree_widget = TreeWidget()

        # At the start of the widget, there should not be a selected index.
        assert tree_widget.selected_index is False
        # Check for the existence and correct instance of the server node list.
        assert isinstance(tree_widget.server_nodes, list)

    def test_find_new_relevant_parameters(self):
        """
        Test the function for finding new relevant connection parameters.
        """

        # Create an app, because this is necessary for testing a QWidget.
        app = QApplication(sys.argv)
        # Create a tree widget.
        tree_widget = TreeWidget()

        # Add potential existing nodes to the tree widget.
        for connection_dictionary in tree_widget.find_new_relevant_parameters():
            new_server_node = ServerNode(connection_dictionary["Host"],
                                         connection_dictionary["Host"],
                                         connection_dictionary["Username"],
                                         connection_dictionary["Port"],
                                         connection_dictionary["Timeout"])
            tree_widget.server_nodes.append(new_server_node)

        # After the start and without new relevant connection parameters, the function should return an empty list.
        assert tree_widget.find_new_relevant_parameters() == []

        # Define new connection parameters, so new relevant parameters can be found.
        new_connection_parameters = {"Host": "127.0.01",
                                     "Database": "testdb",
                                     "Port": 5432,
                                     "Username": "testuser"}

        # Get the current number of the connection parameters in the connection store and use it as new position for new
        # connection parameters.
        position = global_connection_store.get_number_of_connection_parameters()
        # Save the new defined connection parameters in the connection store.
        global_connection_store.save_connection_parameters_in_yaml_file(new_connection_parameters)
        # Get the new and relevant parameters out of the tree widget.
        new_relevant_parameters = tree_widget.find_new_relevant_parameters(position)[0]

        # Check for the correct values for the given keys in the dictionary, because they should be identical.
        assert new_connection_parameters["Database"] == new_relevant_parameters["Database"]
        assert new_connection_parameters["Host"] == new_relevant_parameters["Host"]
        assert new_connection_parameters["Port"] == new_relevant_parameters["Port"]
        assert new_connection_parameters["Username"] == new_relevant_parameters["Username"]

        # Delete the new connection parameters as a clean up.
        global_connection_store.delete_connection(new_connection_parameters)

    def test_create_new_server_node(self):
        """
        Test the method for creating a new server node.
        """

        # Create an app, because this is necessary for testing a QWidget.
        app = QApplication(sys.argv)
        # Create a tree widget.
        tree_widget = TreeWidget()

        # Define connection parameters for a new server node.
        server_node_connection_parameters = {"Host": "testhost",
                                             "Database": "testdb",
                                             "Port": 5432,
                                             "Username": "testuser",
                                             "Timeout": 10000}

        # Create a new server node with the tree widget.
        new_server_node = tree_widget.create_new_server_node(server_node_connection_parameters)
        # As a result, the created node should be a server node.
        assert isinstance(new_server_node, ServerNode)

        # Append the node to the list of server nodes, so the next assertion is checked correctly.
        tree_widget.server_nodes.append(new_server_node)
        # The creation of a new server node should return None, because there is a duplicate.
        assert tree_widget.create_new_server_node(server_node_connection_parameters) is None

    def test_check_server_node_for_duplicate(self):
        """
        Test the method for checking the parameters of a potentially new server node for a duplicate.
        """

        # Create an app, because this is necessary for testing a QWidget.
        app = QApplication(sys.argv)
        # Create a tree widget.
        tree_widget = TreeWidget()

        # Define connection parameters for a new server node.
        server_node_connection_parameters = {"Host": "testhost",
                                             "Database": "testdb",
                                             "Port": 5432,
                                             "Username": "testuser",
                                             "Timeout": 10000}

        # There should not be a server node with the connection parameters of the new server node.
        assert tree_widget.check_server_node_for_duplicate(server_node_connection_parameters) is False

        # Create a new server node.
        new_server_node = tree_widget.create_new_server_node(server_node_connection_parameters)
        # Append the new node to the list of server nodes.
        tree_widget.server_nodes.append(new_server_node)
        # The check for a duplicate with the same and old parameters should return True, because there is a duplicate.
        assert tree_widget.check_server_node_for_duplicate(server_node_connection_parameters) is True

    def test_append_new_node(self):
        """
        Test the method for appending a new node in the tree widget.
        """

        # Create an app, because this is necessary for testing a QWidget.
        app = QApplication(sys.argv)
        # Create a tree widget.
        tree_widget = TreeWidget()

        # Create a new server node.
        server_node = ServerNode("testhost", "testhost", "testuser", 5432)
        # Use the method of the tree widget for appending a new server node.
        tree_widget.append_new_node(server_node)

        # Check for the existence of the new server node in the server node list of the tree widget.
        assert server_node in tree_widget.server_nodes
