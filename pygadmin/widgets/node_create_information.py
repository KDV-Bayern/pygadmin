import logging
import os

from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel
from PyQt5.QtCore import Qt

from pygadmin.models.treemodel import DatabaseNode, TableNode, ViewNode
from pygadmin.database_dumper import DatabaseDumper
from pygadmin.widgets.widget_icon_adder import IconAdder


class NodeCreateInformationDialog(QDialog):
    """
    Create a dialog for showing the information about a database node, in this case the create statement.
    """

    def __init__(self, selected_node):
        super().__init__()
        self.setModal(False)
        # Add the pygadmin icon as window icon.
        icon_adder = IconAdder()
        icon_adder.add_icon_to_widget(self)

        # Check for the correct instance of the given node.
        if isinstance(selected_node, DatabaseNode) or isinstance(selected_node, TableNode) or \
                isinstance(selected_node, ViewNode):
            # Use the given node as base and root for further information as attribute.
            self.selected_node = selected_node
            # Initialize the user interface.
            self.init_ui()
            # Initialize the grid layout.
            self.init_grid()

        # Activate the else branch for a node with the wrong type as input parameter.
        else:
            # Save an error in the log.
            logging.error("The given node {} is not a Database/Table/View Node and as a consequence, the specific "
                          "actions for a such a node like showing the definition and the information are not "
                          "possible.".format(selected_node))

            # Initialize a UI for the error case.
            self.init_error_ui()

    def init_ui(self):
        """
        Initialize the user interface.
        """

        # Get the create statement.
        create_statement = self.get_node_create_statement()
        # Set the create statement in a label.
        self.create_statement_label = QLabel(create_statement)
        # Enable the multi line mode.
        self.create_statement_label.setWordWrap(True)
        # Make the text of the label selectable by the mouse.
        self.create_statement_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.setMaximumSize(720, 300)
        self.showMaximized()
        self.setWindowTitle("Create Statement of {}".format(self.selected_node.name))
        self.show()

    def init_grid(self):
        """
        Initialize the grid layout.
        """

        grid_layout = QGridLayout(self)
        grid_layout.addWidget(self.create_statement_label, 0, 0)
        grid_layout.setSpacing(10)
        self.setLayout(grid_layout)

    def init_error_ui(self):
        """
        Use a small UI for the error case of a wrong node type as input parameter.
        """

        # Get the layout as grid layout.
        grid_layout = QGridLayout(self)
        # Add a label with an error.
        grid_layout.addWidget(QLabel("The given node is not a database node, so a definition cannot be shown."), 0, 0)
        self.setLayout(grid_layout)
        self.setMaximumSize(10, 100)
        self.showMaximized()
        # Set the title to an error title.
        self.setWindowTitle("Node Input Error")
        self.show()

    def get_node_create_statement(self):
        """
        Get the create statement of the given database with pg_dump and the class around the subprocess.
        """

        # Get the connection parameters of the database node.
        connection_parameters = self.selected_node.database_connection_parameters
        # Create a class for the dump with the required connection parameters and information about the node.
        database_dump = DatabaseDumper(connection_parameters["user"], connection_parameters["database"],
                                       connection_parameters["host"], connection_parameters["port"],
                                       self.selected_node.get_node_type(), self.selected_node.name)

        # Get the create statement with the relevant create/alter part.
        dump_result = database_dump.dump_database_and_clean_result()

        # Check for a valid result of the database dump. If the result list is empty, something went wrong.
        if not dump_result:
            # Define an error for the user.
            error_string = "The dump failed. Please check the log for further information or check the pg_dump " \
                           "executable in the configuration settings."

            # Return the error string, so instead of a valid result, the error is shown.
            return error_string

        # Make a string out of the list.
        result_string = "".join(dump_result)

        # Define a list of words for splitting the result string. Before these words, there will be a newline for better
        # reading.
        split_list = ["WITH", "ENCODING", "LC_COLLATE", "LC_CTYPE", "LC_TYPE", "ALTER"]

        # Check every string in the defined split list.
        for split_string in split_list:
            # If a word for splitting occurs, create a newline before the word.
            result_string = result_string.replace(split_string, os.linesep + split_string)

        return result_string
