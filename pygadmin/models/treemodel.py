"""
Create a structure for elements in a database structure with nodes. This structure is based on a root node or
AbstractBaseNode. The structure contains at least one server node. A server node contains database nodes. A database
node contains schema nodes. A schema node contains tables nodes and views nodes. A tables node contains table nodes and
a views node contains view nodes. It is possible, that the number of existing sub nodes is 0.
"""

import logging
import os

import psycopg2
from PyQt5.QtGui import QStandardItem, QIcon, QPixmap
from copy import deepcopy
from psycopg2 import sql

import pygadmin
from pygadmin.connectionfactory import global_connection_factory


class AbstractBaseNode(QStandardItem):
    """
    Create a class with attributes and functions as basis for all nodes used in the tree model. This class makes
    inheritance for additional nodes possible.
    """

    def __init__(self, name, host, user, database, port, timeout, **kwargs):
        super().__init__(name)

        # self.name declares the name of the node. It is not part of self.database_connection_parameters because it is
        # not a connection parameter.
        self.name = name

        # Create a dictionary for the connection parameters, e.g. to use them for the database connection.
        self.database_connection_parameters = {
            "host": host,
            "user": user,
            "port": port,
            "database": database,
            "timeout": timeout
        }

        # Establish a database connection as private variable with the parameters of the connection. A special error
        # handling is not necessary. This happens in the connection factory. If a connection with the value None or
        # False ends up here, the program does not crash, it works with errors specified in the log.
        self._database_connection = global_connection_factory.get_database_connection(
            **self.database_connection_parameters)

        # Get the type of the node without a "Node" at the end based on the class and qualname. This is necessary to
        # find icons in the next step.
        self._node_type = self.__class__.__qualname__.replace("Node", "")

        # There are special icons for the server and its connection status. The other ones are corner cases without
        # icons (yet?)
        if self._node_type not in ["Server", "Schema", "Tables", "Views"]:
            # Specify a path for icons. The path depends on the place of this file in the module. The icon is based
            # on the node type. This procedure ensures os independent file checking.
            node_icon_path = os.path.join(os.path.dirname(pygadmin.__file__), "icons",
                                          "{}.svg".format(self._node_type.lower()))

            self.add_node_icon(node_icon_path)

        # AbstractBaseNode is some kind of root node, so a parent is not necessary. This attribute is used by nodes
        # which inherit by this node.
        self._parent = None

    def add_node_icon(self, icon_path):
        """
        Add an icon to the name of the node.
        """

        # If the path exists, use the icons there.
        if os.path.exists(icon_path):
            # Create a QIcon.
            node_icon = QIcon()
            # Use the QIcon for adding a pixmap with the given path.
            node_icon.addPixmap(QPixmap(icon_path))
            self.setIcon(node_icon)

        else:
            logging.warning("Icons were not found for the node type {} with path in the treemodel.".format(
                self._node_type, icon_path))

    def add_child(self, child):
        """
        Add a child, which is an input parameter, to a node, if this child is an instance of AbstractBaseNode.
        """

        if isinstance(child, AbstractBaseNode):
            # Add a child with the function appendRow() of QStandardItem.
            self.appendRow(child)
            # Set the parent of the child to the current node to show the hierarchy.
            child._parent = self

        else:
            logging.warning("Child has a wrong object type, so appending is not possible. Please expect unexpected "
                            "behavior of the tree model.")

    def remove_child(self, child):
        """
        Remove a child, which is an input parameter. A check for the instance is necessary, because there could be any

        """

        if isinstance(child, AbstractBaseNode):
            # Set the parent to None because a removed child does not need a connection to a parent.
            child._parent = None
            # Remove child with the function removeRow() of QStandardItem.
            self.removeRow(child.row())

        else:
            logging.error("A child with a wrong type cannot be removed out of the tree model. The child is "
                          "{}".format(child))

    def fetch_children(self, child_class, query, parameters=None):
        """
        Fetch the children of a node with its class, a specified query and parameters as option. Parameters can be
        required for example to use a query with the schema name to get the views and tables.
        """

        # Check for the existence of a database connection. If the database connection does not have the correct type,
        # end the function.
        if not isinstance(self._database_connection, psycopg2.extensions.connection):
            return

        # Check for a closed database connection, because fetching children is not possible with a closed database
        # connection.
        if self._database_connection.closed == 1:
            # Get a new connection.
            self.update_database_connection()

        # Use the database connection of the node for executing the query.
        with self._database_connection.cursor() as database_cursor:
            # Execute the SQL query with its optional parameters
            database_cursor.execute(sql.SQL(query), parameters)

            # database_cursor has a description if the query leads to a result, which is not None.
            if database_cursor.description:
                # Get all data in a list.
                data_output = database_cursor.fetchall()
                for element in data_output:
                    # The first (or 0th) element contains under some circumstances and queries the database "template0"
                    # as database. This database can lead to problems, so the next steps are for every result except
                    # template0.
                    if element[0] != "template0":
                        # The function deepcopy() creates a real copy and not only a reference, so the connection 
                        # parameters can be copied and saved for further usage. They can also be modified without a
                        # modification of the original parameters.
                        current_database_parameter_configuration = deepcopy(self.database_connection_parameters)
                        current_database_parameter_configuration["name"] = element[0]
                        current_database_parameter_configuration["database"] = self.determine_child_database(element[0])
                        # Create a child node based on the changed information and so, on the results of the query.
                        current_node = child_class(**current_database_parameter_configuration)
                        # Add the created node with its information as child to the node.
                        self.add_child(current_node)

                    # This else branch is triggered for the database "template0".
                    else:
                        logging.info("Database template 0 appears for a potential connection. A connection is ("
                                     "normally) impossible, so this database will not appear in the tree model, "
                                     "preventing unexpected behavior and triggering logging messages.")

    def determine_child_database(self, child):
        """
        Determine the database of the given child.
        """

        return self.database_connection_parameters["database"]

    def update_database_connection(self):
        """
        Get a new database connection based on the database connection parameters. An update is necessary for closed
        connections, which needs to update something, for example their structure.
        """

        self._database_connection = global_connection_factory.get_database_connection(
            **self.database_connection_parameters)

    def close_database_connection(self):
        """
        Close the current database connection of the node with the help of the global connection factory.
        """

        # Close the database connection after usage.
        global_connection_factory.close_and_remove_database_connection(self._database_connection)

    def get_node_type(self):
        """
        Get the type of the node, which is a protected variable.
        """

        # Get the node type in a new variable.
        node_type = self._node_type

        return node_type


