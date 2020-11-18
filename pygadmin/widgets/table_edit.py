import copy
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGridLayout, QLabel, QTableView, QMessageBox, QLineEdit, QPushButton, QDialog, QCheckBox

from pygadmin.connectionfactory import global_connection_factory
from pygadmin.database_query_executor import DatabaseQueryExecutor
from pygadmin.models.tablemodel import TableModel
from pygadmin.models.treemodel import TableNode
from pygadmin.configurator import global_app_configurator


class EditTableModel(TableModel):
    """
    Create a sub class of the table model, so editing the cells is possible.
    """

    def __init__(self, data_list):
        """
        Initialize the model with a data list.
        """

        super().__init__(data_list)

    def flags(self, index):
        """
        Define flags for enabling and editing the items in the cells.
        """

        if not index.isValid():
            return Qt.ItemIsEnabled

        return Qt.ItemIsEnabled | Qt.ItemIsEditable

    def setData(self, index, value, role=Qt.DisplayRole):
        """
        Get new data for setting in the table model, defined by the index for setting the new value, the value itself
        and the display role.
        """

        # Get the row and the column of the relevant item based on the index.
        row = index.row()
        column = index.column()

        # Get the relevant row as list for replacing an item.
        relevant_row = list(self.data_list[row + 1])
        # Set the value to the cell in the relevant row, defined by the column.
        relevant_row[column] = value
        # Set the relevant row as tuple in the data list.
        self.data_list[row + 1] = tuple(relevant_row)
        # Append the row and the column to the list of changed row and column tuples, so the marker for a change in the
        # cell is used.
        self.change_list.append((row, column))

        # Emit the signal for a change in the data. The signal must be emitted explicitly for a reimplementation of the
        # function setData.
        self.dataChanged.emit(index, index, [0])

        return True


