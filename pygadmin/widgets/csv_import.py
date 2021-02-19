from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton, QMessageBox, QLineEdit, \
    QInputDialog

from pygadmin.csv_importer import CSVImporter
from pygadmin.widgets.widget_icon_adder import IconAdder
from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton, QMessageBox, QLineEdit, \
    QInputDialog

from pygadmin.csv_importer import CSVImporter
from pygadmin.widgets.widget_icon_adder import IconAdder


class CSVImportDialog(QDialog):
    """
    Create a dialog for importing a table out of a csv file to a table in the database with all given data in the csv
    file. User interaction is necessary for editing the names and data types of the column.
    """

    def __init__(self, database_connection, csv_file):
        super().__init__()
        # Add the pygadmin icon as window icon.
        icon_adder = IconAdder()
        icon_adder.add_icon_to_widget(self)

        # Get the result of an input dialog for getting the delimiter of the csv file.
        delimiter_result = self.init_delimiter_question(csv_file)

        # The second variable in the tuple of the input dialog result contains the success. So if the user cancels the
        # dialog, the result contains False.
        if delimiter_result[1] is False:
            # Inform the user about the aborting of the process.
            QMessageBox.information(self, "Abort", "The csv import process has been aborted by the user.")
            # End the function with a return.
            return

        # At this point, the input dialog for the delimiter was successful, so the result given by the user can be used
        # as delimiter for the csv file.
        self.csv_importer = CSVImporter(database_connection, csv_file, delimiter=delimiter_result[0])

        # If the csv file exists, initialize the relevant parts of the dialog.
        if self.csv_importer.check_existence_csv_file():
            # Parse the given csv file.
            self.csv_importer.parse_csv_file()

            # Try to get the data types of the csv file. A fail or an error is possible and caused by a wrong delimiter.
            try:
                # Get the data types of the given csv file.
                self.csv_importer.assume_data_types()

            # Catch the error with showing the error to the user and end the initialization of the dialog.
            except IndexError:
                self.init_error_ui("The given delimiter is wrong, so the csv file {} cannot be processed.".format(
                    csv_file))
                return

            # Initialize the user interface.
            self.init_ui()
            # Initialize the grid layout.
            self.init_grid()

        # Show an error for a non existing file.
        else:
            self.init_error_ui("The given csv file {} is invalid".format(csv_file))

    def init_delimiter_question(self, csv_file):
        """
        Create an input dialog for getting the delimiter of the csv file.
        """

        # Use an input dialog for getting the csv delimiter with the default of a comma, because it is called comma
        # separated values.
        delimiter_result = QInputDialog.getText(self, "CSV Delimiter", "What is the delimiter of your csv file "
                                                                       "{}?".format(csv_file), text=",")

        # Return the result of the dialog with the input and the success of the dialog.
        return delimiter_result

    def init_ui(self):
        """
        Initialize the user interface.
        """

        # Get the create statement of the given csv file based on the column names in the file and the data types.
        create_statement = self.csv_importer.get_create_statement()

        # Start the statement with a "CREATE TABLE".
        self.create_table_start_label = QLabel("CREATE TABLE ")
        # Get a line edit with the name of the table.
        self.table_name_line_edit = QLineEdit(self.csv_importer.table_name)
        # Open the definition part of the create statement with an (.
        self.open_label = QLabel("(")

        # Get the list of column definition parameters by splitting the create statement at every newline.
        column_definition_list = create_statement.split("\n")
        # Delete the first element, because this element does only contain a "CREATE TABLE".
        del column_definition_list[0]
        # Delete the last element as closing part of the statement.
        del column_definition_list[len(column_definition_list) - 1]

        # Split the column definition at commas.
        column_definition_list = [column_definition.replace(",", "") for column_definition in column_definition_list]

        # Create a list for the column line edits, so there is a class-wide access to this list.
        self.column_line_edit_list = []

        # Process every column in the list.
        for column in column_definition_list:
            # Split the column at whitespaces, so the
            identifier_list = column.split(" ")
            # Get the index of the last element based on the length of the identifier list.
            last_element_index = len(identifier_list) - 1
            # The last item is the column data type, which is only one word with any whitespaces.
            column_data_type = identifier_list[last_element_index]
            # Delete the last element from the list, because it is not necessary anymore and possibly disturbs the
            # process of getting the column name.
            del identifier_list[last_element_index]
            # Define an empty string for the column name for appending the name in the process.
            column_name = ""

            # If the length of the list is now 1, the standard case is the correct one: The first element of the list is
            # the name of the column, plain and simple.
            if len(identifier_list) == 1:
                column_name = identifier_list[0]

            # The edge case is for column names with a whitespace in the column name. Every part of the name is split
            # at the whitespace before, so it will be whole again.
            else:
                for item in identifier_list:
                    column_name = "{} {}".format(column_name, item)

            # Create a line edit for the column name.
            column_name_line_edit = QLineEdit(column_name)
            # Create a line edit for the column data type.
            column_data_type_line_edit = QLineEdit(column_data_type)
            # Append the two line edits to the list of all line edits for further usage.
            self.column_line_edit_list.append((column_name_line_edit, column_data_type_line_edit))

        # Define a label for closing the statement.
        self.close_label = QLabel(");")

        # Use a button for creating the given table.
        self.create_button = QPushButton("Create Table")
        # Connect the button with the function for creating the table.
        self.create_button.clicked.connect(self.create_table)

        # Create a drop button for dropping the table.
        self.drop_button = QPushButton("Drop Table")
        # Connect the button with the function for actually dropping the table.
        self.drop_button.clicked.connect(self.drop_table)

        # Create an insert button for inserting the data.
        self.insert_button = QPushButton("Insert Data")
        # Connect the button with the function for inserting the data.
        self.insert_button.clicked.connect(self.insert_data)

        self.create_and_insert_button = QPushButton("Create Table and Insert Data")
        self.create_and_insert_button.clicked.connect(self.create_table_and_insert_data)

        # Define two parameters/attributes for controlling the number of expected inserts.
        self.number_of_inserts = 0
        self.executed_inserts = 0

        # Define an attribute for the usage after a create statement: If the attribute is True, the data is inserted
        # right after the creation of the table.
        self.proceed_with_insert = False

        # Connect the signals for the result data and the error with functions for processing.
        self.csv_importer.database_query_executor.result_data.connect(self.process_sql_success)
        self.csv_importer.database_query_executor.error.connect(self.process_sql_error)

        self.show()

    def init_grid(self):
        """
        Initialize the grid part of the layout.
        """

        # Get the grid layout.
        grid_layout = QGridLayout(self)

        # Place the first three widgets: The label for the beginning of the CREATE, the name and the opening of the
        # table.
        grid_layout.addWidget(self.create_table_start_label, 0, 0)
        grid_layout.addWidget(self.table_name_line_edit, 0, 1)
        grid_layout.addWidget(self.open_label, 0, 2)

        # Define a line count for placing the elements of the column line edit list.
        line_edit_count = 1

        # Place all components of the column line edit list.
        for line_edits in self.column_line_edit_list:
            # Place the first element of the tuple, the name of the column.
            grid_layout.addWidget(line_edits[0], line_edit_count, 0)
            # Place the second element of the tuple, the data type of the column on the right of the name.
            grid_layout.addWidget(line_edits[1], line_edit_count, 1)
            # Increment the count, so the next tuple of line edits is placed under those ones.
            line_edit_count += 1

        # Place the close label at the end of CREATE.
        grid_layout.addWidget(self.close_label, line_edit_count, 0)
        # Set the create and insert button at the end of the statement, created by the line edits.
        grid_layout.addWidget(self.create_and_insert_button, line_edit_count, 1)
        # Set the drop button on the right of the create and insert button.
        grid_layout.addWidget(self.drop_button, line_edit_count, 2)
        # Set the insert and the create button under the row with the create and insert button.
        grid_layout.addWidget(self.insert_button, line_edit_count+1, 0)
        grid_layout.addWidget(self.create_button, line_edit_count+1, 1)

        # Set the spacing of the grid.
        grid_layout.setSpacing(10)
        # Set the layout to the grid layout.
        self.setLayout(grid_layout)

    def init_error_ui(self, message):
        """
        Initialize the user interface for the error case and use an error message for specifying the error.
        """

        # Get the layout as grid layout.
        grid_layout = QGridLayout(self)
        # Add a label with an error.
        grid_layout.addWidget(QLabel(message), 0, 0)
        self.setLayout(grid_layout)
        self.setMaximumSize(10, 100)
        self.showMaximized()
        # Set the title to an error title.
        self.setWindowTitle("File Error")
        self.show()

    def create_table(self):
        """
        Build the create statement specified by the user in the line edits and use the csv importer for execution of the
        statement.
        """

        create_statement = self.get_user_create_statement()
        self.csv_importer.create_table_for_csv_data(create_statement)

    def get_user_create_statement(self):
        """
        Build the create statement specified by the user in the line edits.
        """

        # Initialize the statement with the begin, the table name and the opening (.
        create_statement = "{}{} {}\n".format(self.create_table_start_label.text(), self.table_name_line_edit.text(),
                                              self.open_label.text())

        # Iterate over the list of column line edits for getting the user data.
        for line_edit_count in range(len(self.column_line_edit_list)):
            # Get the line edit tuple.
            line_edit = self.column_line_edit_list[line_edit_count]
            # The first element contains the line edit for name of the column.
            name_line_edit = line_edit[0]
            # The second element contains the line edit for the data type of the column.
            datatype_line_edit = line_edit[1]

            # If the current line edit tuple is not the last one, use a comma as comma value for separating the column
            # definitions.
            if line_edit_count != len(self.column_line_edit_list) - 1:
                comma_value = ","

            # If the current line edit tuple is the last one, a comma is not necessary.
            else:
                comma_value = ""

            # Add the column definition to the create statement.
            create_statement = "{} {} {}{}\n".format(create_statement, name_line_edit.text(), datatype_line_edit.text(),
                                                     comma_value)

        # Add the closing text to the create statement.
        create_statement = "{}{}".format(create_statement, self.close_label.text())

        # Return the result.
        return create_statement

    def drop_table(self):
        """
        Drop the table specified in the line edit with the table name.
        """

        table_name = self.table_name_line_edit.text()
        self.csv_importer.drop_table(table_name)

    def process_sql_success(self, result):
        """
        Process the result of the table creation or dropping.
        """

        # The parameter result contains a list. If the list is not empty, a success can be processed.
        if result:
            # Get the title of the result list for further usage as QMessageBox title.
            title = result[0][0]
            # A data definition query has been executed.
            if self.number_of_inserts == 0 and self.executed_inserts == 0:
                # Get the message.
                message = result[1][0]
                # Show the title and the message to the user.
                QMessageBox.information(self, title, message)

                # Check the attribute for proceeding with the insert of the data.
                if self.proceed_with_insert is True:
                    # Insert the data of the csv file.
                    self.insert_data()

            # The inserts are not done yet.
            elif self.number_of_inserts != self.executed_inserts:
                # Increment the insert counter for executed inserts.
                self.executed_inserts += 1

            # The inserts are done.
            elif self.number_of_inserts == self.executed_inserts:
                # Show the success to the user.
                QMessageBox.information(self, title, "The data has been inserted successfully.")
                # Reset the number of excepted inserts and the number of executed inserts back to 0.
                self.number_of_inserts = 0
                self.executed_inserts = 0

    def process_sql_error(self, result):
        """
        Process the SQL error after the try to execute a query.
        """

        # Get the title of the error message.
        title = result[0]
        # Get the error message.
        message = result[1]

        # This function defines the error case, so if a table should have been created and the data inserted, set the
        # attribute for proceeding with an insert to False, which is the default value for this attribute.
        if self.proceed_with_insert is True:
            self.proceed_with_insert = False

        # A data definition query should have been executed.
        if self.number_of_inserts == 0 and self.executed_inserts == 0:
            QMessageBox.critical(self, title, message)

        # The inserts are not done yet.
        elif self.number_of_inserts != self.executed_inserts:
            # Increment the counter for one processed insert.
            self.executed_inserts += 1

        # The inserts are done.
        elif self.number_of_inserts == self.executed_inserts:
            # Show the insert error
            QMessageBox.critical(self, "Insert Error", "An error occurred during the insert: {}".format(message))
            # Reset the number of excepted inserts and the number of executed inserts back to 0.
            self.number_of_inserts = 0
            self.executed_inserts = 0

    def insert_data(self):
        """
        Insert the data of the csv file into the given table.
        """

        self.proceed_with_insert = False

        # Get the table name out of the line edit.
        table_name = self.table_name_line_edit.text()
        # Calculate the expected number of inserts by the chunk size of the csv importer.
        self.number_of_inserts = (len(self.csv_importer.csv_data) - 2) // self.csv_importer.chunk_size
        # Start the insert process.
        self.csv_importer.create_and_execute_insert_queries(table_name)

    def create_table_and_insert_data(self):
        """
        Create the table and insert the data.
        """

        # Set the attribute for inserting the data to True.
        self.proceed_with_insert = True
        # Create the table. The insert will be triggered, if the create statement is successful.
        self.create_table()
