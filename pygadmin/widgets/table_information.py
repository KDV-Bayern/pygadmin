import logging

from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QTableView, QMessageBox

from pygadmin.models.treemodel import TableNode
from pygadmin.models.tablemodel import TableModel
from pygadmin.connectionfactory import global_connection_factory
from pygadmin.database_query_executor import DatabaseQueryExecutor
from pygadmin.widgets.widget_icon_adder import IconAdder


class TableInformationDialog(QDialog):
    """
    Create a dialog for showing the definition of a table.
    """

    def __init__(self, selected_table_node, full_definition=True):
        super().__init__()
        self.setModal(False)

        icon_adder = IconAdder()
        icon_adder.add_icon_to_widget(self)

        # Check for the correct instance of the given node.
        if isinstance(selected_table_node, TableNode):
            # Use the given node as base and root for further information as attribute.
            self.selected_table_node = selected_table_node
            # Set the boolean for showing a full description to the given value. The default value is True.
            self.full_definition = full_definition
            # Initialize the user interface.
            self.init_ui()
            # Initialize the grid layout.
            self.init_grid()

        # Activate the else branch for a node with the wrong type as input parameter.
        else:
            # Save an error in the log.
            logging.error("The given node {} is not a Table Node and as a consequence, the specific actions for a Table"
                          " Node like showing the definition and the information are not "
                          "possible.".format(selected_table_node))

            # Initialize a UI for the error case.
            self.init_error_ui()

    def init_ui(self):
        """
        Initialize the user interface with the relevant components.
        """

        # Use the table model as table model and use an empty data list.
        self.table_model = TableModel([])
        # Use a table view with the customized model as model.
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)

        # Get the connection parameters based on the table node.
        connection_parameters = self.selected_table_node.database_connection_parameters

        # Get the database connection based on the parameters of the table node.
        self.database_connection = global_connection_factory.get_database_connection(connection_parameters["host"],
                                                                                     connection_parameters["user"],
                                                                                     connection_parameters["database"],
                                                                                     connection_parameters["port"],
                                                                                     connection_parameters["timeout"])
        # Define a query executor.
        self.database_query_executor = DatabaseQueryExecutor()
        # Connect the resulting data list with a function for refreshing the data in the table model.
        self.database_query_executor.result_data.connect(self.refresh_data)
        # Connect the error with a function for processing an error.
        self.database_query_executor.error.connect(self.process_error)

        # Use the function for getting the table information.
        self.get_table_information()

        # Adjust the size of the dialog.
        self.setMaximumSize(720, 300)
        self.showMaximized()
        self.setWindowTitle("Definition of {}".format(self.selected_table_node.name))
        self.show()

    def init_grid(self):
        """
        Initialize the layout as grid layout.
        """

        # Define the layout as grid layout.
        grid_layout = QGridLayout(self)
        # Set the table.
        grid_layout.addWidget(self.table_view, 0, 0)
        grid_layout.setSpacing(10)
        self.setLayout(grid_layout)

    def init_error_ui(self):
        """
        Use a small UI for the error case of a wrong node type as input parameter.
        """

        # Get the layout as grid layout.
        grid_layout = QGridLayout(self)
        # Add a label with an error.
        grid_layout.addWidget(QLabel("The given node is not a table node, so a definition cannot be shown."), 0, 0)
        self.setLayout(grid_layout)
        self.setMaximumSize(10, 100)
        self.showMaximized()
        # Set the title to an error title.
        self.setWindowTitle("Node Input Error")
        self.show()

    def get_table_information(self):
        """
        Execute the database query for getting the table information.
        """

        # Check for the value of the boolean for showing the full definition.
        if self.full_definition is True:
            # Define the database query for the full definition.
            database_query = "SELECT * FROM information_schema.columns WHERE table_name=%s;"

        else:
            # Define the database query for showing the minimal definition.
            database_query = "SELECT column_name, data_type, character_maximum_length " \
                             "FROM information_schema.columns WHERE table_name=%s; "

        # Define the parameter, which is the name of the node.
        database_query_parameter = [self.selected_table_node.name]

        # Set the current database connection as database connection of the executor.
        self.database_query_executor.database_connection = self.database_connection
        # Set the database query.
        self.database_query_executor.database_query = database_query
        # Set the database parameter.
        self.database_query_executor.database_query_parameter = database_query_parameter
        # Execute the database query.
        self.database_query_executor.submit_and_execute_query()

    def refresh_data(self, result_data_list):
        """
        Refresh the data in the tree model with a new data list, containing the new values.
        """

        self.table_model.refresh_data_list(result_data_list)
        self.table_view.resizeColumnsToContents()

    def process_error(self, error):
        """
        Get the current error by a signal, which is a tuple wih the title of the error and the description. Show the
        error to the user and save the message in the log.
        """

        # Get the title out of the tuple.
        error_title = error[0]
        # Get the description out of the tuple.
        error_description = error[1]

        # Show the error to the user.
        QMessageBox.critical(self, "{}".format(error_title), "The database query for getting the definition failed with"
                                                             " the error: {}".format(error_description))

        # Save the error in the log.
        logging.error("During the process of executing the query, an error occurred: {}".format(error_description),
                      exc_info=True)
