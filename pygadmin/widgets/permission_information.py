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

        # Define two booleans for a query check: If the query for the required parameter is executed, set the check to
        # True.
        self.super_user_check = False
        self.function_table_check = False

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
        grid_layout.addWidget(self.table_view, 1, 0)

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
        Process the result data based on the executed queries and the instance of the given node.
        """

        # If the super user check is True, the query has been executed. If the function table check is False, the
        # related query needs to be executed.
        if self.super_user_check is True and self.function_table_check is False:
            # Update the super user information in the GUI.
            self.update_super_user_information(data_list)
            # Check for a database node: For databases, there are functions given.
            if isinstance(self.selected_node, DatabaseNode):
                self.get_function_permissions()

            # For a Table or a View node, there are special permissions on the table or view.
            else:
                self.get_table_view_permissions()

        # In this case, the function for getting the function or table permissions is executed and has now a data list
        # as result.
        else:
            self.update_information_table(data_list)

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
        self.database_query_executor.submit_and_execute_query()

    def update_super_user_information(self, super_user_result_list):
        """
        Update the super user information in the GUI based on the result list after the query execution.
        """

        # If the list is longer than 1, there is a usable result.
        if len(super_user_result_list) > 1:
            # Define a list for super users, because only there names are necessary.
            super_user_list = []
            # Get every super user in a query.
            for user_number in range(len(super_user_result_list)-1):
                # Get the first parameter of the tuple with the result. This is the super user.
                super_user_list.append(super_user_result_list[user_number+1][0])

            # Define a text for the GUI.
            self.super_user_label.setText("The following super users were found: ")

            # Add every super user to the label.
            for user in super_user_list:
                self.super_user_label.setText("{} {}".format(self.super_user_label.text(), user))

        # Show an information, if there is no super user.
        else:
            self.super_user_label.setText("No super user was found.")

    def update_information_table(self, data_list):
        """
        Update the table with the new data.
        """

        self.table_model.refresh_data_list(data_list)
        self.table_view.resizeColumnsToContents()