class ServerNode(AbstractBaseNode):
    """
    Create a class for server nodes based on the class AbstractBaseNode.
    """

    def __init__(self, name, host, user, port, database="postgres", timeout=1000, load_all_databases=True):
        # Use the database postgres, because this database should definitely exist on a database server and is used as
        # entry point here.
        super().__init__(name, host, user, database, port, timeout)

        # Check for the right class as psycopg2 connection object and an open connection. If there is one, an icon for
        # a valid connection is set and a query is used to get all children of the server node.
        if isinstance(self._database_connection, psycopg2.extensions.connection) \
                and self._database_connection.closed == 0:
            # Use the server icon for a valid connection.
            node_icon_path = os.path.join(os.path.dirname(pygadmin.__file__), "icons",
                                          "{}_valid.svg".format(self._node_type.lower()))

            # If all databases should be loaded, this parameter is True. This is a default parameter.
            if load_all_databases is True:
                child = None

            # If the parameter is not True, only one database should be loaded.
            else:
                child = database

            # Get the children with a query.
            self.get_children_with_query(child)

        else:
            # Use the server icon for a invalid connection.
            node_icon_path = os.path.join(os.path.dirname(pygadmin.__file__), "icons",
                                          "{}_invalid.svg".format(self._node_type.lower()))

        self.add_node_icon(node_icon_path)

        self.close_database_connection()

    def determine_child_database(self, child):
        """
        Overwrite the function determine_child_database of AbstractBaseNode. The children of a server node are the
        database nodes.
        """

        return child

    def get_children_with_query(self, child=None):
        """
        Get all children of the node with a database query. As default, get all the children of the node, but use an
        option for only getting one given child.
        """

        # If one explicit child is not given, get all the children of the server node.
        if child is None:
            # Use a query to get all children, in this case, all the database nodes.
            self.fetch_children(DatabaseNode, "SELECT datname FROM pg_database ORDER BY datname ASC;")

        # If an explicit child is given, load the one explicit child.
        else:
            self.fetch_children(DatabaseNode, "SELECT datname FROM pg_database WHERE datname=%s ORDER BY datname ASC;",
                                [child])


