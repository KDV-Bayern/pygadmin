import sys
import unittest

from PyQt5.QtWidgets import QApplication

from pygadmin.widgets.mdi_area import MdiArea
from pygadmin.widgets.editor import EditorWidget

from pygadmin.connectionfactory import global_connection_factory


class TestMdiAreaMethods(unittest.TestCase):
    """
    Test the functionality and methods of Mdi area.
    """

    def test_initial_attributes(self):
        """
        Test the existence and correct instance of some initial attributes.
        """

        # Create an app, because this is necessary for testing a QMdiArea.
        app = QApplication(sys.argv)
        # Create an MdiArea.
        mdi_area = MdiArea()

        # The tabs in the MdiArea should be movable.
        assert mdi_area.tabsMovable() is True
        # The tabs in the MdiArea should be closable.
        assert mdi_area.tabsClosable() is True
        # The view mode should be 1, which is the tab view.
        assert mdi_area.viewMode() == 1

    def test_generate_editor_widget(self):
        """
        Test the correct generating process of an editor in the MdiArea.
        """

        # Create an app, because this is necessary for testing a QMdiArea.
        app = QApplication(sys.argv)
        # Create an MdiArea.
        mdi_area = MdiArea()

        # Generate an editor, which is also the return value of the function.
        generated_editor = mdi_area.generate_editor_tab()
        # The generated editor should be an editor widget.
        assert isinstance(generated_editor, EditorWidget)

        # Get the widgets of the sub windows of the MdiArea as list.
        widget_list = [sub_window.widget() for sub_window in mdi_area.subWindowList()]
        # The generated editor should be in the widget list.
        assert generated_editor in widget_list

    def test_change_current_sub_window_and_connection_parameters(self):
        """
        Test the method for setting new database connection parameters in case of an editor change in the MdiArea.
        """

        # Create an app, because this is necessary for testing a QMdiArea.
        app = QApplication(sys.argv)
        # Create an MdiArea.
        mdi_area = MdiArea()

        # Generate an editor, so there is a current sub window.
        generated_editor = mdi_area.generate_editor_tab()
        # Define a dictionary with connection parameters.
        connection_parameters = {"host": "localhost",
                                 "user": "testuser",
                                 "database": "testdb",
                                 "port": 5432}

        # Set the connection parameters.
        mdi_area.change_current_sub_window_and_connection_parameters(connection_parameters)
        # Get the current connection of the editor.
        editor_connection = generated_editor.current_database_connection
        # Get the connection dictionary related to the connection of the editor.
        editor_connection_parameters = global_connection_factory.get_database_connection_parameters(editor_connection)
        # The connection parameters of the editor should be identical to the initial connection parameters.
        assert editor_connection_parameters == connection_parameters

    def test_determine_current_editor_widget(self):
        """
        Test the method for determining the current editor widget.
        """

        # Create an app, because this is necessary for testing a QMdiArea.
        app = QApplication(sys.argv)
        # Create an MdiArea.
        mdi_area = MdiArea()

        # Right after the initialization and without any editor widget, the function for determining the current editor
        # widget should return None.
        assert mdi_area.determine_current_editor_widget() is None

        # Generate a new editor tab.
        generated_editor = mdi_area.generate_editor_tab()
        # The current editor widget should be the freshly generated editor.
        assert mdi_area.determine_current_editor_widget() == generated_editor

    def test_determine_empty_editor_widget_with_connection(self):
        """
        Test the method for getting an empty editor widget with a given database connection.
        """

        # Create an app, because this is necessary for testing a QMdiArea.
        app = QApplication(sys.argv)
        # Create an MdiArea.
        mdi_area = MdiArea()

        # Generate a new editor tab.
        editor_widget = mdi_area.generate_editor_tab()

        # Define a dictionary with connection parameters for the freshly generated editor widget.
        first_connection_parameters = {"host": "localhost",
                                       "user": "testuser",
                                       "database": "testdb",
                                       "port": 5432}

        # Get a connection based on the dictionary with connection parameters.
        connection = global_connection_factory.get_database_connection(first_connection_parameters["host"],
                                                                       first_connection_parameters["user"],
                                                                       first_connection_parameters["database"],
                                                                       first_connection_parameters["port"])

        # Set the new connection as current connection of the generated editor widget.
        editor_widget.current_database_connection = connection
        # The editor with the database connection should be the generated editor_widget.
        assert mdi_area.determine_empty_editor_widget_with_connection(first_connection_parameters) == editor_widget

        # Define a second dictionary with different connection parameters.
        second_connection_parameters = {"host": "localhost",
                                        "user": "testuser",
                                        "database": "postgres",
                                        "port": 5432}

        # A new generated widget with new connection parameters should not be the first generated editor widget.
        assert mdi_area.determine_empty_editor_widget_with_connection(second_connection_parameters) != editor_widget

    def test_determine_next_empty_editor_widget(self):
        """
        Test the method for determining the next empty editor widget.
        """

        # Create an app, because this is necessary for testing a QMdiArea.
        app = QApplication(sys.argv)
        # Create an MdiArea.
        mdi_area = MdiArea()

        # After the initialization and without any editor widgets, the function should return None,
        assert mdi_area.determine_next_empty_editor_widget() is None

        # Generate an editor widget.
        first_editor_widget = mdi_area.generate_editor_tab()
        # The generated widget should be an empty editor widget.
        assert mdi_area.determine_next_empty_editor_widget() == first_editor_widget

        # Set a text to the editor widget, so it is not empty anymore.
        first_editor_widget.query_input_editor.setText("Not Empty")
        # There is only one widget and this widget is not empty, so the function for determining an empty editor widget
        # should return None.
        assert mdi_area.determine_next_empty_editor_widget() is None

        # Generate a new editor tab.
        second_editor_widget = mdi_area.generate_editor_tab()
        # The freshly generated widget should be the next empty editor widget.
        assert mdi_area.determine_next_empty_editor_widget() == second_editor_widget

