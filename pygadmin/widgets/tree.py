import copy
import logging

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QItemSelectionModel, QModelIndex, Qt, QRunnable, QThreadPool, QObject
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QWidget, QTreeView, QAbstractItemView, QMessageBox, QGridLayout, QPushButton, QMenu, \
    QAction, QMainWindow

from pygadmin.configurator import global_app_configurator
from pygadmin.connectionstore import global_connection_store
from pygadmin.csv_exporter import CSVExporter
from pygadmin.models.treemodel import ServerNode, TablesNode, ViewsNode, SchemaNode, AbstractBaseNode, DatabaseNode, \
    TableNode, ViewNode
from pygadmin.widgets.materialized_view_information import MaterializedViewInformationDialog
from pygadmin.widgets.node_create_information import NodeCreateInformationDialog
from pygadmin.widgets.permission_information import PermissionInformationDialog
from pygadmin.widgets.table_edit import TableEditDialog
from pygadmin.widgets.table_information import TableInformationDialog


class TreeWorkerSignals(QObject):
    """
    Define signals for the TreeNodeWorker.
    """

    # Define a signal for the successful creation of all initial nodes.
    node_creation_complete = pyqtSignal(bool)


class TreeNodeWorker(QRunnable):
    """
    Define a class for creating all initial server nodes in a separate thread.
    """

    def __init__(self, function_to_execute, connection_parameters, server_node_list, tree_model, new_node_added_signal):
        """
        Get the function to execute with its required parameters.
        """

        super().__init__()
        self.function_to_execute = function_to_execute
        self.connection_parameters = connection_parameters
        self.server_node_list = server_node_list
        self.tree_model = tree_model
        self.new_node_added_signal = new_node_added_signal
        self.signals = TreeWorkerSignals()

    @pyqtSlot()
    def run(self):
        """
        Run the function to execute with its parameters. All nodes are created at once, so the creation of all nodes is
        in one separate thread.
        """

        # Execute the function.
        self.function_to_execute(self.connection_parameters, self.server_node_list, self.tree_model,
                                 self.new_node_added_signal)

        # Emit the signal for a complete creation.
        self.signals.node_creation_complete.emit(True)