class DatabaseNode(AbstractBaseNode):
    """
    Create a class for database nodes based on the class AbstractBaseNode.
    """

    def __init__(self, name, host, user, database, port, timeout):
        super().__init__(name, host, user, database, port, timeout)

        self.get_children_with_query()

        # Close the database connection after usage.
        self.close_database_connection()

    def get_children_with_query(self):
        """
        Get all children of the node with a database query.
        """

        # Use a query to get all children, in this case, all the schema nodes except pg_toast, pg_toast_temp_1 and
        # pg_temp_1 as unused schemas.
        self.fetch_children(SchemaNode, "SELECT schema_name FROM information_schema.schemata WHERE schema_name "
                                        "!= 'pg_toast' AND schema_name != 'pg_toast_temp_1' AND schema_name "
                                        "!= 'pg_temp_1' ORDER BY schema_name ASC;")


class SchemaNode(AbstractBaseNode):
    """
    Create a class for schema nodes based on the class AbstractBaseNode.
    """

    def __init__(self, name, host, user, database, port, timeout):
        super().__init__(name, host, user, database, port, timeout)

        # Create static nodes for tables node and views node, because their existence is not based on a query. They
        # exist as a parent node for all table nodes or view nodes. The actual existence of tables or views is
        # irrelevant. In this corner case, the model ends in this node for this schema and database and server.
        self.add_child(TablesNode("Tables", name, host, user, database, port, timeout))
        self.add_child(ViewsNode("Views", name, host, user, database, port, timeout))


class ViewsNode(AbstractBaseNode):
    """
    Create a class for views nodes based on the class AbstractBaseNode.
    """

    def __init__(self, name, schema, host, user, database, port, timeout):
        super().__init__(name, host, user, database, port, timeout)

        # Define the schema, which is necessary as query parameter for fetching the children.
        self.schema = schema

        # Get children with an extra function.
        self.get_children_with_query()

    def get_children_with_query(self):
        """
        Get all children of the node with a database query.
        """

        # Use a query to get all children, in this case, all view nodes. Sort the nodes alphabetically.
        self.fetch_children(ViewNode, "SELECT table_name FROM information_schema.views WHERE table_schema=%s ORDER BY"
                                      " table_name ASC",
                            [self.schema])


class ViewNode(AbstractBaseNode):
    """
    Create a class for view nodes based on the class AbstractBaseNode. This node just exits.
    """

    pass


class TablesNode(AbstractBaseNode):
    """
    Create a class for tables nodes based on the class AbstractBaseNode.
    """

    def __init__(self, name, schema, host, user, database, port, timeout):
        super().__init__(name, host, user, database, port, timeout)
        # Define the schema, which is necessary as query parameter for fetching the children.
        self.schema = schema

        self.get_children_with_query()

    def get_children_with_query(self):
        """
        Get all children of the node with a database query.
        """

        # Use a query to get all children, in this case, all view nodes. Sort the nodes alphabetically.
        self.fetch_children(TableNode, "SELECT table_name FROM information_schema.tables WHERE table_schema=%s ORDER BY"
                                       " table_name ASC", [self.schema])


class TableNode(AbstractBaseNode):
    """
    Create a class for table nodes based on the class AbstractBaseNode. This node just exists.
    """

    pass