class TableEditDialog(QDialog):
    """
    Define a widget for editing the current table and update single cells.
    """

    def __init__(self, table_node):
        super().__init__()

        # Check for the correct instance of the given node. This should be a Table Node, because the whole widget is
        # about editing a table.
        if isinstance(table_node, TableNode):
            self.selected_table_node = table_node
            self.init_ui()
            self.init_grid()

        # If the given node has the wrong instance, show the user interface for the error case.
        else:
            self.init_error_ui()

    def init_ui(self):
        """
        Initialize the user interface and the relevant components.
        """

        self.table_model = EditTableModel([])
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        self.table_model.dataChanged.connect(self.process_table_data_change)

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

        # Normally, queries with .format would be unsafe and not recommended. In this case, the query is part of user
        # interface, so the user has already database and table access and can edit this QLineEdit.
        self.query_select_line_edit = QLineEdit("SELECT * FROM {}".format(self.selected_table_node.name))
        # Define a label with the text "WHERE" as part of the query.
        self.where_label = QLabel("WHERE")
        # Define a line edit for possible conditions after the WHERE in the query.
        self.condition_line_edit = QLineEdit()
        # Define a line edit for a limit for the query. The default limit is 1000, so there are 1000 results as a
        # maximum.
        self.limit_line_edit = QLineEdit("LIMIT 1000")

        # Create a button for executing the query with a SELECT for getting the necessary results.
        self.execute_select_button = QPushButton("Execute")
        # Connect the button with the function for executing the select query.
        self.execute_select_button.clicked.connect(self.execute_select_query)

        # Create a label for showing the update statement.
        self.update_label = QLabel()
        # Create a button for executing the update.
        self.update_button = QPushButton("Update")
        self.update_button.clicked.connect(self.execute_update_query)
        self.process_table_data_change()

        # Create a checkbox for another update possibility: Instead of clicking on a button for an update, update the
        # table immediately after an insert.
        self.update_immediately_checkbox = QCheckBox("Update values immediately")
        # Connect the signal for a state change of the checkbox with the method for applying those changes.
        self.update_immediately_checkbox.stateChanged.connect(self.apply_update_immediately_checkbox_changes)
        # Define the name of the checkbox configuration for easier access instead of writing the name every time.
        self.checkbox_configuration_name = "update_table_immediately_after_changes"
        # Initialize the checkbox with its value based on the current saved configuration.
        self.init_update_immediately_checkbox()

        # Execute the select query at the start/initialization of the widget.
        self.execute_select_query()

        # Define a boolean for describing the current query. Before executing a query, this boolean is set to True for
        # a select query and False for all the other queries (update queries). So after an update, a select can be
        # executed, so the new and fresh values are immediately shown.
        self.is_select_query = False

        # Adjust the size of the dialog.
        self.setMaximumSize(900, 300)
        self.showMaximized()
        self.setWindowTitle("Edit {}".format(self.selected_table_node.name))
        self.show()

    def init_grid(self):
        """
        Define a layout as a grid layout for placing the components of the widget.
        """

        # Get the layout as grid layout.
        grid_layout = QGridLayout(self)

        # Set the elements for executing the select query at the top of the widget.
        grid_layout.addWidget(self.query_select_line_edit, 0, 0)
        grid_layout.addWidget(self.where_label, 0, 1)
        grid_layout.addWidget(self.condition_line_edit, 0, 2)
        grid_layout.addWidget(self.limit_line_edit, 0, 3)
        grid_layout.addWidget(self.execute_select_button, 0, 4)
        # Set the table under the select query elements.
        grid_layout.addWidget(self.table_view, 1, 0, 1, 5)

        # Place the checkbox under the table with the data.
        grid_layout.addWidget(self.update_immediately_checkbox, 7, 0)

        # Set the update items under the checkbox for choosing the update option.
        grid_layout.addWidget(self.update_label, 8, 0, 1, 4)
        grid_layout.addWidget(self.update_button, 8, 4)

        grid_layout.setSpacing(10)
        self.setLayout(grid_layout)

    def init_update_immediately_checkbox(self):
        """
        Initialize the value of the checkbox with the saved configuration.
        """

        # Get the checkbox configuration out of the global app configurator.
        checkbox_configuration = global_app_configurator.get_single_configuration(self.checkbox_configuration_name)

        # Set the checkbox to checked, if the configuration is True.
        if checkbox_configuration is True:
            self.update_immediately_checkbox.setChecked(True)

    def init_error_ui(self):
        """
        Show the user interface for the error case with a wrong node type.
        """

        # Get the layout as grid layout.
        grid_layout = QGridLayout(self)
        # Add a label with an error.
        grid_layout.addWidget(QLabel("The given node is not a table node, so editing the table is not possible."), 0, 0)
        self.setLayout(grid_layout)
        self.setMaximumSize(10, 100)
        self.showMaximized()
        # Set the title to an error title.
        self.setWindowTitle("Node Input Error")
        self.show()

    def refresh_data(self, data_list):
        """
        Refresh the data in the table model with the new data list.
        """

        # Set the change list back to an empty list, because after the execution of a query, there will not be any
        # changed data.
        self.table_model.change_list = []
        self.process_table_data_change()
        self.table_model.refresh_data_list(data_list)
        self.table_view.resizeColumnsToContents()

        # If the executed query was not a select query, execute the current select query, so there is a table with
        # result data shown in the table view.
        if self.is_select_query is False:
            self.execute_select_query()

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
        QMessageBox.critical(self, "{}".format(error_title), "The database query failed with the error: "
                                                             "{}".format(error_description))

        # Save the error in the log.
        logging.error("During the process of executing the query, an error occurred: {}".format(error_description),
                      exc_info=True)

    def execute_select_query(self):
        """
        Execute the select query with the help of the database query executor.
        """

        # The current query is a select query, so set the boolean to True.
        self.is_select_query = True

        # Get the current select query.
        select_query = self.get_select_query()

        # The current query is the database query and the current database connection is the database connection.
        self.database_query_executor.database_query = select_query
        self.database_query_executor.database_connection = self.database_connection
        # Execute the query.
        self.database_query_executor.submit_and_execute_query()

    def get_select_query(self):
        """
        Get the current select query based on the text in the select line edit, the condition line edit and the limit
        line edit.
        """

        # Get all texts in the line edit.
        select_query = self.query_select_line_edit.text()
        condition_text = self.condition_line_edit.text()
        limit_text = self.limit_line_edit.text()

        # If the condition is not empty, use the condition with a "WHERE".
        if condition_text != "":
            select_query = "{} {} {}".format(select_query, self.where_label.text(), condition_text)

        # If the limit text is not empty, use a limit.
        if limit_text != "":
            select_query = "{} {}".format(select_query, limit_text)

        # Return the select query without further checking, because a check is processed during the execution of the
        # query. Bad and hacky behavior is possible with the editor. Persons, who use this query, have already full
        # access to the table and the database.
        return select_query

    def process_table_data_change(self):
        """
        Process the current change in the table data with changed and currently not committed data. If there is not any
        changed data, deactivate the button for an update query.
        """

        if not self.table_model.change_list:
            self.update_button.setEnabled(False)
            self.update_label.setText("UPDATE {}".format(self.selected_table_node.name))

            return

        if self.update_button.isEnabled():
            return

        # Get the first changed tuple for creating an update statement.
        change_tuple = self.table_model.change_list[0]
        # Get the row and the column based on the changed tuple.
        row = change_tuple[0] + 1
        column = change_tuple[1]
        # Get the relevant value, which changed, out of the table model data list.
        value = self.table_model.data_list[row][column]

        # Get the header data of the table model data list. Get a copy, so changes do not affect the original data list.
        header_data = copy.copy(self.table_model.data_list[0])
        # Get the column for changes.
        change_column = header_data[column]

        # Delete the column with the value in the header data, so it is not used for creating the WHERE condition.
        del header_data[column]
        # Get the relevant row as list, so changes are possible.
        relevant_row = list(self.table_model.data_list[row])
        # Delete the column with the value in the relevant row, so it is not used for creating the WHERE condition.
        del relevant_row[column]

        # Create the SET part of the statement with the column for the change and the change value.
        set_statement = "SET {}='{}'".format(change_column, value)

        # Create the beginning of the WHERE condition for further adding of the single column conditions with its
        # values.
        where_condition = "WHERE "

        # Add every column with its value as condition.
        for column_name_number in range(len(header_data)):
            # Create the condition part with the column and the value.
            condition = "{}='{}'".format(header_data[column_name_number],
                                         relevant_row[column_name_number])

            # Add the created condition to the WHERE condition.
            where_condition += condition

            # If the condition is not the last one, add an AND, so further conditions are coming.
            if column_name_number != len(header_data) - 1:
                where_condition += " AND "

            # At this point, the end of the statement is reached and a semicolon is added.
            else:
                where_condition += ";"

        # Show the update statement in the label for the update statement.
        update_statement = "{} {} {}".format(self.update_label.text(), set_statement, where_condition)

        # Set the text in the update label.
        self.update_label.setText(update_statement)
        # Activate the update button.
        self.update_button.setEnabled(True)

        # If the checkbox for immediate updates is checked, execute the update query.
        if self.update_immediately_checkbox.isChecked():
            self.execute_update_query()

    def execute_update_query(self):
        """
        Execute the update query.
        """

        # The current query is an update query and not a select query.
        self.is_select_query = False

        # The update statement is the text in the update label.
        update_statement = self.update_label.text()
        self.database_query_executor.database_query = update_statement
        self.database_query_executor.database_connection = self.database_connection
        # Execute the query.
        self.database_query_executor.submit_and_execute_query()

    def apply_update_immediately_checkbox_changes(self):
        """
        Apply the changes for a(n un)checked checkbox: Change the GUI and save the current configuration.
        """

        # Get the current checked value.
        checked = self.update_immediately_checkbox.isChecked()
        # (De)activate the GUI elements for a manual update after a change in the table.
        self.de_activate_update_elements(checked)
        # Set the current configuration and and save the configuration in the global app configurator.
        global_app_configurator.set_single_configuration(self.checkbox_configuration_name, checked)
        global_app_configurator.save_configuration_data()

    def de_activate_update_elements(self, is_active):
        """
        (De)activate the GUI elements for manual updating. If the checkbox is active, deactivate the elements.
        """

        self.update_label.setVisible(not is_active)
        self.update_button.setVisible(not is_active)

