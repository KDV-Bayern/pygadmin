import logging
import re
import datetime

from PyQt5 import QtGui
from PyQt5.Qsci import QsciScintilla
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QEvent
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QTableView, QMessageBox, QShortcut, QFileDialog, \
    QCheckBox, QLabel, qApp

from pygadmin.connectionfactory import global_connection_factory
from pygadmin.models.tablemodel import TableModel
from pygadmin.configurator import global_app_configurator
from pygadmin.models.lexer import SQLLexer
from pygadmin.database_query_executor import DatabaseQueryExecutor
from pygadmin.widgets.search_replace_widget import SearchReplaceWidget
from pygadmin.widgets.search_replace_parent import SearchReplaceParent
from pygadmin.command_history_store import global_command_history_store
from pygadmin.file_manager import global_file_manager


class MetaEditor(type(QWidget), type(SearchReplaceParent)):
    """
    Define a meta class for the Editor Widget for preventing a meta class conflict. The editor should implement QWidget
    and an interface for providing the methods, which are required by a parent of the search replace widget.
    """

    pass


class EditorWidget(QWidget, SearchReplaceParent, metaclass=MetaEditor):
    """
    Create a class which is a child class of QWidget as an interface for an editor window/widget. The class shows the
    GUI components for entering and submitting an SQL query. The data about the database connection is received with a
    pyqtSlot.
    """

    # Define a signal for a structural change in tables, views, schemas and databases.
    structural_change_in_view_table = pyqtSignal(tuple)
    # Define a signal for a change in the current status message.
    change_in_status_message = pyqtSignal(str)

    def __init__(self):
        """
        Make sub functions for initializing the widget, separated by the parts user interface, grid layout and SQL
        lexer.
        """

        super().__init__()
        self.init_ui()
        self.init_grid()
        self.init_lexer()

    def init_ui(self):
        """
        Design the user interface and its components.
        """

        # Create an input field with QsciScintilla as SQL editor field.
        self.query_input_editor = QsciScintilla()

        # Initialize the table model with an empty data list because data from SQL queries
        self.table_model = TableModel([])
        self.table_view = QTableView()
        # Use the table view with the customized table model.
        self.table_view.setModel(self.table_model)
        self.table_view.installEventFilter(self)

        # Set the current database connection to None because all parameters for a database connection are received by a
        # signal.
        self.current_database_connection = None

        # Set the connection identifier to None.
        self.connection_identifier = None

        # Get a database executor.
        self.database_query_executor = DatabaseQueryExecutor()
        # Connect the function for new data with the refresh of the table model.
        self.database_query_executor.result_data.connect(self.refresh_table_model)
        # Connect the function for processing an error with the error.
        self.database_query_executor.error.connect(self.process_query_error)
        # Connect the new query status message with the function for checking the query status message.
        self.database_query_executor.query_status_message.connect(self.check_query_status_message)
        # Connect the new database connection with a function for refreshing the database connection.
        self.database_query_executor.new_database_connection.connect(self.refresh_database_connection)

        self.long_description = QLabel()

        # Create a button for submitting a query.
        self.submit_query_button = QPushButton("Submit Query")
        self.submit_query_button.clicked.connect(self.execute_current_query)

        # Create a shortcut for submitting a query.
        self.submit_query_shortcut = QShortcut(QKeySequence("F5"), self)
        # Use a function for the shortcut, which checks also the validity of the connection and executes a query or
        # shows an error to the user.
        self.submit_query_shortcut.activated.connect(self.check_for_valid_connection_and_execute_query_with_shortcut)

        # Check for enabling and disabling of the button for submitting a query.
        self.check_enabling_of_submit_button()

        # Create a button for stopping a query.
        self.stop_query_button = QPushButton("Stop Query")
        self.stop_query_button.clicked.connect(self.stop_current_query)

        self.stop_query_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        self.stop_query_shortcut.setEnabled(False)
        self.stop_query_shortcut.activated.connect(self.stop_current_query)

        # Set the button and the shortcut for stopping a query as disabled as default, because a query only needs to be
        # stopped when a query is currently executed.
        self.set_stop_query_element_activate(False)

        # Set the corresponding saved file to None: This parameter will be overwritten later.
        self.corresponding_saved_file = None
        # Set the current text to an empty string. This text will be overwritten by the saved state of the file or the
        # loaded state.
        self.current_editor_text = ""
        # Connect a change of text to an update of the window title. This statement changes the status of saved or
        # unsaved of the current text.
        self.query_input_editor.textChanged.connect(self.update_window_title_and_description)

        # Create a shortcut for saving the current text/statement in the editor.
        self.save_current_sql_statement_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        # Connect the shortcut with the function for saving the current statement in a file.
        self.save_current_sql_statement_shortcut.activated.connect(self.save_current_statement_in_file)

        # Create a shortcut for opening a loaded file.
        self.open_previous_file_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        # Connect the shortcut to a function with more user dialog.
        self.open_previous_file_shortcut.activated.connect(self.load_file_with_potential_overwrite_in_editor)

        # Create a search replace widget with this editor widget as parent.
        self.search_replace_widget = SearchReplaceWidget(self)
        # Set the button disabled, because initially, there is no search, so there is no next.
        self.deactivate_search_next_and_replace_buttons_and_deselect()
        # Set the widget invisible, so it is only activated for a search.
        self.close_search_replace_widget()

        # Define a short cut for the search dialog.
        self.search_usages_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.search_usages_shortcut.activated.connect(self.open_search_dialog)

        # Define a short cut for the extended search dialog with a replace function.
        self.replace_usages_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        self.replace_usages_shortcut.activated.connect(self.open_replace_dialog)

        # Create a button for exporting the result to a csv.
        self.export_csv_button = QPushButton("Export result to .csv")
        # Connect the button with the function for exporting and saving the csv data.
        self.export_csv_button.clicked.connect(self.export_and_save_csv_data)
        # Set the button as invisible as default, because at the beginning, an export is not necessary.
        self.export_csv_button.setVisible(False)

        self.setGeometry(600, 600, 500, 300)

        self.update_window_title_and_description()

        self.show()

    def init_grid(self):
        """
        Set a grid layout to the widget and place all its components.
        """

        # Define the layout.
        grid_layout = QGridLayout(self)

        grid_layout.addWidget(self.long_description, 0, 0, 1, 4)
        # Set the search and replace widget.
        grid_layout.addWidget(self.search_replace_widget, 1, 0, 2, 4)

        # Set the input field for SQL queries as element at the top.
        grid_layout.addWidget(self.query_input_editor, 3, 0, 1, 4)
        # Set the export button above the table view.
        grid_layout.addWidget(self.export_csv_button, 4, 0, 1, 4)
        # Set the table view as window for results between the input field for SQL queries and the button for submitting
        # the query.
        grid_layout.addWidget(self.table_view, 5, 0, 1, 4)
        # Set the submit button for the SQL queries as element at the bottom.
        grid_layout.addWidget(self.submit_query_button, 6, 0, 1, 4)
        # Place the stop button below the submit button.
        grid_layout.addWidget(self.stop_query_button, 7, 0, 1, 4)

        grid_layout.setSpacing(10)

        self.setLayout(grid_layout)

    def init_lexer(self):
        """
        Configure the lexer for SQL queries and the SQL language in general, so syntax highlighting is enabled.
        """

        # Get the custom lexer as input field for the SQL queries.
        self.lexer = SQLLexer(self.query_input_editor)
        # Assign the lexer to the input field for SQL queries.
        self.query_input_editor.setLexer(self.lexer)
        # Enable UTF8 support as common standard for encoding.
        self.query_input_editor.setUtf8(True)

    @pyqtSlot(dict)
    def set_connection_based_on_parameters(self, connection_parameter_dictionary):
        """
        Get a database connection based on given parameters in a dictionary which could be received by a pyqtSlot. Check
        also for potential errors which could occur and report them to the user.
        """

        # Use the global connection factory to get a connection which is used as current database connection of the
        # class.
        self.current_database_connection = global_connection_factory.get_database_connection(
            connection_parameter_dictionary["host"],
            connection_parameter_dictionary["user"],
            connection_parameter_dictionary["database"],
            connection_parameter_dictionary["port"])

        # Define a connection identifier. Its existence is not limited by a failed connection, because it is relevant to
        # know which specific connection has failed.
        self.connection_identifier = "{}@{}:{}/{}".format(connection_parameter_dictionary["user"],
                                                          connection_parameter_dictionary["host"],
                                                          connection_parameter_dictionary["port"],
                                                          connection_parameter_dictionary["database"])

        # If the database connection is None, this is caused by one specific error, which is defined by the connection
        # factory with the return value None. The reason can be shown to the user as the error is mostly cause by them.
        if self.current_database_connection is None:
            password_none_error_topic = "Password Error"
            # Specify the error by showing which user is affected.
            password_none_error_message = "A password cannot be found for {}. Please check for a " \
                                          "given password.".format(connection_parameter_dictionary["user"])
            # Use the function for error handling.
            self.connection_failed_error_handling(password_none_error_topic, password_none_error_message)

        # If the database connection is False, this is caused by a wider range of errors.
        if self.current_database_connection is False:
            connection_error_topic = "Connection Error"
            connection_error_message = "An error occurred during the database connection process. There is a huge " \
                                       "range of possible reasons for example a wrong password or problems with the " \
                                       "database server. Please check the log for further information."
            # Use the function for error handling
            self.connection_failed_error_handling(connection_error_topic, connection_error_message)

        # Set the new database connection as database connection of the database query executor.
        self.database_query_executor.database_connection = self.current_database_connection

        # Check for enabling or disabling the button and the shortcut for submitting a query based on the new result of
        # the established connection.
        self.check_enabling_of_submit_button()

        # Update the window title to the current status of the database connection.
        self.update_window_title_and_description()

    def execute_current_query(self):
        """
        Check for a valid connection and execute the current (selected) content of the editor in a separate thread. The
        separate thread emits signals for processing the result of the query. This process is realized by the database
        query executor.
        """

        # At this point, the query will be executed and the process will begin, so a signal for a status bar is emitted,
        # which can be used by a main window. This method with a signal is safer than finding the main window in the
        # parents of this widget.
        self.change_in_status_message.emit("Executing Query")

        # Activate the button and the shortcut for stopping the current query.
        self.set_stop_query_element_activate(True)

        # Set the button invisible during a query.
        self.export_csv_button.setVisible(False)

        # Get the query for executing.
        query_to_execute = self.get_query_in_input_editor()

        # If the query is not None for an error or abort during the check process, continue.
        if query_to_execute is not None:
            # Define the query to execute as database query of the executor.
            self.database_query_executor.database_query = query_to_execute
            # Submit and execute the query with the given parameters.
            self.database_query_executor.submit_and_execute_query()

    def get_query_in_input_editor(self, check=True):
        """
        Get the current query out of the input editor. If there is a selected part of the text in the editor, then use
        only the selected text as query. Set the check to True as default, so the query is preprocessed.
        """

        # If the selected text contains an empty string, there is not any selected text.
        if self.query_input_editor.selectedText() == "":
            # The query to execute is the whole text in the input editor.
            query_to_execute = self.query_input_editor.text()

        # Use the current selection in the editor.
        else:
            query_to_execute = self.query_input_editor.selectedText()

        # If the check parameter is True, check the query.
        if check is True:
            # If the check returns a problem, set the query to None.
            if self.check_current_query_for_single_update_delete(query_to_execute) is False:
                query_to_execute = None

        return query_to_execute

    def check_current_query_for_single_update_delete(self, query):
        """
        Check the given query for a single UPDATE or DELETE without any WHERE. This would execute the DELETE or UPDATE
        for every row in the table. So this function is for warning the user in case they would like to execute such a
        query.
        """

        # Check the global app configurator, if the user has set the configuration to False, so they does not want any
        # warnings. In this case, stop the check with a return.
        if global_app_configurator.get_single_configuration("check_where") is False:
            return

        # Set the whole query to lower case, so it is easier to check, if there is an UPDATE or DELETE without a WHERE.
        query = query.lower()
        # Check the query: If the query contains a delete or an update, there could be a problem. If the query does not
        # contain a where, there is a problem.
        if ("delete" in query or "update" in query) and "where" not in query:
            # Ask the user how to proceed.
            question_message_box = QMessageBox.question(self, "Query without WHERE", "Your query contains an UPDATE"
                                                                                     " or a DELETE without a WHERE."
                                                                                     "Proceed anyway? (Ignore for "
                                                                                     "ignoring those warnings in "
                                                                                     "the future)",
                                                        QMessageBox.Yes | QMessageBox.No | QMessageBox.Ignore)

            # Proceed normally for a yes.
            if question_message_box == QMessageBox.Yes:
                return True

            # Stop the process for a no.
            elif question_message_box == QMessageBox.No:
                return False

            # Proceed with setting the configuration and normally for an ignore.
            elif question_message_box == QMessageBox.Ignore:
                global_app_configurator.set_single_configuration("check_where", False)
                global_app_configurator.save_configuration_data()
                return True

    def refresh_table_model(self, result_data_list, save_command=True):
        """
        Refresh the table model with the given result data list. As default, the used command is saved.
        """

        # Add the given result list with its current content to the table model for showing the result.
        self.table_model.refresh_data_list(result_data_list)
        self.table_view.resizeColumnsToContents()

        # At this point, a new query can be executed, so the status message is changed to ready again.
        self.change_in_status_message.emit("Ready")

        # Disable the button and the short cut for stopping a query, because a query is currently not executed.
        self.set_stop_query_element_activate(False)

        # Set the export button visible after a result.
        self.export_csv_button.setVisible(True)

        # Check, if the command should be saved.
        if save_command:
            # Save the used command of the query in the command history.
            self.save_command_in_history()

    def process_query_error(self, error_tuple):
        """
        Get a tuple for an error. This tuple contains the title of an error and its description. This error is shown to
        the user.
        """

        # Use a message box for showing an error to the user.
        QMessageBox.critical(self, error_tuple[0], error_tuple[1])

    def connection_failed_error_handling(self, error_topic, error_message):
        """
        Handle a failed connection and show an adequate error to the user without a message box, because they occur so
        often with a failed connection, it is truly annoying.. Use the identifier of the connection to show the user the
        failed connection in the title of the widget.
        """

        # Enter the two error parameters in a list, which can be used by the table model for showing the connection
        # error data again to the user.
        error_result_list = [[error_topic], (error_message,)]
        # Show the error in the table model and do not save the command, which caused the error.
        self.refresh_table_model(error_result_list, save_command=False)

    def check_enabling_of_submit_button(self):
        """
        Check for enabling or disabling the button and the shortcut for submitting a query. There is a check for a valid
        connection with a specified function.
        """

        # If the connection is valid, the button is enabled. If the connection is invalid, the button is disabled.
        self.submit_query_button.setEnabled(self.database_query_executor.is_connection_valid())

    def check_query_status_message(self, status_message):
        """
        Check the class wide object for a status message, which is set after executing a query and emit a signal, if the
        status message contains a "TABLE" or "VIEW" or "SCHEMA".
        """

        # Check for a valid status message, which is not None.
        if status_message is not None:
            # Check the query status message for the occurrence of "TABLE", "VIEW", "SCHEMA" or "DATABASE". These words
            # normally occur in a status message, if a table or view or schema or database is created, deleted, altered
            # or dropped. As a result, the tree must be updated to the current database circumstances.
            table_view_schema_pattern = re.search("TABLE|VIEW|SCHEMA|DATABASE", status_message)

            # If such a pattern is found, the variable is not None.
            if table_view_schema_pattern is not None:
                # Get the first result of the pattern, either the word "TABLE" or the word "VIEW" or the word "SCHEMA".
                table_view_schema_pattern = table_view_schema_pattern.group(0)
                # Get the parameters of the current connections. Based on the current connection, a change was made, so
                # this connection needs to be updated and informed about the change.
                database_connection_parameters = global_connection_factory.get_database_connection_parameters(
                    self.current_database_connection)

                # Emit the pattern and the connection parameters, so a slot can received them.
                self.structural_change_in_view_table.emit((table_view_schema_pattern, database_connection_parameters))

    def stop_current_query(self):
        """
        Stop the current query with a function of the database query executor.
        """

        self.database_query_executor.cancel_current_query()

    def set_stop_query_element_activate(self, activation):
        """
        (De)activate the GUI elements for stopping a query with a bool, which contains the relevant True/False
        parameter.
        """

        # Check for a bool.
        if isinstance(activation, bool):
            # (De)activate the button and the shortcut.
            self.stop_query_button.setEnabled(activation)
            self.stop_query_shortcut.setEnabled(activation)

    def save_current_statement_in_file(self, previous_file_name=None):
        """
        Save the current text/statement of the lexer as query editor in for further usage. The class-wide variable for
        the corresponding file is used as directory with file. If this variable contains its initialized value None,
        use the function for opening a file dialog. A default parameter is used for the previous file name. In this case
        the previous corresponding saved file is used. If a file name is given, the given one is used.
        """

        # Check for the configuration and the previous file name: if the previous file name is None, get the name of the
        # current corresponding saved file, because this one is going to be the previous one.
        if previous_file_name is None and global_app_configurator.get_single_configuration("open_previous_files") is \
                True:
            previous_file_name = self.corresponding_saved_file

        # Check if the class-wide variable for the corresponding file is None.
        if self.corresponding_saved_file is None:
            # Open a file dialog and if the result is False, the process has been aborted.
            if self.activate_file_dialog_for_saving_current_statement() is False:
                # End the function with a return.
                return

        try:
            # Open the file in the write mode, so every content is also overwritten.
            with open(self.corresponding_saved_file, "w") as file_to_save:
                # Define the current text of the query input editor as current text.
                current_text = self.query_input_editor.text()
                # Write the current text of the lexer as SQL editor in the file.
                file_to_save.write(current_text)

        # Parse the error for writing in the file.
        except Exception as file_error:
            # Define an error text.
            error_text = "The file {} cannot be written with the error: {}".format(self.corresponding_saved_file,
                                                                                   file_error)

            # Show the error to the user and save it in the log.
            QMessageBox.critical(self, "File Reading Error", error_text)
            logging.critical(error_text, exc_info=True)

            # Redefine the corresponding saved file back to the previous one.
            self.corresponding_saved_file = previous_file_name

            # End the function after a failure, because the following part is not necessary.
            return

        # If the corresponding file name is not the previous file and the configuration for opening the previous files
        # is True, the old file will be deleted as previous file and the new one added.
        if self.corresponding_saved_file != previous_file_name \
                and global_app_configurator.get_single_configuration("open_previous_files") is True:
            # Delete the previous one.
            global_file_manager.delete_file(previous_file_name)
            # Add the new one.
            global_file_manager.add_new_file(self.corresponding_saved_file)
            # Commit/save the change.
            global_file_manager.commit_current_files_to_yaml()

        # Save the current text in the class-wide current editor text.
        self.current_editor_text = current_text

        # Update the current window title.
        self.update_window_title_and_description()

    def activate_file_dialog_for_saving_current_statement(self):
        """
        Activate a file dialog, so the current widget can be saved with the name and directory chosen by the user. Use
        the class wide variable for the corresponding file as container for the file name. Return the success of the
        operation with a boolean, because the process can be aborted by the user.
        """

        # Create a file dialog for saving the content of the current editor tab.
        file_dialog_with_name_and_type = QFileDialog.getSaveFileName(self, "Save File")
        # The variable file_dialog_with_name_and_type is a tuple. The zeroth variable of the tuple contains the name
        # of the saved file, while the first one contains the valid types for a file.
        file_name = file_dialog_with_name_and_type[0]

        # The file name contains an empty string, the process for saving a file was aborted, so this if branch is
        # only activate for the purpose of the user to save a file.
        if file_name != "":
            # Define the corresponding file as given file name.
            self.corresponding_saved_file = file_name

            # Return the success.
            return True

        # This else branch is activate for an aborted process in the QFileDialog for saving the file.
        else:
            logging.info("The current file saving process was aborted by the user, so the current editor tab is "
                         "not saved.")

            # Return the abortion.
            return False

    def load_statement_out_of_file(self):
        """
        Load a previous saved file with the help of QFileDialog. Save the file name in the class-wide variable for
        the corresponding file. Report the success of the function with a boolean.
        """

        # Get the file name and the types of the file.
        file_name_and_type = QFileDialog.getOpenFileName(self, "Open File")
        # Get the file name out of the tuple.
        file_name = file_name_and_type[0]

        # If the file name is false, the process has been aborted.
        if file_name is False:
            logging.info("The current file opening process was aborted by the user, so the content of this file is not "
                         "loaded.")

            # End the function with a return.
            return False

        # Try to load the statement based on the file name.
        return self.load_statement_with_file_name(file_name)

    def load_statement_with_file_name(self, file_name):
        """
        Load the content of the file with its given name and path.
        """

        # Check for the success in form of an existing file and not an empty string.
        if file_name != "":
            # Try to open the file. This operation can fail without the correct file rights.
            try:
                # Open the file in reading mode.
                with open(file_name, "r") as file_to_load:
                    # Read the whole given file and save its text.
                    file_text = file_to_load.read()

            # Show an error to the user, if the file reading process has failed.
            except Exception as file_error:
                error_text = "The file {} cannot be loaded with the error: {}".format(file_name, file_error)
                QMessageBox.critical(self, "File Reading Error", error_text)
                logging.critical(error_text, exc_info=True)

                # Return False for the error.
                return False

            # If the option for open the previous files is activated and if the current corresponding save file is not
            # None, delete it in the file manager, because it will be replaced by a new one.
            if global_app_configurator.get_single_configuration("open_previous_files") is True and \
                    self.corresponding_saved_file is not None:
                global_file_manager.delete_file(self.corresponding_saved_file)

            # Save the name of the file in the class variable for the corresponding file.
            self.corresponding_saved_file = file_name

            # If the configuration is set, save the new corresponding save file and commit the changes to the file
            # manager.
            if global_app_configurator.get_single_configuration("open_previous_files") is True:
                global_file_manager.add_new_file(self.corresponding_saved_file)
                global_file_manager.commit_current_files_to_yaml()

            # Show the content of the file as text in the lexer as SQL query editor.
            self.query_input_editor.setText(file_text)
            # Save the text of the file in the class-wide variable for the current text to check for changes and get the
            # current state of saved/unsaved.
            self.current_editor_text = file_text

            # Update the window title
            self.update_window_title_and_description()

            # Report the success with a return value.
            return True

    def load_file_with_potential_overwrite_in_editor(self):
        """
        Load an existing file in the editor widget. This function is a wrapper for load_statement_out_of_file with more
        user interaction under specific circumstances. If the editor is not empty and a global configuration for
        allowing the overwrite without questioning is not set, ask the user.
        """

        # Check for an empty editor and the global configuration for overwriting. The check for an empty and not a
        # saved editor is to avoid the annoying effect of opening a file again, caused by an overwrite of the content in
        # the widget.
        if self.is_editor_empty() is False and \
                global_app_configurator.get_single_configuration("always_overwrite_editor") is not True:
            # Use the custom message box and it's result. If an overwrite is not required, end the function with a
            # return.
            if self.use_custom_message_box_for_user_feedback_about_editor_content_overwrite() is False:
                # End the function with a return.
                return

        # Load the statement out of the file. At this point, the user confirmed their acceptance of an overwrite.
        self.load_statement_out_of_file()

    def use_custom_message_box_for_user_feedback_about_editor_content_overwrite(self):
        """
        Create a custom message box for asking the user about a potential overwrite. A custom message box is necessary
        for the usage of the checkbox. The user can chose between an overwrite of the current content in the editor and
        the persistence of the content. A checkbox is used for a configuration, so the user can decide to overwrite all
        files as default. The return value of the function is the answer to the question of the message box.
        """

        # Create a custom message box with the editor widget as parent.
        custom_message_question_box = QMessageBox(parent=self)
        # Set the title to a short form of the question.
        custom_message_question_box.setWindowTitle("Overwrite Editor?")
        # Set the text to a longer form of the question.
        custom_message_question_box.setText("Do you want to overwrite the current editor content?")
        # Use two standard buttons: A button for yes and a button for no.
        custom_message_question_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        # Set the icon to the typical QMessageBox question icon.
        custom_message_question_box.setIcon(QMessageBox.Question)
        # Define the checkbox with its text and function: Always overwrite the current editor and stop questioning.
        self.overwrite_editor_always_checkbox = QCheckBox("Always overwrite current editor")
        # Connect the state change to a function for setting the editor configuration.
        self.overwrite_editor_always_checkbox.stateChanged.connect(self.set_always_overwrite_editor_configuration)
        # Set the checkbox as part of the message box.
        custom_message_question_box.setCheckBox(self.overwrite_editor_always_checkbox)
        # Execute the message box. This is preferred over show(), so the rest of the function is executed after closing
        # the message box.
        custom_message_question_box.exec_()

        # Save the new data in the global app configurator.
        global_app_configurator.save_configuration_data()

        # Check the result of the clicked button, which closed the message box. "&Yes" is returned by Qt for clicking
        # the yes button.
        if custom_message_question_box.clickedButton().text() == "&Yes":
            # Return True for a yes.
            return True

        else:
            # Return False for a no.
            return False

    def is_editor_empty(self):
        """
        Check the editor widget for its own potential emptiness. An editor is empty, if the title is the default title
        and the field for a query is without text.
        """

        # Check the title and the text for emptiness.
        if self.windowTitle() == "" and self.query_input_editor.text() == "":
            # Return True for emptiness.
            return True

        else:
            # Return False for missing emptiness.
            return False

    def set_always_overwrite_editor_configuration(self):
        """
        Set the configuration for always overwriting the editor configuration.
        """

        global_app_configurator.set_single_configuration("always_overwrite_editor",
                                                         self.overwrite_editor_always_checkbox.isChecked())

    def update_window_title_and_description(self):
        """
        Update the window title of the editor. The window title is determined by three factors: The current database
        connection, the corresponding saved file and the saved/unsaved status of the current text in the editor.
        """

        # Get the two different file names, the long version and the short version.
        file_name_data = self.get_corresponding_file_name_string_for_window_title_and_description()
        # Get the short name out of the tuple.
        short_file_name = file_name_data[0]
        # Get the full name ouf of the tuple.
        full_file_name = file_name_data[1]

        # Check, if the full name of the file is not an empty string.
        if full_file_name != "":
            # Format the file name for the title.
            formatted_file_name = " - {}".format(full_file_name)

        # If the full file name is an empty string, use as formatted file name the empty string.
        else:
            formatted_file_name = full_file_name

        # Create a new description title, which is the long title and add an HTML tag for a bold database connection.
        new_description_title = "<b>{}</b>{}".format(self.get_connection_status_string_for_window_title(),
                                                     formatted_file_name)

        # If the short file is not an empty string, use it for the window title.
        if short_file_name != "":
            # Use the short name with the current state as window title.
            new_window_title = "{}{}".format(short_file_name, self.get_file_save_status_string_for_window_title())

        # If the short file is an empty string, use the connection status as window title.
        else:
            new_window_title = self.get_connection_status_string_for_window_title()

        # Set the new window title.
        self.setWindowTitle(new_window_title)

        # Set the new title of the description.
        self.long_description.setText(new_description_title)

    def get_connection_status_string_for_window_title(self):
        """
        Get the current connection status as string based on the connection identifier.
        """

        # If the connection has failed, the current database connection would be False. The second case is also for a
        # failed database connection. The connection identifier needs to be checked, because the current database
        # connection and the connection identifier are initialized with None. So if the connection identifier is not
        # None, there is a try to establish a database connection.
        if self.current_database_connection is False or (self.current_database_connection is None and
                                                         self.connection_identifier is not None):

            # Set the connection status as failed, because the previous if-statement suggests a failed database
            # connection. Use the connection identifier as description for the failed connection.
            connection_status = "Connection failed: {}".format(self.connection_identifier)

        # If the current database connection is not None and not False, the connection is valid and successfully
        # established.
        elif self.current_database_connection is not False and self.current_database_connection is not None:
            # Set the connection status to the valid connection as connection identifier.
            connection_status = "{}".format(self.connection_identifier)

        # This else-branch describes the behavior for the connection status before there was even the try to establish a
        # database connection.
        else:
            # Set the connection status to an empty string.
            connection_status = ""

        # Return the result of the current connection status.
        return connection_status

    def get_corresponding_file_name_string_for_window_title_and_description(self):
        """
        Get the name of the corresponding file as string with the appropriate format for the prospective window title
        and get the title for the description.
        """

        # Check the class-wide variable for the saved file, which is initialized as None. So this branch is only
        # activated for a determined corresponding saved file.
        if self.corresponding_saved_file is not None:
            # Use the full title of the file as full name with a -.
            full_file_name = "{}".format(self.corresponding_saved_file)
            # Split the name at "/", so there are shorter parts of name.
            split_list = full_file_name.split("/")
            # Get the last item of the list as file name.
            short_file_name = split_list[len(split_list) - 1]

        # Activate the else-branch for a non-determined corresponding saved file.
        else:
            # Use an empty string for the corresponding file name.
            short_file_name = ""
            full_file_name = ""

        # Return the result of the current corresponding file name and the full name.
        return short_file_name, full_file_name

    def get_file_save_status_string_for_window_title(self):
        """
        Get the current status for a saved/(n) unsaved file: If the text has not changed after the last save point or
        after loading the file, there is nothing, which needs to be saved. If something has changed, there is an
        information in the save status.
        """

        # If the saved current editor text is not the text in the query editor, proceed.
        if self.current_editor_text != self.query_input_editor.text():
            # In this case, the current state has not been saved.
            save_status = " (*)"

        # There is nothing new to save.
        else:
            # Set the information to an empty string, because everything is saved.
            save_status = ""

        # Return the save status.
        return save_status

    def check_for_valid_connection_and_execute_query_with_shortcut(self):
        """
        Check for a valid database connection. If the connection is valid, execute the query. If the connection is
        invalid, show an error to the user. The connection is mostly invalid, if a database is not chooen.
        """

        # Check for a valid connection.
        if self.database_query_executor.is_connection_valid():
            # Submit and execute the query.
            self.execute_current_query()

        # Proceed for an invalid connection.
        else:
            # Show an error as message box to the user.
            QMessageBox.critical(self, "Connection Invalid", "The current database connection is invalid. Please choose"
                                                             " a valid database for executing a query.")

    def refresh_database_connection(self, new_connection):
        """
        Get a new database connection and set the connection as current connection. This function is used by a signal
        from the database query executor, if the current connection is invalid and a new one is established.
        """

        self.current_database_connection = new_connection

    def eventFilter(self, source, event):
        """
        Implement the function for filtering an event: This event checks for a keypress event. If the sequence of the
        keypress event matches the sequence for copy, the function for copying the current selection of the table is
        used.
        """

        # Check for the correct event type.
        if event.type() == QEvent.KeyPress and event.matches(QKeySequence.Copy):
            # Copy the current selection of the table.
            self.copy_current_table_selection()

            # Return True for a success, which is a necessary part for Qt.
            return True

        # Prevent a type error with the return of this function.
        return super(EditorWidget, self).eventFilter(source, event)

    def copy_current_table_selection(self):
        """
        Get the current selected indexes/values of the table view and copy them to the clipboard.
        """

        # Get the selected values.
        selected_values = self.table_view.selectedIndexes()

        # Proceed, if these values exist.
        if selected_values:
            # Get the index of all selected rows.
            selected_row_indexes = [index.row() for index in selected_values]
            # Sort them for further usage, so the smallest number is the first element in the list.
            selected_row_indexes.sort()

            # Get the index of all selected columns.
            selected_columns_indexes = [index.column() for index in selected_values]
            # Sort them for further usage.
            selected_columns_indexes.sort()

            # Define the string for the clipboard text.
            clipboard = ""
            # Define a row count for the start row.
            row_count = 0

            # Iterate over every selected value/index.
            for index in selected_values:
                # Get the relevant row number.
                row = index.row() - selected_row_indexes[0]

                # If the row count is not equal to the relevant row number, proceed. In this case, the current column
                # has ended and there is a new one.
                if row_count != row:
                    # Add a new line for a new column to the clipboard text.
                    clipboard += "\n"
                    # Set the row count to the current new row.
                    row_count = row

                # Get the data at the current index.
                data = index.data()
                # Add the data to the clipboard.
                clipboard += data
                # Add a tab to the clipboard, because this data cell has ended.
                clipboard += "\t"

            # Add the full text to the system clipboard.
            qApp.clipboard().setText(clipboard)

    def open_search_dialog(self):
        """
        Set the GUI components for the search dialog to (not) visible, depending on their current state.
        """

        # Set the simple search widget visible.
        self.search_replace_widget.set_widget_visible(False)
        # Check for a selected text in the editor and use it for the search field.
        self.set_current_selection_to_search_replace()

    def open_replace_dialog(self):
        """
        Open the extended search dialog/replace dialog.
        """

        # Set the widget with all components visible.
        self.search_replace_widget.set_widget_visible(True)
        # Check for a selected text in the editor and use it for the search field.
        self.set_current_selection_to_search_replace()

    def set_current_selection_to_search_replace(self):
        """
        Get the current selected text of the query input editor. If there is a selected text, use it for the first
        search and set it as text in the search line edit.
        """

        # Get the current selected text in the input editor.
        current_selected_editor_text = self.query_input_editor.selectedText()

        # Proceed for selected text.
        if current_selected_editor_text != "":
            # Set the selected text in the QLineEdit for searching.
            self.search_replace_widget.set_search_text(current_selected_editor_text)
            # Search for the current selected string.
            self.search_and_select_sub_string()

    def replace_current_selection(self):
        """
        Get the current text in the replace line edit and use the function of the query input editor for replacing the
        current search result.
        """

        # Get the text in the replace line edit as text for replacing.
        replace_text = self.search_replace_widget.get_replace_text()
        # Replace the current search result with the replace text.
        self.query_input_editor.replace(replace_text)

    def replace_all_sub_string_matches(self):
        """
        Replace all occurrences of the search result. Use the function for finding the next result. This function
        returns True, if there is still a match.
        """

        # Replace a match, if there is a search result.
        while self.query_input_editor.findNext():
            self.replace_current_selection()

        # Deactivate the replace buttons after the process for replacing all sub string matches.
        self.search_replace_widget.deactivate_replace_buttons()

    def search_and_select_sub_string(self):
        """
        Search the first occurrence of the given sub string in the search line edit and select it, which is done by the
        function findFirst.
        """

        # The text is the current text of the line edit. The expression is interpreted as regular expression and it is
        # case sensitive. It is searched for any matching text and the search wraps around the end of the text. Save the
        # result in a variable.
        match_found = self.query_input_editor.findFirst(self.search_replace_widget.get_search_text(), True, True,
                                                        False, True)

        # Activate the relevant buttons, if a match is found.
        if match_found:
            self.search_replace_widget.activate_search_next_button()

            # Check, if replace enabling is available.
            self.check_for_replace_enabling()

    def search_and_select_next_sub_string(self):
        """
        Find the next occurrence of the given sub string.
        """

        self.query_input_editor.findNext()

    def deactivate_search_next_and_replace_buttons_and_deselect(self):
        """
        Deactivate the button for searching the next item and deselect the current selection.
        """

        # Deactivate the next button.
        self.search_replace_widget.deactivate_search_next_button()

        # Deactivate the replace buttons.
        self.search_replace_widget.deactivate_replace_buttons()

        # Remove the current selection, because, for example, the text in the QLineEdit for searching has changed.
        self.query_input_editor.setSelection(0, 0, 0, 0)

    def check_for_replace_enabling(self):
        """
        Check if the replacing should be enabled. If the search input text is not empty, so there is a search, at least
        one button can be enabled. If the replace text does not contain a sub string of the search input text, replace
        all is available too.
        """

        # Get the text out of the search line edit.
        search_input_text = self.search_replace_widget.get_search_text()
        # Get the text out of the replace line edit.
        replace_line_edit_text = self.search_replace_widget.get_replace_text()

        # Check if the search input text is not empty.
        if search_input_text != "":
            # The search input text must not be in the replace text for enabling all buttons, because for the replace
            # all button, this could lead to an endless loop.
            if search_input_text not in replace_line_edit_text:
                self.search_replace_widget.activate_replace_buttons()

            # If the search input text is a sub string of the replace text, enable the button for a single replace and
            # set the one for replacing all to disabled.
            else:
                self.search_replace_widget.activate_replace_button()
                self.search_replace_widget.deactivate_replace_all_button()

        # If the search field is empty, deactivate all replace buttons.
        else:
            self.search_replace_widget.deactivate_replace_buttons()

    def close_search_replace_widget(self):
        """
        Close the search widget by setting all relevant components to invisible.
        """

        # Make the relevant widget invisible.
        self.search_replace_widget.set_widget_invisible()

    def save_command_in_history(self):
        """
        Save the current executed command in the command history.
        """

        # Define a dictionary with the relevant command data. The command itself is the query text in the input editor.
        # The check is set to False for preventing preprocessing the query and finding problems, because they are
        # currently not relevant.
        command_dictionary = {"Command": self.get_query_in_input_editor(check=False),
                              # Get the current date and time. The date is used and the current time with hours, minutes
                              # and seconds.
                              "Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                              # Get the current connection identifier as identifier.
                              "Identifier": self.connection_identifier}

        # Save the dictionary in the yaml file.
        global_command_history_store.save_command_history_in_yaml_file(command_dictionary)

    def export_and_save_csv_data(self):
        """
        Activate the export and save of the csv data.
        """

        # Get the file name with a file dialog.
        file_name = self.activate_file_dialog_for_csv_export()

        # If the file name is None, the process of saving the file has been aborted.
        if file_name is None:
            # End the function with a return.
            return

        # Save the current query result data.
        self.export_result_to_csv(file_name)

    def activate_file_dialog_for_csv_export(self):
        """
        Create a file dialog for activating the csv export.
        """

        # Get a csv file with the default name result.csv and the file type csv.
        file_dialog_with_name_and_type = QFileDialog.getSaveFileName(self, "Save File", "result", "CSV (*.csv)")

        # Get the file name.
        file_name = file_dialog_with_name_and_type[0]

        # If the file name is not an empty string, return the file name, because in this case, the user has entered one.
        if file_name != "":
            return file_name

        # Inform the user in the log about the abort.
        else:
            logging.info("The current file saving process was aborted by the user, so the current result as csv file"
                         " is not saved.")

            # Return None, because there is no file name.
            return None

    def export_result_to_csv(self, file_name):
        """
        Export the result data to csv with the file name. Get the data out of the table model.
        """

        # Open the given file in write mode.
        with open(file_name, "w") as file_to_save:
            # Get through every data row in the data list.
            for data_row in self.table_model.data_list:
                # Get through every value in the data row.
                for data_value_counter in range(len(data_row)):
                    # Write every value.
                    file_to_save.write(str(data_row[data_value_counter]))

                    # If the value is not the last one, append a comma for comma separated value.
                    if data_value_counter != len(data_row) - 1:
                        file_to_save.write(",")

                # Write a newline at the end of a data row.
                file_to_save.write("\n")

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        """
        Overwrite the close event: If the configuration for opening the previous is set and the corresponding save file
        exists, delete it from the file manager, because it does not have to be opened after a restart of the program.
        """

        if self.corresponding_saved_file is not None \
                and global_app_configurator.get_single_configuration("open_previous_files") is True:
            global_file_manager.delete_file(self.corresponding_saved_file)
            global_file_manager.commit_current_files_to_yaml()

        self.close()