class TreeWidget(QWidget):
    """
    Create a class which is a child class of QWidget as interface for the tree, which shows the available servers,
    databases, schemas, views and tables in a defined structure. The widget also contains a signal for the currently
    selected database or database environment.
    """

    # Define a signal for the change of database parameters, which is currently used by the widget.
    database_parameter_change = pyqtSignal(dict)
    new_node_added = pyqtSignal(bool)

    def __init__(self):
        """
        Make sub functions for initializing the widget, separated by the parts user interface and grid
        layout.
        """

        super().__init__()
        self.init_ui()
        self.init_grid()

    def init_ui(self):
        """
        Design the user interface and its components.
        """

        # Use a tree view for showing the data in the form of a tree.
        self.tree_view = QTreeView()
        # Disable the possibility to edit items in the tree.
        self.tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # Deactivate a header, because there is nothing relevant to show in the header.
        self.tree_view.header().setVisible(False)

        # Define the tree model as QStandardItemModel, which is also the base for the different nodes in the tree model.
        self.tree_model = QStandardItemModel()
        # Connect the function for a row insert with the function for selecting an index.
        self.tree_model.rowsInserted.connect(self.select_previous_selected_index)
        self.selected_index = False

        # Check for empty connection parameters and warn the user in case.
        if global_connection_store.get_connection_parameters_from_yaml_file() is None:
            logging.warning("Database connection parameters cannot be found in "
                            "{}.".format(global_connection_store.yaml_connection_parameters_file))

            QMessageBox.warning(self, "No connections in file",
                                "The file {} does not contain any database connection parameters.".format(
                                    global_connection_store.yaml_connection_parameters_file))

        # Set the actual tree model to the tree view, which is necessary for connecting the signal of the selection
        # model for a current change.
        self.tree_view.setModel(self.tree_model)

        # Use the selection model of the tree view to get the current selected node.
        self.tree_view.selectionModel().selectionChanged.connect(
            self.get_selected_element_by_signal_and_emit_database_parameter_change)

        # Create a button for adding and changing connection data.
        self.add_connection_data_button = QPushButton("Add Connection Data")
        # Connect a click on the button with a function for a new connection dialog.
        self.add_connection_data_button.clicked.connect(self.get_new_connection_dialog)

        # Set the context menu policy to a custom context menu, so a own context menu can be used. This change of policy
        # emits the following signal for a custom context menu.
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        # Use the signal for a custom context menu to open a context menu with the specified function. The signal uses
        # the position of the mouse to transmit the clicked item.
        self.tree_view.customContextMenuRequested.connect(self.open_context_menu)

        # Create a thread pool for the later usage of the tree node worker.
        self.thread_pool = QThreadPool()

        # Make an empty list for initializing the variable. The variable is not changed, if the .yaml file does not
        # contain any parameters.
        self.server_nodes = []

        self.setGeometry(600, 600, 500, 300)
        self.setWindowTitle("Database Tree")
        self.show()

    def init_data(self):
        """
        Initialize the connection data and the relevant parameters at the start of the application. Use the initial data
        to create a list of connection dictionaries for the initial creation of the nodes.
        """

        # Get the current connection parameters stored in the .yaml file.
        current_connection_parameters = global_connection_store.get_connection_parameters_from_yaml_file()

        current_query_timeout = self.get_current_query_timeout()

        # These parameters can be None, if the .yaml file does not contain any connection parameters.
        if current_connection_parameters is not None:
            # Get every connection parameter dictionary and add the timeout.
            for connection_parameters in current_connection_parameters:
                connection_parameters["Timeout"] = current_query_timeout

        # Initialize the tree node worker for creating all initial nodes in a single thread. Use the created connection
        # parameters, the server node list for adding the new node, the tree model for inserting a new node and the
        # signal for emitting the addition of a new node as parameters.
        tree_node_worker = TreeNodeWorker(self.create_all_initial_nodes, current_connection_parameters,
                                          self.server_nodes, self.tree_model, self.new_node_added)

        # Connect the signal for the creation success with the function for sorting the tree, so the tree is sorted
        # after the initializing of all nodes.
        tree_node_worker.signals.node_creation_complete.connect(self.sort_tree)

        # Start the tree node worker.
        self.thread_pool.start(tree_node_worker)

    @staticmethod
    def create_all_initial_nodes(connection_parameters, server_node_list, tree_model, new_node_added_signal):
        """
        Create all initial server nodes in a static function, so this function can be used by a QRunnable without
        interfering in the main thread. Use the connection parameters for the creation of a new server node, the server
        node and the tree model for appending the new node and the signal for emitting an information about appending a
        new node.
        """

        # Create a server node for every connection dictionary.
        for connection_parameter in connection_parameters:
            # Get the parameter for loading all databases.
            try:
                load_all_databases = connection_parameter["Load All"]

            except KeyError:
                load_all_databases = True

            new_node = ServerNode(name=connection_parameter["Host"],
                                  host=connection_parameter["Host"],
                                  user=connection_parameter["Username"],
                                  database=connection_parameter["Database"],
                                  port=connection_parameter["Port"],
                                  timeout=connection_parameter["Timeout"],
                                  load_all_databases=load_all_databases)

            # Append the node to the server list.
            server_node_list.append(new_node)
            # Insert the node in the tree model.
            tree_model.insertRow(0, new_node)
            # Emit the signal for a new added node.
            new_node_added_signal.emit(True)

    def init_grid(self):
        """
        Set a grid layout to the widget and place all its components.
        """

        # Define the layout.
        grid_layout = QGridLayout()
        # Set the tree view as only element on the widget.
        grid_layout.addWidget(self.tree_view, 0, 0)
        grid_layout.addWidget(self.add_connection_data_button, 1, 0)

        grid_layout.setSpacing(10)

        self.setLayout(grid_layout)

    def open_context_menu(self, position):
        """
        Get the position of a requested context menu and open the context menu at this position with different actions.
        One of these actions is to open a new connection dialog and for this, the current selected item/node is
        necessary, so the corresponding connection is selected in the dialog.
        """

        # Make a new context menu as QMenu.
        self.context_menu = QMenu()

        # Get the current selected node by the function for getting the selected element by the current selection.
        current_selected_node = self.get_selected_element_by_current_selection()

        # Check, if the current selected node is a server node.
        if isinstance(current_selected_node, ServerNode):
            # Create an action for editing the database connection of the server node.
            edit_connection_action = QAction("Edit Connection", self)
            # Add the action to the context menu.
            self.context_menu.addAction(edit_connection_action)
            # Create an action for refreshing the server node.
            refresh_action = QAction("Refresh", self)
            # Add the action to the context menu.
            self.context_menu.addAction(refresh_action)
            # Get the action at the current position of the triggering event.
            position_action = self.context_menu.exec_(self.tree_view.viewport().mapToGlobal(position))

            # Check, if the action at the current position is the action for editing the connection.
            if position_action == edit_connection_action:
                # Show a connection dialog with the current selected node as preselected node.
                self.show_connection_dialog_for_current_node(current_selected_node)

            # Check, if the action at the current position is the action for refreshing the node.
            elif position_action == refresh_action:
                # Refresh the current selected node.
                self.refresh_current_selected_node(current_selected_node)

        if isinstance(current_selected_node, DatabaseNode):
            show_create_statement_action = QAction("Show Create Statement", self)
            self.context_menu.addAction(show_create_statement_action)
            show_drop_statement_action = QAction("Show Drop Statement", self)
            self.context_menu.addAction(show_drop_statement_action)
            show_permission_information_action = QAction("Show Permissions", self)
            self.context_menu.addAction(show_permission_information_action)
            show_materialized_views_action = QAction("Show Materialized Views")
            self.context_menu.addAction(show_materialized_views_action)

            position_action = self.context_menu.exec_(self.tree_view.viewport().mapToGlobal(position))

            if position_action == show_create_statement_action:
                # Use the function for getting the create statement of the database node.
                self.get_create_statement_of_node(current_selected_node)

            elif position_action == show_drop_statement_action:
                self.get_drop_statement_of_database_node(current_selected_node)

            elif position_action == show_permission_information_action:
                self.show_permission_dialog(current_selected_node)

            elif position_action == show_materialized_views_action:
                self.show_materialized_views_of_database_node(current_selected_node)

        # Check for a view node.
        if isinstance(current_selected_node, ViewNode):
            show_create_statement_action = QAction("Show Create Statement", self)
            self.context_menu.addAction(show_create_statement_action)
            show_permission_information_action = QAction("Show Permissions", self)
            self.context_menu.addAction(show_permission_information_action)

            # Get the action at the current position of the triggering event.
            position_action = self.context_menu.exec_(self.tree_view.viewport().mapToGlobal(position))

            if position_action == show_create_statement_action:
                # Use the function for getting the create statement of the view node.
                self.get_create_statement_of_node(current_selected_node)

            elif position_action == show_permission_information_action:
                self.show_permission_dialog(current_selected_node)

        # Check for a table node as current selected node.
        if isinstance(current_selected_node, TableNode):
            # Create an action for showing the definition of the node.
            show_definition_action = QAction("Show Definition", self)
            # Add the action to the context menu.
            self.context_menu.addAction(show_definition_action)
            # Create an action for showing the full definition of the node.
            show_full_definition_action = QAction("Show Full Definition", self)
            # Add the action to the context menu.
            self.context_menu.addAction(show_full_definition_action)
            # Create an action for showing the create statement of the table node.
            show_create_statement_action = QAction("Show Create Statement", self)
            self.context_menu.addAction(show_create_statement_action)
            show_permission_information_action = QAction("Show Permissions", self)
            self.context_menu.addAction(show_permission_information_action)
            edit_single_values_action = QAction("Edit Single Values", self)
            self.context_menu.addAction(edit_single_values_action)
            export_full_table_to_csv_action = QAction("Export Full Table As CSV", self)
            self.context_menu.addAction(export_full_table_to_csv_action)
            # Get the action at the current position of the triggering event.
            position_action = self.context_menu.exec_(self.tree_view.viewport().mapToGlobal(position))

            # Check, if the action at the current position is the action for showing the definition of a table.
            if position_action == show_definition_action:
                # Show a new table dialog.
                self.show_table_information_dialog(current_selected_node, False)

            # Check, if the action at the current position is the action for showing the full definition of a table
            elif position_action == show_full_definition_action:
                # Show the new table dialog.
                self.show_table_information_dialog(current_selected_node, True)

            elif position_action == show_create_statement_action:
                # Use the function for getting the create statement of the database node.
                self.get_create_statement_of_node(current_selected_node)

            elif position_action == show_permission_information_action:
                self.show_permission_dialog(current_selected_node)

            elif position_action == edit_single_values_action:
                self.show_edit_singles_values_dialog(current_selected_node)

            elif position_action == export_full_table_to_csv_action:
                self.get_full_data_of_current_table_for_csv_export(current_selected_node)

    def append_new_connection_parameters_and_node(self):
        """
        Get new parameters out of the .yaml file, where all connections are stored, because this function should be
        called after adding new database connection parameters to the file. These new parameters are used to create new
        server nodes and then, they are appended to the list of all nodes and to the tree model.
        """

        # Get the new parameters.
        new_connection_parameters = self.find_new_relevant_parameters()
        # Get the current timeout.
        current_query_timeout = self.get_current_query_timeout()

        # If the list for the new connection parameters exist, the list is not empty.
        if new_connection_parameters:
            # Check every possible connection in the list.
            for connection_parameters in new_connection_parameters:
                # Inject the current timeout in the dictionary for connection parameters.
                connection_parameters["Timeout"] = current_query_timeout
                # Create a new node.
                new_node = self.create_new_server_node(connection_parameters)

                # If the node is a server node, append it to the list of nodes and to the tree.
                if isinstance(new_node, ServerNode):
                    self.append_new_node(new_node)

        # This else branch is used for an empty list and as a result, non existing new connections.
        else:
            logging.info("New database connection parameters in {} could not be found and all previous database "
                         "connection parameters are currently represented in the "
                         "tree".format(global_connection_store.yaml_connection_parameters_file))

    def find_new_relevant_parameters(self, position=None):
        """
        Find new parameters in the .yaml file for database connection parameters. If there are new parameters, return
        them in the list. If not, return an empty list. Normally, new relevant parameters are at the end of the .yaml
        file. If not, there is a position parameter for the exact position of the connection.
        """

        # Create a container list for the relevant parameters.
        relevant_parameters = []

        # If the position is None, there is just an appending to the tree and so, the last parameters in the .yaml file
        # can be used.
        if position is None:
            # Get the number of currently unused parameters as connection parameter dictionaries, which are not
            # represented with server nodes at the moment. Use the function of the connection store to check the current
            # number of connection parameters and the length of the list for all nodes.
            number_of_unused_parameters = global_connection_store.get_number_of_connection_parameters() - \
                                          len(self.server_nodes)

            # If the number of currently of unused parameters is larger than 0, there are parameters, which are
            # currently not represented.
            if number_of_unused_parameters > 0:
                # Get the list of all parameters out of the connection store.
                full_parameter_list = global_connection_store.get_connection_parameters_from_yaml_file()
                # Define a list for the connection dictionaries of the different server nodes.
                server_node_dictionaries = []

                # Get for every server node a connection dictionary.
                for server_node in self.server_nodes:
                    server_connection_dictionary = {"Host": server_node.database_connection_parameters["host"],
                                                    "Database": server_node.database_connection_parameters["database"],
                                                    "Port": server_node.database_connection_parameters["port"],
                                                    "Username": server_node.database_connection_parameters["user"]}
                    server_node_dictionaries.append(server_connection_dictionary)

                # The relevant parameters are the one, which are only part of the list of all parameters and not part of
                # the list with the server connection dictionaries.
                relevant_parameters = [connection_dictionary for connection_dictionary in full_parameter_list
                                       if connection_dictionary not in server_node_dictionaries]

        # If there is a position, the new connection parameters can be found with this information. This else branch is
        # used for the change of a connection, so the position in the tree is contained.
        else:
            # Get the parameters out of the connection store.
            relevant_connection_parameters_dictionary = global_connection_store.get_connection_at_index(position)
            # Append them to the list of relevant parameters, so a node can be created.
            relevant_parameters.append(relevant_connection_parameters_dictionary)

        timeout = global_app_configurator.get_single_configuration("Timeout")

        if timeout is None:
            timeout = 10000

        for connection_dictionary in relevant_parameters:
            connection_dictionary["Timeout"] = timeout

        return relevant_parameters

    def create_new_server_node(self, connection_parameters_for_server_node):
        """
        Take database connection parameters and use them to create a server node after a check for a duplicate. Return
        the server node.
        """

        # Get the parameter for loading all databases.
        try:
            load_all_databases = connection_parameters_for_server_node["Load All"]

        except KeyError:
            load_all_databases = True

        # Try to create a server node.
        try:
            # Check for a duplicate, because only one server node is necessary for one host, user and port.
            if self.check_server_node_for_duplicate(connection_parameters_for_server_node) is not True:
                server_node = ServerNode(name=connection_parameters_for_server_node["Host"],
                                         host=connection_parameters_for_server_node["Host"],
                                         user=connection_parameters_for_server_node["Username"],
                                         database=connection_parameters_for_server_node["Database"],
                                         port=connection_parameters_for_server_node["Port"],
                                         timeout=connection_parameters_for_server_node["Timeout"],
                                         load_all_databases=load_all_databases)

            else:
                # If there is a duplicate, set the server node as return value to None, because a server node was not
                # created.
                server_node = None

        # Use an error for a failed connection.
        except Exception as error:
            server_node = None
            # Communicate the connection error with a QMessageBox to the user.
            QMessageBox.critical(self, "Connection Error", "A connection cannot be established in the tree model. "
                                                           "Please check the log for further information. "
                                                           "The resulted error is {}.".format(str(error)))

        return server_node

    def check_server_node_for_duplicate(self, new_server_node_parameters):
        """
        Use the database connection parameters of a candidate for a new server node and check in the list of all server
        nodes, if a (nearly) identical node exists. An identical node in this case is described as a node with the same
        host, username and port. A second server node for a different database in the tree is not necessary.
        """

        # Check every existing server node with its parameters for a match in the given parameters for a new server
        # node.
        for server_node in self.server_nodes:
            # Get the parameters of the existing server node.
            server_node_parameters = server_node.database_connection_parameters

            # Check for the same host, user and port.
            if server_node_parameters["host"] == new_server_node_parameters["Host"] and \
                    server_node_parameters["user"] == new_server_node_parameters["Username"] and \
                    server_node_parameters["port"] == new_server_node_parameters["Port"]:
                # Warn the user, if one duplicate is found.
                logging.warning("A server node with the connection parameters {} already exists. The database can be a "
                                "different one, but a new server node is not necessary for another database"
                                "".format(new_server_node_parameters))

                # Use a return value to break the for loop, because further iterations are after a found not necessary.
                return True

        return False

    def get_selected_element_by_signal_and_emit_database_parameter_change(self, new_item_selection,
                                                                          previous_item_selection):
        """
        Get the currently selected element/node in the tree view by a signal, which uses the new selection of an item
        and the previous selection as parameters. The previous item contains information about the previous node and its
        connection. Normally, the connection of the previous node is closed, while a new one for the new selected node
        is opened. In case of identical connections parameters, the connection of the previous node is not closed, but
        recycled. The function uses the currently selected node to emit a signal for changed database connection
        parameters.
        """

        # Initialize the previous node as None.
        previous_node = None

        # Check all indexes for the previous item selection.
        for index in previous_item_selection.indexes():
            # Get the node at the item with a match for further usage.
            previous_node = self.tree_model.itemFromIndex(index)

        # Check all indexes (one or None) of the new item selection.
        for index in new_item_selection.indexes():
            # Get the node out of the treemodel with the index.
            new_node = self.tree_model.itemFromIndex(index)
            # Check the previous node for its instance, because it should be a node to match with the required
            # attributes.
            if isinstance(previous_node, AbstractBaseNode) and isinstance(new_node, AbstractBaseNode):
                # Check the connection parameters of the previous node and the new node. If they are different, a new
                # connection is required and the old one needs to be closed.
                if previous_node.database_connection_parameters != new_node.database_connection_parameters:
                    # Close the database connection of the previous node.
                    previous_node.close_database_connection()

            # Update the database connection of the new, selected node, so there is an open connection available.
            new_node.update_database_connection()

            # Emit the change with the parameters of the new selected node.
            self.database_parameter_change.emit(new_node.database_connection_parameters)

    def get_selected_element_by_current_selection(self):
        """
        Use the method of the tree view for getting all selected indexes and check for a selected index. Use the index
        to get a node as currently selected element.
        """

        # Check for a selected index in the list of all selected indexes of the tree view.
        for index in self.tree_view.selectedIndexes():
            # Get the node with the given index.
            node = self.tree_model.itemFromIndex(index)

            # Return the node, which was found.
            return node

    # Use as type for a slot parameter an object, because it can not only be a dictionary.
    @pyqtSlot(object)
    def select_node_for_database_parameters(self, database_parameter_dict):
        """
        Select a database node in the tree model based on a dictionary with parameters. If there is a dictionary, the
        nodes of the tree are checked for the same parameters. If there is compatible node, this one is selected in the
        tree view. If there is not a dictionary, the current selection in the tree view is cleared.
        """

        # Check for a dictionary to read the connection parameters.
        if isinstance(database_parameter_dict, dict):
            # Clear the selection before enabling a new one.
            self.tree_view.selectionModel().clear()
            # Check every server node, because self.nodes contains all added server nodes in a list.
            for server_node in self.server_nodes:
                # Check the server node and the given dictionary with connection parameters for the same hostname,
                # user and port.
                if server_node.database_connection_parameters["host"] == database_parameter_dict["host"] \
                        and server_node.database_connection_parameters["user"] == database_parameter_dict["user"] \
                        and server_node.database_connection_parameters["port"] == database_parameter_dict["port"]:

                    # Check for an expanded node in the tree view at the current index of the server node. If the tree
                    # is expanded, proceed. If not, open the tree at the current index of the server node. This course
                    # of action prevents bad behavior: A node can be selected, but if the tree is not expanded, this
                    # (database) node is unseen and it looks like a bug without being a bug.
                    if self.tree_view.isExpanded(server_node.index()) is False:
                        self.tree_view.expand(server_node.index())

                    # Use the row count of the matching server node and check every child/database.
                    for row in range(server_node.rowCount()):
                        # Get the related database node.
                        database_node = server_node.child(row)
                        # Check if the database name of the node and of the dictionary are the same.
                        if database_node.database_connection_parameters["database"] \
                                == database_parameter_dict["database"]:
                            # Get the index of the database node.
                            database_node_index = database_node.index()
                            # Use the tree view to select the found database node
                            self.tree_view.selectionModel().select(database_node_index,
                                                                   QItemSelectionModel.SelectCurrent)

                            # Return nothing, so the for loops end, because a node was found.
                            return

                    # Add an else statement to the for loop: If there is not a database, this connection is flawed. But
                    # the connection can still be selected, so it will be selected.
                    else:
                        self.tree_view.selectionModel().select(server_node.index(), QItemSelectionModel.SelectCurrent)

                        return

        # This else is triggered, if the parameter is not a dictionary.
        else:
            # Select an empty model index in the tree view, so there is not a selected node.
            self.tree_view.selectionModel().select(QModelIndex(), QItemSelectionModel.Clear)

    def update_tree_structure(self, change_node_information):
        """
        Update the structure of the tree after creating, deleting, dropping, altering, ... tables or views or schemas or
        databases with the information, which node is changed. The variable change_information is a tuple and contains a
        pattern for the node and the database connection parameters to find the right node for further operations.
        """

        # Get the node pattern out of the tuple.
        node_type_pattern = change_node_information[0]

        # If the pattern contains a TABLE, the relevant node is the TablesNode.
        if node_type_pattern == "TABLE":
            node_type = TablesNode

        # If the pattern contains a VIEW, the relevant node is the ViewsNode.
        elif node_type_pattern == "VIEW":
            node_type = ViewsNode

        # In the elif branch, the pattern contains a SCHEMA, so the relevant node is the SchemaNode.
        elif node_type_pattern == "SCHEMA":
            node_type = SchemaNode

        # The last known pattern contains a DATABASE, so the relevant node is the DatabaseNode.
        else:
            node_type = DatabaseNode

        # Get the connection parameters as second part of the tuple.
        database_connection_parameters = change_node_information[1]

        # Check every server node for the occurrence  of the database connection parameters and try to find a match.
        for server_node in self.server_nodes:
            # Check for host, user and port as currently relevant parameters and proceed with the match.
            if server_node.database_connection_parameters["host"] == database_connection_parameters["host"] \
                    and server_node.database_connection_parameters["user"] == database_connection_parameters["user"] \
                    and server_node.database_connection_parameters["port"] == database_connection_parameters["port"]:

                # Check for the node type and proceed for a database node.
                if node_type == DatabaseNode:
                    # Remove all current database nodes of the current server node.
                    server_node.removeRows(0, server_node.rowCount())
                    # Get all children and so, the updated child will be a part of it.
                    server_node.get_children_with_query()

                    # End the function with a return, because at this point, everything related to a new database is
                    # done.
                    return

                # Check every database node as child of a server node and its place in the row count of a server node.
                for server_row in range(server_node.rowCount()):
                    # Get the child node of a server by the row. The child is a database node.
                    database_node = server_node.child(server_row)

                    # Check for a match in the database with the database connection parameters.
                    if database_node.database_connection_parameters["database"] \
                            == database_connection_parameters["database"]:

                        # If a schema node is the relevant node, use this if branch.
                        if node_type == SchemaNode:
                            # Remove all nodes between the start of the database node and the end of the range of all
                            # children of the database node.
                            database_node.removeRows(0, database_node.rowCount())

                            # Generate new children.
                            database_node.get_children_with_query()

                        # If the TablesNode or the ViewsNode is relevant, continue with the else branch.
                        else:
                            # Get every node between the begin and end of a database node.
                            for database_row in range(database_node.rowCount()):
                                # Label the nodes as children of the database node. These children are SchemaNodes.
                                schema_node = database_node.child(database_row)

                                # Get every node in the range of this SchemaNode.
                                for schema_row in range(schema_node.rowCount()):
                                    # Label the nodes as children of the schema node. TablesNodes and ViewsNodes are
                                    # possible.
                                    tables_views_node = schema_node.child(schema_row)

                                    # Check the child node for its type with is decided by the given pattern, so this
                                    # operation is only executed by the relevant node. If the pattern describes a TABLE,
                                    # the TablesNode is used. If the pattern describes a VIEW, a ViewNode is used.
                                    if isinstance(tables_views_node, node_type):
                                        # Remove all nodes between the start of the TablesNode/ViewsNode and its end.
                                        tables_views_node.removeRows(0, tables_views_node.rowCount())
                                        # Reload all children and create new nodes.
                                        tables_views_node.get_children_with_query()

                        # Return at this point, so the iteration in the for loop ends fast, because a match was found
                        # and the relevant operations were performed. There is no need to check further nodes.
                        return

    def update_tree_connection(self, changed_connection_parameters_and_change_information):
        """
        Update a given connection in the tree. The given parameter contains a dictionary with the connection parameters
        and an information about the kind of change. If a connection is changed, there is also its position in the
        global connection store.
        """

        # Get the connection parameters.
        changed_connection_parameters = changed_connection_parameters_and_change_information[0]

        # Get more information about the change. This variable contains, if a connection was deleted or if a new one was
        # created.
        change_information = changed_connection_parameters_and_change_information[1]

        # Get the information about the changed index.
        index_in_connection_store = changed_connection_parameters_and_change_information[2]

        # If the change information is new, there is a new node.
        if change_information == "new":
            # Use the function for appending new nodes.
            self.append_new_connection_parameters_and_node()

            # End the function with a return.
            return

        # Initialize the variable for the row of the server node, which will be the node with the changed connection
        # parameters.
        current_server_node_row = 0

        # Define a variable for the usage of the selected index as container.
        self.selected_index = False

        # Iterate over all server nodes to find the one with the given connection parameters, which were changed.
        for server_node in self.server_nodes:
            # Check for the right host, user, port and database.
            if server_node.database_connection_parameters["host"] == changed_connection_parameters["Host"] \
                    and server_node.database_connection_parameters["user"] == changed_connection_parameters[
                "Username"] \
                    and server_node.database_connection_parameters["port"] == changed_connection_parameters["Port"] \
                    and server_node.database_connection_parameters["database"] == changed_connection_parameters[
                "Database"]:
                # Get the current row number of the index of the server node to find the part of the tree, which needs
                # to be removed.
                current_server_node_row = server_node.index().row()

                # Iterate over all selected indexes of the tree view. There should be None or one selected index.
                for index in self.tree_view.selectedIndexes():
                    # Check for the current server node, which is about to be deleted and the current selected item in
                    # the tree view with its index in the tree model.
                    if server_node == self.tree_model.itemFromIndex(index):
                        # Save the index in the variable.
                        self.selected_index = True

                # If the variable for selected index is not None, there was a selected index. This index is saved now
                # for further usage.
                if self.selected_index is True:
                    # Clear the current selection, so a new selection is not automatically chosen.
                    self.tree_view.selectionModel().clear()

                # Remove the node from the list of all nodes.
                self.server_nodes.remove(server_node)
                # Remove the node from the tree model with its row.
                self.tree_model.removeRow(current_server_node_row)

        # If the change information is change, there has been a change in the connection parameters and not only a
        # deletion.
        if change_information == "change":
            # Get the new and relevant parameters with the position of the connection parameters in the list of the
            # connection store.
            updated_parameter_list = self.find_new_relevant_parameters(position=index_in_connection_store)

            # If there is a new parameter in the updated list, update the tree model.
            if updated_parameter_list:
                # Create a new node with the first element in the list, which should be the only relevant element,
                # because there should be just one change in parameters for one, single node.
                new_node = self.create_new_server_node(updated_parameter_list[0])
                # Append the new node with the function for appending new nodes, so the node is appended and sorted.
                self.append_new_node(new_node)

    def get_new_connection_dialog(self, current_selection_identifier=None):
        """
        Get a new connection dialog and use the modified data of the dialog to change dynamically the appearance of the
        tree model. The identifier for a current selection ensures a pre-selection of a connection in the connection
        dialog, but the default value of the function of the main window is None, so normally, there is no
        pre-selection.
        """

        # Check, if self.parent().parent() is a QMainWindow.
        if isinstance(self.parent().parent(), QMainWindow):
            # Use the function of the main window for activating a new connection dialog.
            self.parent().parent().activate_new_connection_dialog(current_selection_identifier)

    def sort_tree(self):
        """
        Sort the tree with its nodes alphabetically. Check, if sorting is enabled and if not, enable it.
        """

        # Check for enabled sorting, if not, proceed.
        if not self.tree_view.isSortingEnabled():
            # Enable sorting.
            self.tree_view.setSortingEnabled(True)

        # Sort in the "wrong" order. This is necessary for the call of this function after a structural change in the
        # tree, for example after adding a new node. This new node needs to be sorted correctly, a simple call of a new
        # sort is not effective and does not change the current order, so a new node is not sorted. To prevent this, a
        # "wrong" sort order is used, so the sort after that is correct.
        self.tree_view.sortByColumn(0, 1)
        # Use the correct sort order for ensuring the right sort for all nodes.
        self.tree_view.sortByColumn(0, 0)

    @staticmethod
    def get_current_query_timeout():
        """
        Get the current timeout of a query.
        """

        # Use the global app configurator to get the current timeout time.
        current_query_timeout = global_app_configurator.get_single_configuration("Timeout")

        # If a timeout cannot be found, set the timeout to 10000.
        if current_query_timeout is None:
            current_query_timeout = 10000

        # Return the timeout.
        return current_query_timeout

    def append_new_node(self, server_node):
        """
        Append a new server node to the list of server nodes and as row to the tree model. Sort the tree after
        appending. This function does not select a potential previous selected node, because this is realized by a
        signal, which ensures the correct handling of the asynchronous thread.
        """

        # Append the server node to the list of server nodes.
        self.server_nodes.append(server_node)
        # Insert the node in the tree. 0 is used, because there is only one column.
        self.tree_model.insertRow(0, server_node)

        # Sort the database tree.
        self.sort_tree()

        self.new_node_added.emit(True)

    def select_previous_selected_index(self, parent_index, first_item, last_item):
        """
        Select a previous selected index. This can be used for a change in a node, so the attribute selected index is
        True. This function is called by the signal rowsInserted. This signal sends the parent index, the first item
        and the last item as parameters.
        """

        # Check, if the selected index is True. This variable contains a boolean, which is set to True for the change of
        # a node.
        if self.selected_index is True:
            # Clear the previous selection.
            self.tree_view.selectionModel().clear()
            # Get the index of the inserted row with the tree model and the first item.
            inserted_row_index = self.tree_model.index(first_item, 0)
            # Set the current selected index as the inserted row index.
            self.tree_view.selectionModel().setCurrentIndex(inserted_row_index, QItemSelectionModel.Select)

    def show_connection_dialog_for_current_node(self, node_information):
        """
        Get the a node as node information and get the database connection parameters of the node. Use the connection
        parameters for identifying a connection identifier and open a connection dialog with a selected identifier. The
        selected identifier is the identifier of the node.
        """

        # Get the connection parameters.
        connection_parameters = node_information.database_connection_parameters
        # Create a connection identifier out of the parameters of the node.
        current_selected_identifier = "{}@{}:{}/{}".format(connection_parameters["user"],
                                                           connection_parameters["host"],
                                                           connection_parameters["port"],
                                                           connection_parameters["database"])

        # Get a new connection dialog with a pre-selection of the currently selected connection of the node.
        self.get_new_connection_dialog(current_selected_identifier)

    def show_table_information_dialog(self, node_information, show_full_definition):
        """
        Show a table information dialog based on a node. The full definition of a table is shown, if the full definition
        is set as True.
        """

        self.table_information_dialog = TableInformationDialog(node_information, show_full_definition)

    def show_permission_dialog(self, node_information):
        """
        Show a permission dialog for the given node.
        """

        self.permission_information_dialog = PermissionInformationDialog(node_information)

    def show_edit_singles_values_dialog(self, current_node):
        """
        Create a table edit dialog for changing single values in the current node.
        """

        self.table_edit_dialog = TableEditDialog(current_node)

    def refresh_current_selected_node(self, current_node):
        """
        Get the current server node and refresh this node with the information about the database connection parameters,
        define the change information and use the index in the global connection store. Store the resulting variables in
        a list for usage in the function for updating the tree connection.
        """

        # Map the database parameters of the server node to the more readable parameters, which are used in the
        # connection store and connection dialog.
        database_parameters = {"Host": current_node.database_connection_parameters["host"],
                               "Database": current_node.database_connection_parameters["database"],
                               "Username": current_node.database_connection_parameters["user"],
                               "Port": current_node.database_connection_parameters["port"],
                               }
        # Define the change information as change, which is normally used for a change in connection parameters. Here,
        # it is used for a refresh.
        change_information = "change"
        # Get the index in the connection store for the database parameters.
        index_in_connection_store = global_connection_store.get_index_of_connection(database_parameters)
        # Get the information in a information list.
        information_list = [database_parameters, change_information, index_in_connection_store]

        # Use the function for updating the tree connection (or the node's connection) with the function for updating.
        self.update_tree_connection(information_list)

    def get_create_statement_of_node(self, current_node):
        """
        Create a database information dialog with the current selected/given node. The dialog contains the create
        statement of the node.
        """

        self.create_information_dialog = NodeCreateInformationDialog(current_node)

    def get_drop_statement_of_database_node(self, current_node):
        """
        Use the current node for getting a drop statement. The drop statement contains an optional part for closing the
        database connection, which can be used by the user for an unsuccessful drop. The query and the database
        connection parameters of the node are used as input parameter for a function of the main window for showing an
        editor with the statement. In addition, postgres as database is chosen as standard database, so a drop is
        executed with the connection to the database postgres.
        """

        # This query/statement does not have to be execute the way it is. The user will have the possibility to execute
        # it after seeing in the GUI, so an SQL injection is not a problem, because the user will have the possibility
        # to edit the statement if necessary.
        optional_close_and_drop_statement = "--SELECT pg_terminate_backend(pg_stat_activity.pid)\n" \
                                            "--FROM pg_stat_activity\n" \
                                            "--WHERE datname='{}'\n" \
                                            "DROP DATABASE {};".format(current_node.name, current_node.name)

        # Get the database connection parameters of the current node. A copy is made, because the database connection
        # parameters are going to be modified.
        parameters_current_node = copy.copy(current_node.database_connection_parameters)
        # Remove the key value pair for timeout, because the timeout is not necessary for the further dictionary
        # comparison.
        parameters_current_node.pop("timeout", None)
        # Set the database to postgres.
        parameters_current_node["database"] = "postgres"

        # The purpose of this whole for block is selecting the database node with the database postgres. To achieve this
        # goal, every server node is checked for the right host, user and database.
        for server_node in self.server_nodes:
            if server_node.database_connection_parameters["host"] == parameters_current_node["host"] and \
                    server_node.database_connection_parameters["user"] == parameters_current_node["user"] \
                    and server_node.database_connection_parameters["port"] == parameters_current_node["port"]:
                # Check every database node as child of a server node and its place in the row count of a server node.
                for server_row in range(server_node.rowCount()):
                    # Get the child node of a server by the row. The child is a database node.
                    database_node = server_node.child(server_row)

                    # Check for a match in the database with the database connection parameters.
                    if database_node.database_connection_parameters["database"] == parameters_current_node["database"]:
                        # Get the new index for the selection by the index of the matching database node.
                        new_index_for_selection = self.tree_model.indexFromItem(database_node)
                        # Select the new index and the database node for the database postgres.
                        self.tree_view.selectionModel().select(new_index_for_selection,
                                                               QItemSelectionModel.SelectCurrent)

        # Use the function of the parent's parent (the main window) for loading an editor with the given connection and
        # the given drop statement.
        self.parent().parent().load_editor_with_connection_and_query(parameters_current_node,
                                                                     optional_close_and_drop_statement)

    def show_materialized_views_of_database_node(self, current_node):
        """
        Show a dialog with the materialized views of the given node.
        """

        self.materialized_view_information_dialog = MaterializedViewInformationDialog(current_node)

    def get_full_data_of_current_table_for_csv_export(self, current_node):
        """
        Export the data of the selected table to a csv file.
        """

        # Use the csv exporter: The data list is None (because there is currently no data list), the connection
        # parameters are based on the parameters of the node (without the timeout) and the table name is the name of the
        # node.
        self.csv_exporter = CSVExporter(self, None, {"host": current_node.database_connection_parameters["host"],
                                                     "user": current_node.database_connection_parameters["user"],
                                                     "database":
                                                         current_node.database_connection_parameters["database"],
                                                     "port": current_node.database_connection_parameters["port"]},
                                        current_node.name)

        # Export and save the csv data.
        self.csv_exporter.export_and_save_csv_data()
        # Connect the success of the export with a message box for showing the success.
        self.csv_exporter.export_complete.connect(lambda: QMessageBox.information(self, "Export Success",
                                                                                  "The csv export was "
                                                                                  "successful."))

        # Connect the failure of the data list with a message box for whoring the error.
        self.csv_exporter.database_query_executor.error.connect(lambda error: QMessageBox.critical(self, "Export Error",
                                                                                                         "The export "
                                                                                                         "failed with "
                                                                                                         "error: {"
                                                                                                         "}".format(
                                                                                                             error[1])))
