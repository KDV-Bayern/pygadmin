import os
import csv
import re

from psycopg2 import sql

from pygadmin.database_query_executor import DatabaseQueryExecutor
from pygadmin.connectionfactory import global_connection_factory


class CSVImporter:
    """
    Create a class for importing (small) .csv files. The process involves parsing a csv file, creating the table with
    assumed data types and inserting all the data.
    """

    def __init__(self, database_connection, csv_file, delimiter=",", null_type="NULL", create_table=True,
                 table_name=None):

        # Use the given database connection for further execution of database queries on the given database.
        self.database_connection = database_connection
        # Use the csv file for loading the relevant data.
        self.csv_file = csv_file
        # Use a delimiter for the csv file, not necessarily ",".
        self.delimiter = delimiter
        # Define the null type of the csv file.
        self.null_type = null_type
        # Use a new table for saving the data and not only appending to an existing one.
        self.create_table = create_table
        # Get the name of the table.
        self.table_name = table_name
        # Save the csv data in a list.
        self.csv_data = []
        # Save the data types in a list.
        self.data_types = []
        # TODO: Create functions for connecting the result signal and the error signal
        # Use the database query executor for executing the create table and insert queries.
        self.database_query_executor = DatabaseQueryExecutor()
        self.database_query_executor.error.connect(self.print_error)
        self.database_query_executor.result_data.connect(self.print_result)

    def check_existence_csv_file(self):
        """
        Check for the existence of the given csv file, because only if the file exists, data can be read from the file.
        """

        if os.path.exists(self.csv_file):
            return True

        else:
            return False

    def parse_csv_file(self):
        """
        Parse the content of the csv file.
        """

        # Use a try in case of invalid permissions or a broken file.
        try:
            # Open the file.
            with open(self.csv_file) as csv_file:
                # Read the content of the file with the given delimiter.
                reader = csv.reader(csv_file, delimiter=self.delimiter)

                # Add every row to a data list.
                for row in reader:
                    self.csv_data.append(row)

            # Return the success.
            return True

        except Exception as file_error:
            # Return the error.
            return file_error

    def assume_data_types(self):
        """
        Assume the data types of the rows in the csv file based on the given values. Check the first 100 values, so the
        overhead is small, but the check data is large enough to get a correct assumption. The supported data types for
        assuming are NULL, INT, DECIMAL and TEXT.
        """

        # If the data is larger than 100 rows, define the check limit for the first 100 rows.
        if len(self.csv_data)-2 > 100:
            check_limit = 100

        # Define the limit based on the file length.
        else:
            check_limit = len(self.csv_data) - 2

        # Create a list for the data types.
        self.data_types = [None] * len(self.csv_data[0])

        # Check every row within the check limit.
        for check_row in range(1, check_limit):
            # Get the row.
            current_row = self.csv_data[check_row]

            # Check the data type of the current column.
            for check_column in range(len(current_row)):
                # If the data type is TEXT, break, because there is nothing to change. This data type works in every
                # case.
                if self.data_types[check_column] == "TEXT":
                    break

                # Get the current value.
                value = current_row[check_column]
                # Get the data type of the current value.
                data_type = self.get_data_type(value)

                # If the data type is not null, write the data type in the data type list.
                if data_type != "NULL":
                    self.data_types[check_column] = data_type

    def get_data_type(self, value):
        if value == self.null_type:
            return "NULL"

        try:
            if float(value).is_integer():
                return "INT"

            float(value)
            return "REAL"

        except ValueError:
            pass

        return "TEXT"

    def create_table_for_csv_data(self):
        if self.create_table is not True:
            return

        create_statement = self.get_create_statement()

        with self.database_connection.cursor() as database_cursor:
            database_cursor.execute(sql.SQL(create_statement))

            if database_cursor.description:
                print(database_cursor.description)

    def get_create_statement(self):
        self.get_table_name()
        create_table_query = "CREATE TABLE {} (".format(self.table_name)

        header = self.csv_data[0]

        for column_count in range(len(header)):
            if column_count != len(header)-1:
                comma_value = ","

            else:
                comma_value = ""

            create_column = "{} {}{}\n".format(header[column_count], self.data_types[column_count], comma_value)
            create_table_query = "{}{}".format(create_table_query, create_column)

        create_table_query = "{});".format(create_table_query)

        print(create_table_query)

        # TODO: Mechanism for the user to check the create table statement

        return create_table_query

    def get_table_name(self):
        if self.table_name is None:
            slash_split_list = self.csv_file.split("/")
            self.table_name = slash_split_list[len(slash_split_list) - 1]
            csv_split_list = self.table_name.split(".csv")
            self.table_name = csv_split_list[0]
            self.table_name = self.check_ddl_parameter(self.table_name)

    @staticmethod
    def check_ddl_parameter(parameter):
        parameter = re.sub(r"[^a-zA-Z0-9 _\.]", "", parameter)

        if " " in parameter:
            parameter = '"{}"'.format(parameter)

        return parameter

    def print_error(self, error):
        print(error)

    def print_result(self, result):
        print(result)


    def do_all_the_stuff(self):
        """
        Normal persons would call this function "main". This function is only a placeholder to remember me, that I'm
        going to need a function for doing all the relevant csv stuff, so the user/rest of the program needs only a
        database connection and a name, function call, boom, everything is working (or not, that's a case for an error).
        So, strong TODO
        """

        pass


# TODO: Check for file existence, parse file with error handling, assume the data type on a very basic level, check for
#  create table or insert in existing table, (create table and) insert

if __name__ == "__main__":
    csv_importer = CSVImporter(global_connection_factory.get_database_connection("localhost", "testuser", "testdb"),
                               "/home/sqlea/test.csv", delimiter=";", table_name="new_test_table")
    if csv_importer.check_existence_csv_file() is True:
        csv_importer.parse_csv_file()
        csv_importer.assume_data_types()
        csv_importer.get_create_statement()
