from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtGui import QColor


class TableModel(QAbstractTableModel):
    """
    Create a custom class to show data in a table with rows and columns based on given data in form of a list. A
    subclass of QAbstractTableModel needs a reimplementation of the functions rowCount(), columnCount() and data(). For
    well behaved models, headerData() is also necessary.
    """

    def __init__(self, data_list):
        super().__init__()

        # Check for the correct instance of the data_list, which should be a list.
        if isinstance(data_list, list):
            self.data_list = data_list

        # If the given input parameter is not a list, use an empty list instead.
        else:
            self.data_list = []

        # Define a list for storing tuples of row and column. These stored tuples are the changed ones.
        self.change_list = []

    def rowCount(self, parent=QModelIndex()):
        """
        Count the number of rows in the given data list as row dimension of the table.
        """

        # If the length of the data list is 0, the list is empty and does not contain any data.
        if len(self.data_list) == 0:
            return 0

        # Rows are represented by the elements of the data list.
        row_number = len(self.data_list) - 1

        return row_number

    def columnCount(self, parent=QModelIndex()):
        """
        Count the number of columns in the given data list as column dimension of the table.
        """

        # If the length of the data list is 0, the list is empty and does not contain any data.
        if len(self.data_list) == 0:
            return 0

        # The number of columns in a table is determined by the length of the elements in the data list. The first (or
        # rather 0th) element of the list is chosen because this element will always exist at this point.
        column_number = len(self.data_list[0])

        return column_number

    def data(self, index, role=Qt.DisplayRole):
        """
        Check every element of the data list and fill every cell of the table with data. If required, change also the
        appearance of specific cells.
        """

        # Ensure a correct and valid index.
        if not index.isValid():
            return None

        # Get the row number and column number out of the index.
        row = index.row()
        column = index.column()

        # Check the role: The display role should show the value in the cell.
        if role == Qt.DisplayRole:
            # Check every value for all row and column combinations.
            row_list = self.data_list[row + 1]
            value = row_list[column]

            # Return the value as a string for correct formatting.
            return str(value)

        # Check for the background role, which describes the background of the cell.
        if role == Qt.BackgroundRole:
            # If the given combination of row and column is in the change list, mark the related cell.
            if (row, column) in self.change_list:
                # Change the background of the cell to blue.
                return QColor("blue")

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
        Return data for given part of the header like row title and column title.
        """

        # An incorrect role results in a bad output format.
        if role != Qt.DisplayRole:
            return None

        # A check for the necessary element as title or header data is required.
        if orientation == Qt.Horizontal and section < self.columnCount():
            # The first (or rather 0th) element of the data list contains the header data or names of the columns. The
            # part with section gets the necessary element in this list of titles.
            return self.data_list[0][section]

        # Vertical orientation is meant for rows. Their name is determined by incrementation.
        elif orientation == Qt.Vertical:
            return section + 1

        return None

    def refresh_data_list(self, new_data_list):
        """
        Refresh the data in the table model with a new list of data.
        """

        if isinstance(new_data_list, list):
            # Save the current number of columns before a change of data to compare with new data.
            current_columns = self.columnCount()
            # Save the new data list as the data list of the object.
            self.data_list = new_data_list
            # Change the data in the table to the new data.
            self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount(), self.columnCount()))
            # Change the header data of the table to the new data.
            self.headerDataChanged.emit(Qt.Horizontal, 0,
                                        current_columns - 1 if current_columns > self.columnCount()
                                        else self.columnCount())
