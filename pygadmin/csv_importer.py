import os
import csv

from pygadmin.database_query_executor import DatabaseQueryExecutor


class CSVImporter:
    def __init__(self, database_connection, csv_file, delimiter=",", null_type="NULL", create_table=True,
                 table_name=None):

        self.database_connection = database_connection
        self.csv_file = csv_file
        self.delimiter = delimiter
        self.null_type = null_type
        self.create_table = create_table
        self.table_name = table_name
        self.csv_data = []
        self.data_types = []
        # TODO: Create functions for connecting the result signal and the error signal
        self.database_query_executor = DatabaseQueryExecutor()

    def check_existence_csv_file(self):
        if os.path.exists(self.csv_file):
            return True

        else:
            return False

    def parse_csv_file(self):
        try:
            with open(self.csv_file) as csv_file:
                reader = csv.reader(csv_file, delimiter=",")

                for row in reader:
                    self.csv_data.append(row)

            return True

        except Exception as file_error:
            return file_error

    def assume_data_types(self):
        if len(self.csv_data)-2 > 100:
            check_limit = 100

        else:
            check_limit = len(self.csv_data) - 2

        self.data_types = [None] * len(self.csv_data[0])

        for check_row in range(1, check_limit):
            current_row = self.csv_data[check_row]

            for check_column in range(len(current_row)):
                if self.data_types[check_column] == "TEXT":
                    break

                value = current_row[check_column]
                data_type = self.get_data_type(value)

                if data_type != "NULL":
                    self.data_types[check_column] = data_type

    def get_data_type(self, value):
        if value == self.null_type:
            return "NULL"

        try:
            float(value)
            return "REAL"

        except ValueError:
            pass

        try:
            int(value)
            return "INT"

        except ValueError:
            pass

        return "TEXT"

    def create_table_for_csv_data(self):
        if self.create_table is not True:
            return

        create_statement = self.get_create_statement()

    def get_create_statement(self):
        create_table_query = "CREATE TABLE %s ("

        header = self.csv_data[0]

        for column_count in range(len(header)):
            if column_count != len(header)-1:
                comma_value = ","

            else:
                comma_value = ""

            create_column = '"%s" %s{}\n'.format(comma_value)
            create_table_query = "{}{}".format(create_table_query, create_column)

        create_table_query = "{});".format(create_table_query)

        return create_table_query

    def get_create_parameter(self):
        parameter_list = []

        if self.table_name is None:
            slash_split_list = self.csv_file.split("/")
            self.table_name = slash_split_list[len(slash_split_list) - 1]
            csv_split_list = self.table_name.split(".csv")
            self.table_name = csv_split_list[0]

        parameter_list.append(self.table_name)

        header = self.csv_data[0]

        for column_count in range(len(header)):
            parameter_list.append(header[column_count])
            parameter_list.append(self.data_types[column_count])

        return parameter_list

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
    csv_importer = CSVImporter(None, "/home/lal45210/test.csv")
    csv_importer.check_existence_csv_file()
    csv_importer.parse_csv_file()
    csv_importer.assume_data_types()
    print(csv_importer.get_create_parameter())


