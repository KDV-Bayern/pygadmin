import sys
import time

from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QApplication, QPushButton, QMessageBox, QLineEdit

from pygadmin.connectionfactory import global_connection_factory
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

        # TODO: Workaround for delimiter
        self.csv_importer = CSVImporter(database_connection, csv_file)

        # If the csv file exists, initialize the relevant parts of the dialog.
        if self.csv_importer.check_existence_csv_file():
            self.init_ui()
            self.init_grid()
            self.csv_importer.database_query_executor.result_data.connect(self.show_success)
            self.csv_importer.database_query_executor.error.connect(self.show_error)

        # Show an error for a non existing file.
        else:
            self.init_error_ui(csv_file)

    def init_ui(self):
        """
        Initialize the user interface.
        """

        # Parse the given csv file.
        self.csv_importer.parse_csv_file()
        # Get the data types of the given csv file.
        self.csv_importer.assume_data_types()
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
        del column_definition_list[len(column_definition_list)-1]

        # Split the column definition at commas.
        column_definition_list = [column_definition.replace(",", "") for column_definition in column_definition_list]

        # Create a list for the column line edits, so there is a class-wide access to this list.
        self.column_line_edit_list = []

        # Process every column in the list.
        for column in column_definition_list:
            # Split the column at whitespaces, so the
            identifier_list = column.split(" ")
            # Get the index of the last element based on the length of the identifier list.
            last_element_index = len(identifier_list)-1
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

        # Under construction TODO
        self.insert_button = QPushButton("Insert")
        self.create_button = QPushButton("Create")
        self.insert_button.clicked.connect(self.insert_data)
        self.create_button.clicked.connect(self.create_table)
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

        # Place the close label at the end of CREATE
        grid_layout.addWidget(self.close_label, line_edit_count, 0)

        # Set the spacing of the grid.
        grid_layout.setSpacing(10)
        # Set the layout to the grid layout.
        self.setLayout(grid_layout)

    def init_error_ui(self, csv_file):
        """
        Initialize the user interface for the error case and show the name of the invalid csv file.
        """

        # Get the layout as grid layout.
        grid_layout = QGridLayout(self)
        # Add a label with an error.
        grid_layout.addWidget(QLabel("The given csv file {} is invalid".format(csv_file)), 0, 0)
        self.setLayout(grid_layout)
        self.setMaximumSize(10, 100)
        self.showMaximized()
        # Set the title to an error title.
        self.setWindowTitle("File Error")
        self.show()

    def create_table(self):
        """
        TODO: Build create statement and use the csv importer for execution
        """

        self.csv_importer.create_table_for_csv_data()

    # under construction: TODO
    def insert_data(self):
        begin = time.time()
        self.csv_importer.create_and_execute_insert_queries()
        end = time.time()
        print("Runtime: {}".format(end-begin))

    def show_success(self, result):
        QMessageBox.information(self, "Success", "The result is {}".format(result))

    def show_error(self, error_message):
        QMessageBox.critical(self, "Error", "{}".format(error_message))
        print(error_message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    csv_import = CSVImportDialog(global_connection_factory.get_database_connection("localhost", "testuser", "testdb"),
                                 "/home/sqlea/test.csv")
    sys.exit(app.exec())

