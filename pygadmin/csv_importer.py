import copy
import logging
import os
import csv
import re

from pygadmin.database_query_executor import DatabaseQueryExecutor


class CSVImporter:
    """
    Create a class for importing (small) .csv files. The process involves parsing a csv file, creating the table with
    assumed data types and inserting all the data.
    """

    def __init__(self, database_connection, csv_file, delimiter=",", null_type="", table_name=None):
        # Use the csv file for loading the relevant data.
        self.csv_file = csv_file
        # Use a delimiter for the csv file, not necessarily ",".
        self.delimiter = delimiter
        # Define the null type of the csv file.
        self.null_type = null_type
        # Get the name of the table.
        self.table_name = table_name
        # Save the csv data in a list.
        self.csv_data = []
        # Save the data types in a list.
        self.data_types = []
        # Use the database query executor for executing the create table and insert queries.
        self.database_query_executor = DatabaseQueryExecutor()
        # Use the given database connection for further execution of database queries on the given database.
        self.database_query_executor.database_connection = database_connection
        # Define a chunk size for splitting the data in separate chunks for inserting later. 5000 is an acceptable value
        # between the two extreme cases (inserting all data in one INSERT or inserting every row/list with an own
        # INSERT). A class attribute is chosen for potential (read) access.
        self.chunk_size = 5000

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
        Assume the data types of the rows in the csv file based on the given values. Check the first 10000 values, so
        the overhead is small, but the check data is large enough to get a correct assumption. The supported data types
        for assuming are NULL, INT, DECIMAL and TEXT.
        """

        # Check the of the csv data without the header.
        if len(self.csv_data) - 2 > 10000:
            # Set the limit to 10000 in case of a larger file.
            check_limit = 10000

        # Set the limit to the data size of the file.
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
                # Try to parse and assume the data types. This process could fail caused by a wrong delimiter for the
                # csv file, so the list of data types has a completely different length, causing an error.
                try:
                    # Get the old/previous data type for comparison.
                    old_data_type = self.data_types[check_column]
                    # If the data type is TEXT, break, because there is nothing to change. This data type works in every
                    # case.
                    if old_data_type != "TEXT":
                        # Get the current value.
                        value = current_row[check_column]
                        # Get the data type of the current value.
                        data_type = self.get_data_type(value)

                        # If the data type is not null, write the data type in the data type list. Converting REAL to
                        # INT is not allowed.
                        if data_type != "NULL" and (not (old_data_type == "REAL" and data_type == "INT")):
                            self.data_types[check_column] = data_type

                # Catch the index error of data type list, caused by a wrong delimiter in the csv file.
                except IndexError:
                    # Log the incident.
                    logging.critical("The data types can not be assumed based on an index error. This is caused by a "
                                     "wrong delimiter for the csv file.", exc_info=True)
                    # Raise the exception for further handling, for example in the user interface.
                    raise

    def get_data_type(self, value):
        """
        Get the data type of a specific value in a readable format as Postgres data type. Every value can be a text in
        the end.
        """

        # If the value is the predefined null value/type, return a NULL value. Every other data type is still possible.
        if value == self.null_type:
            return "NULL"

        # Try to cast the value to a float or an integer to check for a number.
        try:
            # Try to float the value and check for an integer.
            if float(value).is_integer():
                return "INT"

            # Only a float/REAL is a possible option now.
            return "REAL"

        # Ignore the value error, because it is not relevant in this case and allowed to go silently.
        except ValueError:
            pass

        # Return TEXT, if a match could not be made.
        return "TEXT"

    def create_table_for_csv_data(self, create_statement=None):
        """
        Create the table to store the csv data in the database. Set the default parameter for the create statement to
        None, so a statement is created out of the given csv file. If the parameter is used, a new create statement can
        be set, for example by a user.
        """

        if create_statement is None:
            # Get the create statement of the table.
            create_statement = self.get_create_statement()

        self.execute_query(create_statement)

    def get_create_statement(self, check_ddl=True):
        """
        Build the CREATE statement for the table for inserting the csv data. The option "check_ddl" secures the column
        name against possible dangerous names. The default is True, because such checks after "blind" imports are a
        security feature.
        """

        # Get the table name, so the table name can be used in the create statement.
        self.get_table_name()
        # Add the table name to the query.
        create_table_query = "CREATE TABLE {} (\n".format(self.table_name)

        # Get the header as start of the csv data, because the columns are defined here.
        header = self.csv_data[0]

        # Iterate over the header. The column count is necessary to set the comma value at the correct point, because
        # the column to create does not need a comma at the end.
        for column_count in range(len(header)):
            # Define the comma to set after the definition of the column.
            if column_count != len(header)-1:
                comma_value = ","

            else:
                comma_value = ""

            # Get the current column.
            current_column = header[column_count]

            # If the name of the column should be checked, check it.
            if check_ddl:
                current_column = self.check_ddl_parameter(current_column)
                # Write the corrected name back in the csv data.
                self.csv_data[0][column_count] = current_column

            # Define the current column with its name, its data type and its comma value.
            create_column = "{} {}{}\n".format(current_column, self.data_types[column_count], comma_value)
            # Build the table query by adding the new column.
            create_table_query = "{}{}".format(create_table_query, create_column)

        # End the query, so the query is in an executable format.
        create_table_query = "{});".format(create_table_query)

        return create_table_query

    def get_table_name(self):
        """
        Get the name of the table based on the name of the csv file, if the name is not specified by the user.
        """

        if self.table_name is None:
            # Split the csv file in the different parts of the path.
            slash_split_list = self.csv_file.split("/")
            # Get the last part of the list as file name, because the last part of the path is the file identifier.
            self.table_name = slash_split_list[len(slash_split_list) - 1]
            # Get the .csv out of the name by splitting.
            csv_split_list = self.table_name.split(".csv")
            # Use the part without csv as table name.
            self.table_name = csv_split_list[0]
            # Check the name of the table.
            self.table_name = self.check_ddl_parameter(self.table_name)

    def create_and_execute_insert_queries(self, table_name=None):
        """
        Create the necessary queries for inserting the data in the table based on splitting the data in sub lists for
        improving the performance of the insert. The attribute of the class for the csv data should not be harmed, so
        a copy is used for the working process. The default for the table name is None, so the attribute of the class
        for the table name is used. Execute the queries after their creation.
        """

        # Use the table name defined by the class/csv file as table name.
        if table_name is None:
            table_name = self.table_name

        # Copy the data list, so the work data list can be used and modified.
        work_data_list = copy.copy(self.csv_data)
        # Delete the header, because the header does not have to be inserted.
        del work_data_list[0]

        # Split the work data list in lists with the given chunk size.
        work_data_list = [work_data_list[i * self.chunk_size:(i+1) * self.chunk_size]
                          for i in range((len(work_data_list) + self.chunk_size - 1) // self.chunk_size)]

        # Iterate over every sub list in the work data list. Those sub lists contain their separate chunk of data for
        # inserting.
        for sub_data_list in work_data_list:
            # Get the begin of an insert query with the given table name.
            insert_query = self.create_insert_query_begin(table_name)
            # Define a list for the parameters, because the data is used as parameter in the query.
            parameter_list = []

            # Get one single row, so this row (count) describes exactly one row of data.
            for row_count in range(len(sub_data_list)):
                # Begin the query with ( for the correct SQL syntax.
                value_query = "("
                # Get the row with the row count.
                row = sub_data_list[row_count]
                # Iterate over the value count, so it is now possible to get every single value.
                for value_count in range(len(row)):
                    # Check the comma value: an INSERT needs commas for separating the values, but only, if a new value
                    # follows, which is the case for every value except the last one.
                    if value_count != len(row)-1:
                        comma_value = ", "

                    else:
                        comma_value = ""

                    # Put the value query together. "%s" is used as placeholder for the parameter.
                    value_query = "{}%s{}".format(value_query, comma_value)
                    # Get the actual value.
                    value = row[value_count]

                    # If the value is equal to the predefined null value/type, the value is set to None. This is
                    # interpreted as NULL by psycopg2.
                    if value == self.null_type:
                        value = None

                    # Append the value to the list of parameters.
                    parameter_list.append(value)

                # If the current row is not the last one in the sub data list, append a comma for separating the
                # different value lists per insert.
                if row_count != len(sub_data_list)-1:
                    comma_value = ", "

                # If the value is the last one, use a semicolon for the end of the query.
                else:
                    comma_value = ";"

                # Put the value query together.
                value_query = "{}){}".format(value_query, comma_value)

                # Combine the insert query with the value query.
                insert_query = "{}{}".format(insert_query, value_query)

            # Execute the insert query.
            self.execute_query(insert_query, parameter_list)

    def create_insert_query_begin(self, table_name=None):
        """
        Create the begin of an insert query. The default table name is None, so the name of the csv file is used.
        """

        # Get the default name, the name of the csv file.
        if table_name is None:
            table_name = self.table_name

        # Begin with the INSERT INTO and the checked table name, so an formatted input is okay.
        insert_query = "INSERT INTO {} (".format(table_name)

        # Get the header for the column names.
        header = self.csv_data[0]

        for column_count in range(len(header)):
            # Define the comma to set after the definition of the column.
            if column_count != len(header)-1:
                comma_value = ", "

            else:
                comma_value = ""

            # Insert the column name.
            insert_column = "{}{}".format(header[column_count], comma_value)
            insert_query = "{}{}".format(insert_query, insert_column)

        # Put the query together and append the VALUES, so the next step is adding the data for inserting.
        insert_query = "{}) VALUES ".format(insert_query)

        # Return the begin of the query.
        return insert_query

    def drop_table(self, table_name=None):
        """
        Drop the given table, defined by the table name. If the table name stays None as default parameter, use the
        deduced name.
        """

        # Get the statement.
        drop_statement = self.get_drop_statement(table_name)
        # Execute the query.
        self.execute_query(drop_statement)

    def get_drop_statement(self, table_name=None):
        """
        Create the drop statement for the existing table.
        """

        # If the given table name is None, use the attribute of the class, defined by the name of the csv file.
        if table_name is None:
            self.get_table_name()
            table_name = self.table_name

        # Create the statement.
        drop_statement = "DROP TABLE {};".format(table_name)

        # Return the statement.
        return drop_statement

    def execute_query(self, query, parameters=None):
        """
        Execute the given query with the parameters. If the parameters are not given, the default None is used, so only
        the query is executed.
        """

        # Assign the query as database query for the executor.
        self.database_query_executor.database_query = query
        # Use the parameters.
        self.database_query_executor.database_query_parameter = parameters
        # Execute!
        self.database_query_executor.submit_and_execute_query()

    @staticmethod
    def check_ddl_parameter(parameter):
        """
        Check the given data definition language parameter for potentially malicious characters. Those malicious
        characters could cause an SQL injection, so nearly all special characters are kicked out.
        """

        # Define a matching regular expression for allowed characters. Kick every other character. Allowed special
        # characters are _, whitespace, . and some special (german) characters, because they can not do any harm.
        parameter = re.sub(r"[^a-zA-ZäöüÄÖÜß0-9 _\.]", "", parameter)

        # If a whitespace is part of the parameter, use " " around the parameter to make a valid column ddl parameter.
        if " " in parameter:
            parameter = '"{}"'.format(parameter)

        return parameter
