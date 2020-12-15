import logging

from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QTableView, QMessageBox

from pygadmin.connectionfactory import global_connection_factory
from pygadmin.database_query_executor import DatabaseQueryExecutor
from pygadmin.models.tablemodel import TableModel
from pygadmin.models.treemodel import DatabaseNode


class MaterializedViewInformationDialog(QDialog):
    """
    Create a dialog for showing information about the materialized views of a database node.
    """

    def __init__(self, selected_database_node):
        super().__init__()
        self.setModal(True)

        # Continue with the normal initialization of the dialog, if the instance is correct.
        if isinstance(selected_database_node, DatabaseNode):
            self.selected_node = selected_database_node
            self.init_ui()
            self.init_grid()

        # Show an error in the log and the UI.
        else:
            logging.error("The given node {} is not a Table, View or Database node. As a consequence, the specific "
                          "actions for checking permissions are not available.".format(selected_database_node))

            self.init_error_ui()

    def init_ui(self):
        """
        Initialize a user interface.
        """

        # Create a table model and table view for showing the resulting data.
        self.table_model = TableModel([])
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)

        # Prepare the database connection parameters for further usage in the database query executor.
        database_connection_parameters = self.selected_node.database_connection_parameters
        self.database_connection = global_connection_factory.get_database_connection(
            database_connection_parameters["host"],
            database_connection_parameters["user"],
            database_connection_parameters["database"],
            database_connection_parameters["port"],
            database_connection_parameters["timeout"])

        # Create the database query executor for getting the materialized views by a query.
        self.database_query_executor = DatabaseQueryExecutor()
        # Connect the signal for the result with displaying the result data.
        self.database_query_executor.result_data.connect(self.process_result_data)
        # Connect the signal for an error with displaying information about an error.
        self.database_query_executor.error.connect(self.process_error_message)

        # Get the materialized views.
        self.get_materialized_views()

        # Adjust the size of the dialog.
        self.setMaximumSize(720, 300)
        self.showMaximized()
        self.setWindowTitle("Materialized views for {}".format(self.selected_node.name))
        self.show()

    def init_grid(self):
        """
        Initialize the grid layout.
        """

        grid_layout = QGridLayout(self)
        grid_layout.addWidget(self.table_view)

        grid_layout.setSpacing(10)
        self.setLayout(grid_layout)

    def init_error_ui(self):
        """
        Use a small UI for the error case of a wrong node instance as input parameter.
        """

        # Get the layout as grid layout.
        grid_layout = QGridLayout(self)
        # Add a label with an error.
        grid_layout.addWidget(QLabel("The given node is not a Database node, so materialized views cannot be "
                                     "shown."), 0, 0)
        self.setLayout(grid_layout)
        self.setMaximumSize(10, 100)
        self.showMaximized()
        # Set the title to an error title.
        self.setWindowTitle("Node Input Error")
        self.show()

    def get_materialized_views(self):
        """
        Get the materialized views of a database node based on a query.
        """

        # Define the query: Get the information of pg_matviews.
        database_query = "SELECT * FROM pg_matviews;"
        # Set the relevant parameters of the query executor.
        self.database_query_executor.database_connection = self.database_connection
        self.database_query_executor.database_query = database_query
        # Execute!
        self.database_query_executor.submit_and_execute_query()

    def process_result_data(self, data_list):
        """
        Process the result data: Show the data list in the table model.
        """

        self.table_model.refresh_data_list(data_list)
        self.table_view.resizeColumnsToContents()

    def process_error_message(self, error_message):
        """
        Process the error message with a log entry and an error message box.
        """

        logging.error("During the query execution, an error occurred: {}".format(error_message))
        QMessageBox.critical(self, "Information Query Error", "The query for getting the information could not"
                                                              " be executed with the error {}".format(error_message))


