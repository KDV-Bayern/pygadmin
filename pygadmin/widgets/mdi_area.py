import logging
import re

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QMdiArea
from PyQt5.QtCore import pyqtSlot, pyqtSignal

from pygadmin.widgets.editor import EditorWidget
from pygadmin.connectionfactory import global_connection_factory


class MdiArea(QMdiArea):
    """
    Create a class for a customized MdiArea as program intern window management widget for all basic widgets (mainly
    the editor widget) except the tree widget.
    """

    # Use a signal for the changed of the current sub window.
    current_sub_window_change = pyqtSignal(object)

    def __init__(self):
        """
        Make sub function for initializing the widget and connecting a signal.
        """

        super().__init__()
        self.init_ui()
        # Connect the signal for an activated sub window with a customized function.
        self.subWindowActivated.connect(self.on_sub_window_change)

    def init_ui(self):
        """
        Design the user interface and its components.
        """

        # Set the tabs movable, so they can be moved in the MdiArea.
        self.setTabsMovable(True)
        # Set the tabs closeable, so they can be removed.
        self.setTabsClosable(True)
        # Set the view mode to tabs, so tabs are used instead of windows, which is more usable.
        self.setViewMode(self.TabbedView)

        # Create an empty icon.
        icon = QIcon(QPixmap(0, 0))
        # Use the empty icon as window icon, so the pygadmin logo is not in the window title bar of every editor widget.
        self.setWindowIcon(icon)

    def generate_editor_tab(self):
        """
        Generate a new editor widget as sub window of the MdiArea and connect a signal for a change table/view for an
        existing parent of the MdiArea, for example a QMainWindow. Use a parameter, so a previous statement, saved in
        a file, can be loaded with a function of the editor widget.
        """

        # Create the editor widget.
        editor_widget_to_generate = EditorWidget()

        # Add the widget to the MdiArea as a sub window.
        self.addSubWindow(editor_widget_to_generate)

        # Try to use the parent of the MdiArea with a specified signal.
        try:
            # Connect the signal for the structural change to the slot of the parent of the MdiArea, which should
            # receive the signal for further usage like informing other components.
            editor_widget_to_generate.structural_change_in_view_table.connect(self.parent().change_tree_structure)
            # Connect the function for changing the status message of the main window with the function for changing a
            # new status bar message.
            editor_widget_to_generate.change_in_status_message.connect(self.parent().show_status_bar_message)

        # If something went wrong, save a message in the log.
        except Exception as parent_error:
            logging.warning("The new generated editor widget, which was placed on the MdiArea, cannot find a parent "
                            "with the correct signal, resulting in the following error: {}".format(parent_error),
                            exc_info=True)

        editor_widget_to_generate.showMaximized()

        return editor_widget_to_generate

    @pyqtSlot(dict)
    def change_current_sub_window_and_connection_parameters(self, database_connection_parameters):
        """
        Get the current activated sub window and change the database connection parameters of the editor widget, which
        is currently activated. As a result, its database connection is changed too.
        """

        # Get the current widget for which the slot is used.
        current_editor_widget = self.determine_current_editor_widget()

        # Check, if the result is not None.
        if current_editor_widget is not None:
            # Change the connection based on its parameters of the editor widget.
            current_editor_widget.set_connection_based_on_parameters(database_connection_parameters)

    def determine_current_editor_widget(self):
        """
        Determine the current, active or only given editor widget, which is shown in a sub window. The possible
        scenarios contain a single widget without recognition by currentSubWindow() as function of the MdiArea and the
        recognition of a current sub window and its widget by the function. The check for an editor widget is required.
        If there is None, None is returned.
        """

        # If currentSubWindow returns None, there could still be a widget, so there is also a check for the list of all
        # sub windows. If this list is not empty, continue.
        if self.currentSubWindow() is None and self.subWindowList:
            # Check all sub windows in the list for their widget. If their widget is an editor widget, it is stored in a
            # list.
            editor_widget_list = [sub_window.widget() for sub_window in self.subWindowList()
                                  if isinstance(sub_window.widget(), EditorWidget)]

            # Check for content in the list and proceed if the list is not empty.
            if editor_widget_list:
                # Get the first item of the list as editor widget.
                first_editor_widget = editor_widget_list[0]

                return first_editor_widget

        # Check if the current sub window is not None. If it is None, all sub windows are closed (or non existent) and a
        # change of connection parameters does not need to be transmitted except in the case checked above.
        elif self.currentSubWindow() is not None:
            # Get the widget of the sub window, which is currently active.
            current_widget = self.currentSubWindow().widget()

            # If the current widget is an EditorWidget, the parameters are committed, because they are only relevant
            # to an editor field and not to every widget.
            if isinstance(current_widget, EditorWidget):
                return current_widget

        # If there is not a widget, just return None.
        else:
            return None

    def determine_empty_editor_widget_with_connection(self, database_connection_parameter):
        """
        Find the editor widget with the current connection and without a current query/text. If such an editor does not
        exist, create one and return it.
        """

        # Get the current editor widget.
        current_editor_widget = self.determine_current_editor_widget()

        # If there is a current widget, proceed.
        if current_editor_widget is not None:
            # Get the current database connection parameters of the current editor widget.
            database_connection_parameter_of_current_widget = \
                global_connection_factory.get_database_connection_parameters(
                    current_editor_widget.current_database_connection)

            # Check, if the parameters of current editor widget are the given parameters and if the current editor does
            # not contain any text.
            if database_connection_parameter_of_current_widget == database_connection_parameter and \
                    current_editor_widget.query_input_editor.text() == "":
                # Return the current editor widget for a success.
                return current_editor_widget

        # Proceed, if the current editor widget is not a match or is None.
        if self.subWindowList():
            # Get all editor widgets.
            editor_widget_list = [sub_window.widget() for sub_window in self.subWindowList()
                                  if isinstance(sub_window.widget(), EditorWidget)]

            # Check every editor widget.
            for editor_widget in editor_widget_list:
                # Get the database connection parameter of the widget.
                database_connection_parameter_of_widget = global_connection_factory.get_database_connection_parameters(
                    editor_widget.current_database_connection)

                # Check the database connection parameters for equality and the editor for an empty text field.
                if database_connection_parameter_of_widget == database_connection_parameter and \
                        editor_widget.query_input_editor.text() == "":
                    # Return the widget for a success.
                    return editor_widget

        # If the steps before fail, generate a new editor widget.
        new_editor_widget = self.generate_editor_tab()
        # Set the connection in the new widget based on the given database connection parameters.
        new_editor_widget.set_connection_based_on_parameters(database_connection_parameter)

        return new_editor_widget

    def on_sub_window_change(self):
        """
        Describe the behavior of the MdiArea, if the active sub window is changed. It is a more specific wrapper for the
        already existing signal of QMdiArea called subWindowActivated. The idea is to inform the tree, containing all
        database connections, of a change of the database connection, so the original tree layout for this EditorWidget
        can be restored.
        """

        # Check for a current active sub window, because only existing sub windows can contain a widget, which is one
        # relevant point of this function.
        if self.currentSubWindow() is not None:
            # Get the widget of the sub window.
            current_active_sub_window = self.currentSubWindow().widget()

            # Check for an EditorWidget, because only EditorWidgets need to know about a requested change of connection
            # parameters.
            if isinstance(current_active_sub_window, EditorWidget):
                # Get the current database connection, which is a class-wide object in the widget.
                current_editor_connection = current_active_sub_window.current_database_connection

                # If the connection exists and is not closed, proceed.
                if current_editor_connection and current_editor_connection.closed == 0:
                    # Get the parameters of the database connection, because the receiving object must be handled with
                    # database connection parameters.
                    database_parameter_dictionary = global_connection_factory.get_database_connection_parameters(
                        current_editor_connection)

                    # Emit the change with the dictionary via slots and signals.
                    self.current_sub_window_change.emit(database_parameter_dictionary)

                # This else branch is used for two corner cases: The database connection failed or the database
                # connection is closed. So the connection identifier of the current sub window is used for the transfer
                # of connection parameters.
                elif (current_editor_connection and current_editor_connection.closed == 1) or \
                        current_editor_connection is False:
                    # Check for a given identifier. The identifier is initialized as None, so there must have been a
                    # change.
                    if current_active_sub_window.connection_identifier is not None:
                        # Split the connection identifier.
                        parameter_list = [parameter.strip() for parameter in re.split(
                            "[@:/]", current_active_sub_window.connection_identifier)]

                        # Make a dictionary out of the list, which split the identifier.
                        database_parameter_dictionary = {
                            "user": parameter_list[0],
                            "host": parameter_list[1],
                            # Cast the port to an integer for preventing weird behavior.
                            "port": int(parameter_list[2]),
                            "database": parameter_list[3]
                        }

                        # Emit the change with the dictionary of a failed connection.
                        self.current_sub_window_change.emit(database_parameter_dictionary)

                # If the connection does not exists, return None, so the selection is cleared.
                else:
                    self.current_sub_window_change.emit(None)

        # The else branch is relevant for a closed sub window.
        else:
            self.current_sub_window_change.emit(None)

    def determine_next_empty_editor_widget(self):
        """
        Determine the next empty editor widget based on the current given widget and the existing editor widgets. First,
        check the current widget for an editor widget. If the widget of the current sub window is an editor widget,
        check this widget for emptiness. An empty widget will be returned. If the current widget is not an editor widget
        or not empty, check the list of all sub windows for their widget. If this widget is an editor widget and empty,
        return it. If an empty widget can not be found, return None.
        """

        # Check for a current existing sub window.
        if self.currentSubWindow() is not None:
            # Check the widget of the current sub window for an editor widget.
            if isinstance(self.currentSubWindow().widget(), EditorWidget):
                # Get the widget of the current sub window.
                next_editor_widget_candidate = self.currentSubWindow().widget()

                # Check for an empty editor with an instance check and the function of the editor for its own emptiness.
                if isinstance(next_editor_widget_candidate, EditorWidget) \
                        and next_editor_widget_candidate.is_editor_empty() is True:
                    # Return an empty editor.
                    return next_editor_widget_candidate

        # Get a list of all editor widgets with a list comprehension: Check all sub windows in the list of all sub
        # windows for their widget and the instance of their widget.
        editor_widget_list = [sub_window.widget() for sub_window in self.subWindowList()
                              if isinstance(sub_window.widget(), EditorWidget)]

        # Check every editor in the editor widget list.
        for editor_widget in editor_widget_list:
            # Check the editor for emptiness.
            if editor_widget.is_editor_empty() is True:
                # If the editor is empty, return it. This statement causes the function to end: The first match is
                # returned.
                return editor_widget

        # None will be returned, if the search for a currently existing empty editor widget is unsuccessful.
        return None
