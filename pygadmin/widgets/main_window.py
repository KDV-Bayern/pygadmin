import os
import logging

from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QMainWindow, QAction, QToolBar, QMessageBox, QMenu, QFileDialog
from PyQt5.QtCore import Qt, pyqtSlot

import pygadmin
from pygadmin.widgets.command_history import CommandHistoryDialog
from pygadmin.widgets.mdi_area import MdiArea
from pygadmin.widgets.dock import DockWidget
from pygadmin.widgets.connection_dialog import ConnectionDialogWidget
from pygadmin.widgets.configuration_settings import ConfigurationSettingsDialog
from pygadmin.widgets.editor_appearance_settings import EditorAppearanceSettingsDialog
from pygadmin.widgets.version_information_dialog import VersionInformationDialog
from pygadmin.widgets.start_progress_dialog import StartProgressDialog
from pygadmin.configurator import global_app_configurator
from pygadmin.widgets.widget_icon_adder import IconAdder


class MainWindow(QMainWindow):
    """
    Create a class for administration of the main interface. Every widget is showed or at least controlled by the main
    window.
    """

    def __init__(self):
        """
        Make sub functions for the initializing process.
        """

        super().__init__()
        icon_adder = IconAdder()
        icon_adder.add_icon_to_widget(self)
        self.show()
        self.init_ui()

    def init_ui(self):
        """
        Create the possibility to enter connection parameters and use them instantly before the main application is
        loaded with its functionality.
        """

        # Check the current configuration. If the configuration is set to True or if the configuration is not found and
        # currently not part of the configuration file and so, the value is None, a connection dialog is opened.
        if global_app_configurator.get_single_configuration("open_connection_dialog_at_start") is not False:
            # Create a connection dialog widget.
            self.connection_dialog = ConnectionDialogWidget()

            # Set the widget as central widget.
            self.setCentralWidget(self.connection_dialog)

            # Set the window title as title of the widget.
            self.setWindowTitle(self.connection_dialog.windowTitle())

            # Initialize the main interface after the widget for entering connection parameter is closed.
            self.connection_dialog.finished.connect(self.init_main_ui)

        else:
            self.init_main_ui()

    def init_main_ui(self):
        """
        Design the main user interface and its components.
        """

        # Activate the progress dialog for starting.
        self.start_progress_dialog = StartProgressDialog()

        # Resize to a specific size, which is big enough to see all the relevant content. Resizing is used at this point
        # so loaded content is already shown in this size.
        self.resize(1280, 720)

        # Set the title with the name of the application at the current point, so a potential existing title is
        # overwritten.
        self.setWindowTitle("Pygadmin")

        # Use a function for configuring the menu bar as part of the ui.
        self.init_menu_bar()

        # Set the current text of the status bar to ready.
        self.show_status_bar_message("Ready")

        # Create the MdiArea widget.
        self.mdi_area = MdiArea()
        # Set the MdiArea widget as central widget, because it contains the editor component as main field for
        # interaction with the program.
        self.setCentralWidget(self.mdi_area)
        # Generate one editor tab for the start of the application with the saved text.
        self.activate_new_editor_tab()

        # Create the dock widget.
        self.dock_widget = DockWidget()
        # Display dock widget at the left side of the window.
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget)

        # Connect the signal for a new added node with the slot of the start progress dialog for getting a new step size
        # and a progress in the progress bar.
        self.dock_widget.tree.new_node_added.connect(self.start_progress_dialog.get_new_step_size)

        # Connect the signal for changed database connection parameters in the tree with the corresponding signal in the
        # editor, so if the node in the tree is changed, the database connection in the editor is adjusted.
        self.dock_widget.tree.database_parameter_change.connect(
            self.mdi_area.change_current_sub_window_and_connection_parameters)

        # Connect the signal for changed database connection parameter in the editor widget(s) with the corresponding
        # slot in the tree, so if the editor tab is changed, the position in the tree is adjusted.
        self.mdi_area.current_sub_window_change.connect(self.dock_widget.tree.select_node_for_database_parameters)

        self.init_tool_bar()

        # Ensure the right deletion order for closing the application and prevent a warning with QTimer and QThread.
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Load the initial data/server nodes in the tree widget.
        self.dock_widget.tree.init_data()

    def init_menu_bar(self):
        """
        Initialize the menu bar as part of the user interface with its tasks and points.
        """

        # Get the menu bar.
        self.menu_bar = self.menuBar()

        # Make a menu point for tasks related to "edit".
        self.edit_menu = self.menu_bar.addMenu("Edit")

        # Add an action for creating a new editor.
        self.add_action_to_menu_bar("New Editor", self.activate_new_editor_tab)
        # Add an action for saving the current editor.
        self.add_action_to_menu_bar("Save Current Editor", self.save_current_editor_widget_statement)
        # Add an action for saving the current editor with a specific name. A parameter needs to be passed. This is
        # realized with the usage of a lambda function.
        self.add_action_to_menu_bar("Save Current Editor as", lambda: self.save_current_editor_widget_statement(True))
        # Add an action for loading a file to an editor widget.
        self.add_action_to_menu_bar("Load Editor", self.load_editor_widget_statement)
        # Add an action for changing database connections.
        self.add_action_to_menu_bar("Change Database Connections", self.activate_new_connection_dialog)
        # Create an action for showing the current history.
        self.add_action_to_menu_bar("Show History", self.activate_command_history_dialog)
        self.add_action_to_menu_bar("Import CSV", self.activate_csv_import)
        # Create a sub menu for settings.
        settings_menu = QMenu("Settings", self)
        # Add the sub menu to the edit menu point.
        self.edit_menu.addMenu(settings_menu)
        # Add an action for opening a configuration settings dialog to the sub menu for settings.
        self.add_action_to_menu_bar("Configuration Settings", self.activate_new_configuration_settings_dialog,
                                    alternate_menu=settings_menu)
        # Add an action for opening an editor appearance settings dialog to the sub menu for settings.
        self.add_action_to_menu_bar("Editor Appearance Settings", self.activate_new_editor_appearance_dialog,
                                    alternate_menu=settings_menu)

        # Add an action for leaving the application.
        self.add_action_to_menu_bar("Exit", self.close_program)

        # Create a new menu bar point: An editor menu.
        editor_menu = self.menu_bar.addMenu("Editor")

        # Add the search dialog in the editor to the editor menu.
        self.add_action_to_menu_bar("Search", self.search_usage_in_editor, alternate_menu=editor_menu)

        info_menu = self.menu_bar.addMenu("Info")
        self.add_action_to_menu_bar("Version", self.show_version_information_dialog,
                                    alternate_menu=info_menu)

    def add_action_to_menu_bar(self, action_name, connected_function, alternate_menu=None):
        """
        Add a new action to the menu bar. A name of the new action and the function for connecting is required. First, a
        new action is defined. The new action is connected to the new function. The action with the function is added to
        the menu bar. If the alternate menu is not None, the alternate menu is used.
        """

        # Define a new action.
        new_action = QAction(action_name, self)
        # Connect the action with the given function.
        new_action.triggered.connect(connected_function)

        # Check for the alternate menu: If the alternate menu is not a QMenu, use the default menu.
        if not isinstance(alternate_menu, QMenu):
            # Add the point to the menu bar.
            self.edit_menu.addAction(new_action)

        # Use a alternate menu.
        else:
            # Add the action to the alternate menu.
            alternate_menu.addAction(new_action)

    def init_tool_bar(self):
        """
        Create a tool bar with its actions.
        """

        # Create a tool bar.
        self.tool_bar = QToolBar()
        # Set the tool bar as not movable.
        self.tool_bar.setMovable(False)
        # Add the tool bar to the window.
        self.addToolBar(self.tool_bar)

        # Add a function for executing a query to the tool bar.
        self.add_action_to_tool_bar("Execute Query", "execute.svg", self.execute_query_in_current_editor_widget)
        # Add a function for saving the current editor to the tool bar.
        self.add_action_to_tool_bar("Save Current Editor", "save.svg", self.save_current_editor_widget_statement)
        # Add a function for loading a previous statement in a file to the tool bar.
        self.add_action_to_tool_bar("Load File", "load.svg", self.load_editor_widget_statement)
        # Add a function for creating a new editor.
        self.add_action_to_tool_bar("New Editor", "editor.svg", self.activate_new_editor_tab)
        # Add a function for activating a new history command dialog.
        self.add_action_to_tool_bar("Show History", "history.svg", self.activate_command_history_dialog)

    def add_action_to_tool_bar(self, action_description, action_icon_file, connected_function):
        """
        Add a new action to the tool bar. The required arguments are a description of the action, a file for an icon and
        a function for the action. The description is used as definition and tool tip. The file for the icon is
        necessary for showing a corresponding icon in the tool bar. The connected function is triggered by the new
        action.
        """

        # Create a new action with the given description. The description as name is necessary for potentially missing
        # icons, so the action has still a usable definition.
        new_action = QAction(action_description, self)
        # Set the tool tip with the given description. A tool tip provides more usability, if the icon does not describe
        # the function properly for the user.
        new_action.setToolTip(action_description)

        # Define the path of the icon.
        icon_path = os.path.join(os.path.dirname(pygadmin.__file__), "icons", action_icon_file)

        # Check for the existence of the path for an icon.
        if os.path.exists(icon_path):
            # Make an empty QIcon.
            icon = QIcon()
            # Add a pixmap to the QIcon with the already checked path.
            icon.addPixmap(QPixmap(icon_path))
            # Add the icon to the new action.
            new_action.setIcon(icon)

        else:
            logging.warning("Icon was not found for the path {} in the tool bar.".format(icon_path))

        # Connect the new action with the designated function.
        new_action.triggered.connect(connected_function)
        # Add the new action to the tool bar.
        self.tool_bar.addAction(new_action)

    def activate_new_editor_tab(self):
        """
        Use the method of the mdi area to generate a new editor tab.
        """

        return self.mdi_area.generate_editor_tab()

    def activate_new_connection_dialog(self, current_selection_identifier=None):
        """
        Activate a new connection dialog, so the user can enter data about a new database connection. The connection
        parameters are checked and if they are accepted, a signal is used. This signal uses the tree widget (in the
        dock widget) to refresh the tree and show the new connection to the user.
        There is also a current selection identifier for a pre-selected connection.
        """

        # Create a new connection dialog widget.
        self.new_connection_dialog = ConnectionDialogWidget()
        self.new_connection_dialog.open_at_start_checkbox.setVisible(False)

        # Check for a identifier of a currently selected connection.
        if current_selection_identifier is not None:
            # Use the function of the class connection dialog for finding the identifier and selecting it.
            self.new_connection_dialog.find_occurrence_in_list_widget_and_select_item(current_selection_identifier)

        # Connect the modified connection dialog to a function of the tree widget for refreshing the tree model.
        self.new_connection_dialog.get_modified_connection_parameters.connect(self.change_tree_connection)
        # Connect the signal for a changed timeout with the function for setting this new timeout in the current active
        # connection.
        self.new_connection_dialog.new_timeout_for_connections.connect(
            self.set_new_timeout_in_current_active_connection)

    def activate_new_configuration_settings_dialog(self):
        """
        Activate a new configuration settings dialog.
        """

        self.configuration_settings_dialog = ConfigurationSettingsDialog()

    def activate_new_editor_appearance_dialog(self):
        """
        Activate a new editor appearance dialog.
        """

        self.editor_appearance_dialog = EditorAppearanceSettingsDialog()

    @pyqtSlot(tuple)
    def change_tree_connection(self, modified_connection_information):
        """
        Use the given, modified connection with its parameters to update the database connection(s) of the tree.
        """

        # Use the function for updating the tree's connection.
        self.dock_widget.tree.update_tree_connection(modified_connection_information)

    @pyqtSlot(tuple)
    def change_tree_structure(self, modified_connection_information):
        """
        Use a function for changing the tree structure and submit the relevant modified connection parameters.
        """

        self.dock_widget.tree.update_tree_structure(modified_connection_information)

    @pyqtSlot(bool)
    def set_new_timeout_in_current_active_connection(self):
        """
        Find the current editor widget and establish a new connection with the new timeout.
        """

        # Get the current editor widget.
        current_widget = self.mdi_area.determine_current_editor_widget()

        # If the current editor widget is not None and the widget is not empty, which means there is no text and no
        # connection, proceed.
        if current_widget is not None and not current_widget.is_editor_empty():
            # Reestablish the connection.
            current_widget.reestablish_connection()

    def execute_query_in_current_editor_widget(self):
        """
        Get the current editor widget and execute the query, if the requirements (existing editor widget and valid, open
        connection) are fulfilled.
        """

        # Get the current editor widget with a function of the MdiArea.
        current_editor_widget = self.mdi_area.determine_current_editor_widget()

        # Check, if a current editor widget exists and proceed.
        if current_editor_widget is not None:
            # Check for a valid connection with a function of the editor widget.
            if current_editor_widget.database_query_executor.is_connection_valid() is True:
                # Execute the current query.
                current_editor_widget.execute_current_query()

                # Leave the function, because everything for a valid case is done and the following part describes the
                # default error case.
                return

        # Describe the error for saving in the log and showing to the user.
        database_error_message = "The query cannot be executed, because a database is not chosen or is invalid."
        # Save the error in the log.
        logging.error(database_error_message)
        # Show the error to the user as message box.
        QMessageBox.critical(self, "Connection Error", database_error_message)

    def save_current_editor_widget_statement(self, save_as=False):
        """
        Try to save the current content of the current editor widget. Determine, if a current editor widget exists. If
        a current editor widget exists, save the current statement in the file. If the option "save_as" is True, open
        always a file dialog. If the option is False, a file dialog is opened in the corner case for a not saved file.
        """

        # Get the current editor widget.
        current_editor_widget = self.mdi_area.determine_current_editor_widget()

        # Check, if the current editor widget exists.
        if current_editor_widget is not None:
            # Check for the configuration settings, because getting the corresponding saved file is only necessary for
            # the step for opening previous files.
            if global_app_configurator.get_single_configuration("open_previous_files") is True:
                # Get the current corresponding file name for the usage as previous file name, so an overwrite in the
                # editor for the global file manager can be realized.
                current_corresponding_file = current_editor_widget.corresponding_saved_file

            # The corresponding file is unnecessary, if the configuration is not True.
            else:
                current_corresponding_file = None

            # Check the parameter for save_as. If the parameter is True, the if clause gets to the point for a new
            # file dialog. If the result of this file dialog is False, end the function with a return. In this case,
            # the process has been aborted.
            if save_as is True and current_editor_widget.activate_file_dialog_for_saving_current_statement() is False:
                # End the function with a return.
                return

            # Save the current statement and text in the query input editor with the function of the editor widget.
            current_editor_widget.save_current_statement_in_file(current_corresponding_file)

        # Define an else branch for error handling with a non existing current editor widget.
        else:
            # Describe the error for saving in the log and showing to the user.
            save_error_message = "The statement in the current editor widget cannot be saved, because there is not a " \
                                 "current editor widget."

            # Save the error in the log.
            logging.error(save_error_message)
            # Raise a message box with the error to inform the user.
            QMessageBox.critical(self, "Saving Error", save_error_message)

    def load_editor_widget_statement(self):
        """
        Use a QFileDialog for loading the content of a saved file into a fresh editor widget. If there is an empty
        editor widget  this widget is used. If there is no such widget, create a new one.
        Finding the correct widget and then opening the file dialog is necessary, because a QFileDialog produces bugs
        with showing the current/active sub window and its widget after their creation.
        """

        # If an empty editor widget is already existing, get this editor.
        empty_editor_widget = self.mdi_area.determine_next_empty_editor_widget()
        # Declare the boolean for the necessity of a new editor. This value is False as default.
        new_editor_necessary = False

        # Save the current active sub window as previous active sub window, so if the process of choosing a file
        # is aborted, this previous sub window is known and the old state can be reproduced.
        previous_active_sub_window = self.mdi_area.activeSubWindow()

        # Check for an existing empty editor widget, because the function for finding one can return None for a failed
        # search.
        if empty_editor_widget is None:
            # Create a new editor widget, which is empty as default
            empty_editor_widget = self.activate_new_editor_tab()
            # Set the boolean for the necessity of a new editor to True, because a new empty editor is created.
            new_editor_necessary = True

        # If there is an existing editor widget, activate the corresponding sub window.
        else:
            # Set the active sub window to the parent of the empty editor widget. This is the corresponding sub window
            # in the MdiArea.
            self.mdi_area.setActiveSubWindow(empty_editor_widget.parent())

        # If the process of loading the file in the editor failed, the return value is False.
        if empty_editor_widget.load_statement_out_of_file() is False:
            # If a new editor was necessary, proceed with the closing event of the corresponding sub window.
            if new_editor_necessary:
                # Close the sub window of the new editor widget.
                self.mdi_area.closeActiveSubWindow()

            # If a new editor was  not necessary, use the previous active sub window.
            else:
                # Use the previous active sub window as new active sub window, so the state before the file process is
                # reproduced.
                self.mdi_area.setActiveSubWindow(previous_active_sub_window)

    def load_editor_with_connection_and_query(self, database_connection_parameter, drop_statement):
        """
        Use the given database connection parameters for creating a new editor widget with the given connection. If
        there is an editor widget without a statement and the appropriate connection, use it. Set the given statement
        as text.
        """

        # Determine the editor widget for the parameters.
        editor_widget = self.mdi_area.determine_empty_editor_widget_with_connection(database_connection_parameter)
        # Set the text in the editor. The text is the given drop statement.
        editor_widget.query_input_editor.setText(drop_statement)

    def load_empty_editor_with_command(self, command):
        """
        Get a command and set this command as text of an empty editor.
        """

        # If an empty editor widget is already existing, get this editor.
        empty_editor_widget = self.mdi_area.determine_next_empty_editor_widget()

        # Check for an existing empty editor widget, because the function for finding one can return None for a failed
        # search.
        if empty_editor_widget is None:
            # Create a new editor widget, which is empty as default
            empty_editor_widget = self.activate_new_editor_tab()

        # Set the text to the query input editor of the editor widget.
        empty_editor_widget.query_input_editor.setText(command)

    def activate_csv_import(self):
        """
        Activate the necessary steps for starting the csv import dialog. This process includes getting the csv file by
        a file dialog and getting the current database connection. TODO: Think about a better place for the importer or
         error for missing database connection.
        """

        file_name_and_type = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV (*.csv)")
        file_name = file_name_and_type[0]

        # The user has aborted the process, so the file name is an empty string, which is useless.
        if file_name == "":
            return

    @pyqtSlot(str)
    def show_status_bar_message(self, message):
        """
        Set the current text of the status bar.
        """

        self.statusBar().showMessage(message)

    def search_usage_in_editor(self):
        """
        Get the current editor and if a current editor exists, open its search dialog.
        """

        # Get the current editor with the mdi area.
        current_editor = self.mdi_area.determine_current_editor_widget()

        # Proceed, if a current editor exists.
        if current_editor is not None:
            # Open the search dialog.
            current_editor.open_search_dialog()

    def show_version_information_dialog(self):
        """
        Activate a dialog for showing the current information of the application.
        """

        self.version_information_dialog = VersionInformationDialog()

    def activate_command_history_dialog(self):
        """
        Activate a command history widget.
        """

        self.command_history_dialog = CommandHistoryDialog()
        # Connect the signal for getting the command with a double click in the history with the function for loading an
        # empty editor with this command.
        self.command_history_dialog.get_double_click_command.connect(self.load_empty_editor_with_command)

    def close_program(self):
        """
        Define a wrapper function for closing the application.
        """

        self.close()
