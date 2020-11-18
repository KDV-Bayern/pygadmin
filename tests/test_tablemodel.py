import unittest

from PyQt5.QtCore import Qt

from pygadmin.models.tablemodel import TableModel


class TestTableModelMethods(unittest.TestCase):
    """
    Use a class for testing the different methods of the table model.
    """

    def test_initial_data_list(self):
        """
        Test the creation of a table model and check the resulting data list.
        """

        # Define a data list.
        test_data = [["column 0", "column 1", "column 2"], ["row A", "row B", "row C"], ["row D", "row E", "row F"]]
        table_model = TableModel(test_data)
        # Check the data list of the model.
        assert test_data == table_model.data_list

    def test_correct_row_count(self):
        """
        Test the correct row count for a normal and valid data list.
        """

        test_data = [["column 0", "column 1", "column 2"], ["row A", "row B", "row C"], ["row D", "row E", "row F"]]
        table_model = TableModel(test_data)
        # Describe the row count as the length of the test data list - 1, because the header is not a row.
        assert table_model.rowCount() == len(test_data) - 1

    def test_correct_column_count(self):
        """
        Test the correct column count for a normal and valid data list.
        """

        test_data = [["column 0", "column 1", "column 2"], ["row A", "row B", "row C"], ["row D", "row E", "row F"]]
        table_model = TableModel(test_data)
        # The first list contains all header elements and describes the number of columns.
        assert table_model.columnCount() == len(test_data[0])

    def test_data_type(self):
        """
        Test with different types the correct result of the data in the table model. Almost every value should cause the
        return of a string.
        """

        # Define different kinds of test data: Numbers in the header, booleans (and None) as first row, numbers as
        # second and strings as third.
        test_data = [[0, 1, 2], [True, False, None], [4, 5, 6], ["test", "1234", "meow"]]
        table_model = TableModel(test_data)

        # Get the first item in the first row, check for a string and for the correct value.
        first_row_item = table_model.data(table_model.index(0, 0))
        assert isinstance(first_row_item, str)
        assert first_row_item == "True"

        # Get the first item in the second row, check for a string and for the correct value.
        second_row_item = table_model.data(table_model.index(1, 0))
        assert isinstance(second_row_item, str)
        assert second_row_item == "4"

        # Get the first item in the third row, check for a string and for the correct value.
        third_row_item = table_model.data(table_model.index(2, 0))
        assert isinstance(third_row_item, str)
        assert third_row_item == "test"

        # Get the first item in the fourth row, but this row does not exist, so it should return None. None is not
        # casted to a string, so there is just a check for None.
        fourth_row_item = table_model.data(table_model.index(3, 0))
        assert fourth_row_item is None

    def test_horizontal_header_data(self):
        """
        Test the correct display of data with a horizontal header.
        """

        # Define a first list as extra list, because this list contains the header.
        first_list = ["column 0", "column 1", "column 2"]
        test_data = [first_list, ["row A", "row B", "row C"], ["row D", "row E", "row F"]]
        table_model = TableModel(test_data)

        # Check every number in the header.
        for header_description_number in range(len(first_list) - 1):
            # Get the data in the header by a horizontal orientation.
            header_data = table_model.headerData(header_description_number, Qt.Horizontal)
            # Check, if the item in the header is the same as the item in the first list, which is the header list.
            assert header_data == first_list[header_description_number]

    def test_vertical_header_data(self):
        """
        Test the correct display of data with a vertical header.
        """

        test_data = [["column 0", "column 1", "column 2"], ["row A", "row B", "row C"], ["row D", "row E", "row F"]]
        table_model = TableModel(test_data)

        # Check for every element in the test data list.
        for row_number in range(len(test_data) - 1):
            # Get the data at the row number with a vertical orientation.
            header_data = table_model.headerData(row_number, Qt.Vertical)
            # The data for a vertical header is numeric, so from 1 to whatever and because of this, off by one needs to
            # be considered.
            assert header_data == row_number + 1

    def test_correct_row_count_with_empty_list(self):
        """
        Test the correct row count with an empty data list.
        """

        test_data = []
        table_model = TableModel(test_data)
        # For an empty list, the row count should be 0.
        assert table_model.rowCount() == 0

    def test_correct_column_count_with_empty_list(self):
        """
        Test the correct column count with an empty data list.
        """

        test_data = []
        table_model = TableModel(test_data)
        # For an empty data list, the column count should be 0.
        assert table_model.columnCount() == 0

    def test_false_type_input(self):
        """
        Test the behavior of the table model for a data list, which is not a list.
        """

        # Define the test data as None.
        test_data = None
        table_model = TableModel(test_data)
        # For a data list, which is not a list, the new and internal data list of the table model should be an empty
        # list.
        assert table_model.data_list == []
