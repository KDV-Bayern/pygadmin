import sys
import unittest

from PyQt5.QtWidgets import QApplication

from pygadmin.models.treemodel import ServerNode, DatabaseNode, SchemaNode, TablesNode, ViewsNode, TableNode, ViewNode


class TestTreeMethods(unittest.TestCase):
    """
    Use a class for testing the methods of the tree and the tree model.
    """

    def test_create_server_node(self):
        """
        Test the creation of a server node.
        """

        # A QApplication is necessary for the usage of a QPixmap, which is part of the Server Node.
        app = QApplication(sys.argv)
        # Create a test node with static connection parameters.
        ServerNode(name="localhost",
                   host="localhost",
                   user="testuser",
                   database="testdb",
                   port=5432,
                   timeout=5000)

    def test_node_children(self):
        # A QApplication is necessary for the usage of a QPixmap, which is part of the Server Node.
        app = QApplication(sys.argv)
        # Create a test node with static connection parameters.
        server_node = ServerNode(name="localhost",
                                 host="localhost",
                                 user="testuser",
                                 database="testdb",
                                 port=5432,
                                 timeout=5000)

        # The child at row and column 0 of a server node is a database node for a correct and fully functional database
        # connection.
        database_node = server_node.child(0, 0)
        # Check for the right instance.
        assert isinstance(database_node, DatabaseNode)

        # The child at row and column 0 of a database node is a schema node.
        schema_node = database_node.child(0, 0)
        # Check for the right instance.
        assert isinstance(schema_node, SchemaNode)

        # The child at row and column 0 of a schema node is a tables node.
        tables_node = schema_node.child(0, 0)
        # Check for the right instance.
        assert isinstance(tables_node, TablesNode)
        # The child at row 1 and column 0 of a schema node is a views node.
        views_node = schema_node.child(1, 0)
        # Check for the right instance.
        assert isinstance(views_node, ViewsNode)

        # The child at row and column 0 of a tables node is a table node.
        table_node = tables_node.child(0, 0)
        # Check for the right instance.
        assert isinstance(table_node, TableNode)
        # The child at row and column 0 of a views node is a view node.
        view_node = views_node.child(0, 0)
        # Check for the right instance.
        assert isinstance(view_node, ViewNode)

    def test_invalid_connection_of_node(self):
        # A QApplication is necessary for the usage of a QPixmap, which is part of the Server Node.
        app = QApplication(sys.argv)
        # Create a test node with static connection parameters. The host contains an invalid parameter, which results in
        # an invalid database connection.
        server_node = ServerNode(name="localhost",
                                 host="local",
                                 user="testuser",
                                 database="testdb",
                                 port=5432,
                                 timeout=5000)

        # The child of a server node should be None for an invalid connection.
        assert server_node.child(0, 0) is None
