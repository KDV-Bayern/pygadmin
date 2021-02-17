import sys
import time

from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QApplication, QPushButton, QMessageBox

from pygadmin.connectionfactory import global_connection_factory
from pygadmin.csv_importer import CSVImporter
from pygadmin.widgets.widget_icon_adder import IconAdder


class CSVImportDialog(QDialog):
    # TODO: docu
    def __init__(self, database_connection, csv_file, delimiter):
        super().__init__()
        # Add the pygadmin icon as window icon.
        icon_adder = IconAdder()
        icon_adder.add_icon_to_widget(self)

        self.csv_importer = CSVImporter(database_connection, csv_file, delimiter, table_name="new_test_table",
                                        null_type="")

        if self.csv_importer.check_existence_csv_file():
            self.init_ui()
            self.init_grid()
            self.csv_importer.database_query_executor.result_data.connect(self.show_success)
            self.csv_importer.database_query_executor.error.connect(self.show_error)

        else:
            self.init_error_ui(csv_file)

    def init_ui(self):
        self.csv_importer.parse_csv_file()
        self.csv_importer.assume_data_types()
        self.create_statement_label = QLabel(self.csv_importer.get_create_statement())
        self.insert_button = QPushButton("Insert")
        self.create_button = QPushButton("Create")
        self.insert_button.clicked.connect(self.insert_data)
        self.create_button.clicked.connect(self.create_table)
        self.show()

    def init_grid(self):
        grid_layout = QGridLayout(self)
        grid_layout.addWidget(self.create_statement_label, 0, 0)
        grid_layout.addWidget(self.insert_button, 0, 1)
        grid_layout.addWidget(self.create_button, 0, 2)
        grid_layout.setSpacing(10)
        self.setLayout(grid_layout)

    def init_error_ui(self, csv_file):
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

    def insert_data(self):
        begin = time.time()
        self.csv_importer.create_and_execute_insert_queries()
        end = time.time()
        print("Runtime: {}".format(end-begin))

    def create_table(self):
        self.csv_importer.create_table_for_csv_data()

    def show_success(self, result):
        QMessageBox.information(self, "Success", "The result is {}".format(result))

    def show_error(self, error_message):
        QMessageBox.critical(self, "Error", "{}".format(error_message))
        print(error_message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    csv_import = CSVImportDialog(global_connection_factory.get_database_connection("localhost", "testuser", "testdb"),
                                 "/home/sqlea/fl.csv", ",")
    sys.exit(app.exec())

