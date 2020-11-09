import logging

from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QTableView, QMessageBox

from pygadmin.connectionfactory import global_connection_factory
from pygadmin.database_query_executor import DatabaseQueryExecutor
from pygadmin.models.tablemodel import TableModel
from pygadmin.models.treemodel import TableNode, ViewNode, DatabaseNode


class PermissionInformationDialog(QDialog):
    """
    Create a dialog for showing the information about the permissions on a database, table or view.
    """

    def __init__(self, selected_node):
        """
        Get a selected node as input parameter, so the information is based on the given node. After a type check,
        initialize the relevant attributes with initializing the UI and the layout.
        """

        super().__init__()
        self.setModal(True)

        # Check for the correct instance of the given node. Table, View and Database nodes are valid, because the
        # required information exists for these nodes.
        if isinstance(selected_node, TableNode) or isinstance(selected_node, ViewNode) \
                or isinstance(selected_node, DatabaseNode):
            # Set the given node as attribute for easier access.
            self.selected_node = selected_node
            # Initialize the UI and the grid layout.
            self.init_ui()
            self.init_grid()

        # Save and show an error in the else branch, because the node has the wrong instance.
        else:
            # Save an error in the log.
            logging.error("The given node {} is not a Table, View or Database node. As a consequence, the specific "
                          "actions for checking permissions are not available.".format(selected_node))

            # Initialize a UI for the error case.
            self.init_error_ui()

    def init_ui(self):
        """
        Initialize the user interface with the relevant components for showing and processing the information.
        """

        # Create a label for showing the super users.
        self.super_user_label = QLabel()
        # Create a label for showing the owners.
        self.owner_label = QLabel()
        # Create a table model for showing the result of a query in a table.
        self.table_model = TableModel([])
        # Create a table view for the model for showing the data in the GUI.
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)

        # Get the database connection parameters of the selected node for usage in the database query executor later.
        database_connection_parameters = self.selected_node.database_connection_parameters
        # Get the database connection related to the parameters, because the database query executor requires a database
        # connection and not connection parameters.
        self.database_connection = global_connection_factory.get_database_connection(
            database_connection_parameters["host"],
            database_connection_parameters["user"],
            database_connection_parameters["database"],
            database_connection_parameters["port"],
            database_connection_parameters["timeout"])

        # Create a database query executor for executing the relevant queries for the requested permission information.
        self.database_query_executor = DatabaseQueryExecutor()
        # Connect the signal for a successful query and its data to the function for processing the result data, so the
        # permission information is shown in the GUI at the end.
        self.database_query_executor.result_data.connect(self.process_result_data)
        # Connect the error signal to the function for processing the error, so the user is informed about it.
        self.database_query_executor.error.connect(self.process_error)

        # Define three booleans for a query check: If the query for the required parameter is executed, set the check to
        # True.
        self.super_user_check = False
        self.function_table_check = False
        self.database_owner_check = False

        # Get the super users, which triggers also the query for getting the function data/table data.
        self.get_super_users()

        # Adjust the size of the dialog.
        self.setMaximumSize(720, 300)
        self.showMaximized()
        self.setWindowTitle("Permissions for {}".format(self.selected_node.name))
        self.show()

    def init_grid(self):
        """
        Initialize the grid layout.
        """

        grid_layout = QGridLayout(self)
        grid_layout.addWidget(self.super_user_label, 0, 0)
        grid_layout.addWidget(self.owner_label, 1, 0)
        grid_layout.addWidget(self.table_view, 2, 0)

        grid_layout.setSpacing(10)
        self.setLayout(grid_layout)

    def init_error_ui(self):
        """
        Use a small UI for the error case of a wrong node instance as input parameter.
        """

        # Get the layout as grid layout.
        grid_layout = QGridLayout(self)
        # Add a label with an error.
        grid_layout.addWidget(QLabel("The given node is not a Table, View or Database node, so a definition cannot "
                                     "be shown."), 0, 0)
        self.setLayout(grid_layout)
        self.setMaximumSize(10, 100)
        self.showMaximized()
        # Set the title to an error title.
        self.setWindowTitle("Node Input Error")
        self.show()

    def process_result_data(self, data_list):
        """
        Process the result data based on the executed queries and the instance of the given node. First of all, the
        super users are updated. If the selected node is a database node, the owners are updated. After that, the
        function or table view permissions are updated.
        """

        # Check for the function and table updates. If this boolean is True, the data inside the result table needs an
        # update.
        if self.function_table_check is True:
            self.update_information_table(data_list)

            # End the function with a return, because now everything is updated.
            return

        # TODO: Find a way to update the super users without an overwrite by the owners
        self.update_super_user_owner_information(data_list, "super users")

        if self.database_owner_check is False and isinstance(self.selected_node, DatabaseNode):
            self.get_database_owners()

        if self.database_owner_check is True:
            if isinstance(self.selected_node, DatabaseNode):
                self.update_super_user_owner_information(data_list, "owners")
                self.get_function_permissions()

            else:
                self.get_table_view_permissions()

    def process_error(self, error):
        """
        Process the given error of a database execution fail with a message in the log and a message in the GUI.
        """

        logging.error("During the query execution, an error occurred: {}".format(error))
        QMessageBox.critical(self, "Information Query Error", "The query for getting the information could not"
                                                              " be executed with the error {}".format(error))

    def get_table_view_permissions(self):
        """
        Get the permissions for a table based on a query and with help of the database query executor.
        """

        # Define the query.
        database_query = "SELECT * FROM information_schema.role_table_grants WHERE table_name=%s"

        # Use the name of the table or view as parameter, so information about this table or view can be found.
        database_query_parameter = [self.selected_node.name]

        # Use the database connection for the executor.
        self.database_query_executor.database_connection = self.database_connection
        # Use the query and the parameter.
        self.database_query_executor.database_query = database_query
        self.database_query_executor.database_query_parameter = database_query_parameter
        # A function for checking permissions on a function or table is now executed, so this value is True now.
        self.function_table_check = True
        # Execute the query.
        self.database_query_executor.submit_and_execute_query()

    def get_function_permissions(self):
        """
        Get the permissions for a table based on a query and with help of the database query executor.
        """

        # Define the required query.
        database_query = "SELECT * FROM information_schema.role_routine_grants WHERE specific_schema='public'"

        # Set the connection and the query.
        self.database_query_executor.database_connection = self.database_connection
        self.database_query_executor.database_query = database_query
        # A function for checking permissions on a function or table is now executed, so this value is True now.
        self.function_table_check = True
        self.database_query_executor.submit_and_execute_query()

    def get_database_owners(self):
        # TODO: Docu
        database_query = "SELECT pg_catalog.pg_get_userbyid(d.datdba) as Owner FROM pg_catalog.pg_database d " \
                         "WHERE d.datname =%s"

        database_query_parameter = [self.selected_node.name]

        self.database_query_executor.database_connection = self.database_connection
        self.database_query_executor.database_query = database_query
        self.database_query_executor.database_query_parameter = database_query_parameter
        self.database_owner_check = True
        self.database_query_executor.submit_and_execute_query()

    def get_super_users(self):
        """
        Get the super users based on a query and with help of the database query executor.
        """

        # Define the query.
        database_query = "SELECT usename FROM pg_user WHERE usesuper='True'"
        # Use the relevant values for the query executor.
        self.database_query_executor.database_connection = self.database_connection
        self.database_query_executor.database_query = database_query
        # Set the boolean to True, because now, the super users are loaded.
        self.super_user_check = True

        # TODO: Docu (or better usage of the check boolean)
        if not isinstance(self.selected_node, DatabaseNode):
            self.database_owner_check = True

        self.database_query_executor.submit_and_execute_query()

    def update_super_user_owner_information(self, result_list, user_type):
        """
        Update the super user or owner information in the GUI based on the result list after the query execution.
        """

        # Check for the given user type.
        if user_type == "super users":
            # Use the super user label as label.
            label = self.super_user_label

        else:
            # Use the owner label as label.
            label = self.owner_label

        # If the list is longer than 1, there is a usable result.
        if len(result_list) > 1:
            # Define a list for super users and owners, because only there names are necessary.
            super_user_owner_list = []
            # Get every super user in a query.
            for user_number in range(len(result_list) - 1):
                # Get the first parameter of the tuple with the result. This is the super user.
                super_user_owner_list.append(result_list[user_number + 1][0])

            # Define a text for the GUI with a replaceable string for the super users or the owners.
            label.setText("The following {} were found: ".format(user_type))

            # Add every super user or owner to the label.
            for user in super_user_owner_list:
                label.setText("{} {}".format(label.text(), user))

        # Show an information, if there is no super user or owner.
        else:
            label.setText("No {} were found.".format(user_type))

    def update_information_table(self, data_list):
        """
        Update the table with the new data.
        """

        self.table_model.refresh_data_list(data_list)
        self.table_view.resizeColumnsToContents()




