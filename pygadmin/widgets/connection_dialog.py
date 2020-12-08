import logging
import os
import keyring
import re

from PyQt5.QtGui import QKeySequence, QPixmap
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QGridLayout, QPushButton, QMessageBox, QCheckBox, QShortcut, \
    QListWidget
from PyQt5.QtCore import pyqtSignal

import pygadmin
from pygadmin.connectionstore import global_connection_store
from pygadmin.connectionfactory import global_connection_factory
from pygadmin.configurator import global_app_configurator
from pygadmin.widgets.widget_icon_adder import IconAdder


class ConnectionDialogWidget(QDialog):
    """
    Create a class for entering database parameter with a check, if they are valid or if they already exist. This is a
    master class, which can be used as template for different connection dialogs.
    """

    # Create a signal for emitting modified connection parameters.
    get_modified_connection_parameters = pyqtSignal(tuple)
    new_timeout_for_connections = pyqtSignal(bool)

    def __init__(self):
        """
        Make sub functions for initializing the widget, separated by the parts user interface, grid layout and SQL
        lexer.
        """

        super().__init__()
        # While this widget is active, all the other components are frozen and cannot be used until this widget is
        # closed again.
        self.setModal(True)
        self.service_name = "Pygadmin"
        # Add the pygadmin icon as window icon.
        icon_adder = IconAdder()
        icon_adder.add_icon_to_widget(self)

        self.init_ui()
        self.init_grid()

    def init_ui(self):
        """
        Design the user interface and its components with separated functions for every part of the interface. The order
        of initialization is related to the interaction of components with each other.
        """

        # Initialize the line edits.
        self.init_line_edit_ui()

        # Initialize the buttons.
        self.init_button_ui()

        # Initialize the label with an unknown and not tested connection.
        self.init_connection_status_label()

        # Initialize the list widget with all database connections.
        self.init_list_widget_ui()

        # Initialize the check boxes.
        self.init_checkbox_ui()

        # Adjust the size of the dialog.
        self.setMaximumSize(1260, 320)
        self.showMaximized()

        self.setWindowTitle("Modify Database Connections")

        self.show()

    def init_line_edit_ui(self):
        """
        Initialize the line edits.
        """

        # Make a list for storing the QLabels for every connection parameter. This is necessary for using the QLabel in
        # the layout setting.
        self.connection_parameter_label_list = []
        # Make a dictionary for storing the QLineEdits for every connection parameter with its name as key. This is
        # necessary for using the QLineEdit in the layout setting. The dictionary also contains the names of the
        # necessary parameters. None is chosen as value, because in the next step, the parameters will get the
        # QLineEdit as value.
        self.connection_parameter_edit_dictionary = {"Host": None,
                                                     "Username": None,
                                                     "Password": None,
                                                     "Database": None,
                                                     "Port": None
                                                     }

        # Create labels for the information about the current connection status and a check for the current connection.
        # This part must be initialized at this part, because the QLineEdits use a signal connected to these labels.
        self.test_given_connection_label = QLabel("Current Connection Status")
        # Create a label for the connection status.
        self.test_given_connection_status_label = QLabel()
        # Create a label for graphical information about the connection status.
        self.test_given_connection_status_pixmap_label = QLabel()

        for connection_parameter in self.connection_parameter_edit_dictionary.keys():
            # Make a label for a parameter.
            self.connection_parameter_label = QLabel(connection_parameter)
            # Store the parameter in the list.
            self.connection_parameter_label_list.append(self.connection_parameter_label)
            # Make a line edit for a parameter for further usage.
            self.connection_parameter_edit = QLineEdit()
            # If the text is changed, the parameters are not the checked parameters, if they were checked. A change in
            # the connection parameters leads to an unchecked connection, so the labels for the connection status are
            # changed to a state of the unknown.
            self.connection_parameter_edit.textChanged.connect(self.init_connection_status_label)
            # Store the parameter in the dictionary for further usage.
            self.connection_parameter_edit_dictionary[connection_parameter] = self.connection_parameter_edit

            # Check for the parameter for the password.
            if connection_parameter == "Password":
                # Set the QLineEdit to the password mode, so a password is not visible while writing it in the line edit
                # field.
                self.connection_parameter_edit.setEchoMode(QLineEdit.Password)

        self.change_global_timeout_label = QLabel("Set the global timeout for a query")
        self.timeout_label = QLabel("Timeout [ms]")
        self.timeout_line_edit = QLineEdit()
        self.get_current_timeout()

    def init_list_widget_ui(self):
        """
        Create the user interface for the list widget, which contains all database connections. These can be selected,
        so modifying them is possible.
        """

        self.choose_connection_label = QLabel("Please choose the database connection you want to change")

        # Make a checkbox for the order of connections in the QListWidget
        self.connection_order_checkbox = QCheckBox("Show latest connection first")
        # Define the name of the configuration.
        self.connection_order_configuration_name = "show_latest_connection_in_tree_first"
        # Load the current configuration.
        self.init_connection_order_checkbox_configuration()
        # Connect the change of the checkbox to a function, which changes the widgets order.
        self.connection_order_checkbox.stateChanged.connect(self.set_connection_to_order_in_list_widget)

        # Create a list widget as a container for all current identifier and connections.
        self.connection_parameters_list_widget = QListWidget()
        # Populate the list widget with all current connections.
        self.get_current_connections_to_list_widget()

        self.connection_parameters_list_widget.itemSelectionChanged.connect(self.insert_parameters_in_edit_fields)

        # Initialize the variables for selected connections.
        self.selected_connection_parameters_dictionary = {}
        self.selected_connection_identifier = None

    def init_button_ui(self):
        """
        Create all buttons with their connected functions and set some of them disabled.
        """

        # Create a button for testing the connection.
        self.test_given_connection_button = QPushButton("Test Connection")
        self.test_given_connection_button.clicked.connect(self.test_current_database_connection)

        # Create a button for committing the connection parameters given by the user.
        self.new_connection_button = QPushButton("Create New Connection")
        self.new_connection_button.clicked.connect(self.set_given_connection_parameters_wrapper)
        # Create a shortcut for committing the connection parameters given by the user with the usage of return.
        self.new_connection_shortcut = QShortcut(QKeySequence("Return"), self)
        self.new_connection_shortcut.activated.connect(self.set_given_connection_parameters_wrapper)

        self.save_connection_button = QPushButton("Save Selected Connection")
        self.save_connection_button.clicked.connect(self.save_connection_changes)
        self.save_connection_button.setEnabled(False)

        # Create a button to delete a connection.
        self.delete_current_connection_button = QPushButton("Delete")
        self.delete_current_connection_button.clicked.connect(self.delete_selected_connection_after_user_question)
        # Disable button, because at the start of the widget, there will not be a selected connection. This button only
        # makes sense with a selected connection.
        self.delete_current_connection_button.setEnabled(False)

        # Create a button for closing the widget.
        self.cancel_parameter_input_button = QPushButton("Close")
        self.cancel_parameter_input_button.clicked.connect(self.close)

        # Set a second function for a clicked cancel button, so the configuration is saved.
        self.cancel_parameter_input_button.clicked.connect(global_app_configurator.save_configuration_data)

        self.set_timeout_button = QPushButton("Set Timeout")
        self.set_timeout_button.clicked.connect(self.set_current_timeout)

    def init_checkbox_ui(self):
        """
        Create the different checkboxes in the application.
        """

        # Create a checkbox for the usage of the standard postgres port.
        self.use_postgres_port_checkbox = QCheckBox("Use standard postgres port")
        # Set the checkbox checked as default, so the standard postgres port is set.
        self.use_postgres_port_checkbox.setChecked(True)
        # Ensure the correct settings for a checked checkbox.
        self.set_port_edit_field_to_checkbox()
        # Define the variable for a potential overwrite, which will happen, if the checkbox is chosen. A chosen checkbox
        # is the default, so this needs to be set at the beginning.
        self.port_to_overwrite = ""
        # Connect the state change of the checkbox to a function which handle a(n un)checked checkbox.
        self.use_postgres_port_checkbox.stateChanged.connect(self.set_port_edit_field_to_checkbox)

        # Create a checkbox for the usage of the standard postgres database.
        self.use_postgres_database_checkbox = QCheckBox("Use standard postgres database")
        # Set the checkbox checked as default, so the standard database is set.
        self.use_postgres_database_checkbox.setChecked(True)
        # Activate the settings for a checked checkbox.
        self.set_database_edit_field_to_checkbox()
        # Define a variable for potential overwrite, which is overwritten, if the checkbox is checked.
        self.database_to_overwrite = ""
        # Connect the state change to a function for handling a change in the checked status of the checkbox.
        self.use_postgres_database_checkbox.stateChanged.connect(self.set_database_edit_field_to_checkbox)

        # Create a checkbox for loading all databases as a configurable parameter.
        self.load_all_databases_checkbox = QCheckBox("Load all databases")
        # Set the default as checked.
        self.load_all_databases_checkbox.setChecked(True)

        # Create a checkbox for usage in specific cases.
        self.open_at_start_checkbox = QCheckBox("Open always a connection dialog at start")

        # Define a configuration option for opening the connection dialog at the start of the application.
        self.open_at_start_configuration = "open_connection_dialog_at_start"

        # Set the default option of the box as checked, so without any changes by the user,
        self.open_at_start_checkbox.setChecked(True)

        # Connect the (un)checked change state of the checkbox to a function for setting the configuration.
        self.open_at_start_checkbox.stateChanged.connect(self.save_open_at_start_checkbox_configuration)

    def init_grid(self):
        """
        Set a grid layout to the widget and place all its components.
        """

        # Set the layout to a grid layout.
        grid_layout = QGridLayout(self)

        # Use the length of the list of parameters, because it contains all labels and so, every label is placed.
        for parameter_number in range(len(self.connection_parameter_label_list)):
            # The last parameter needs special handling caused by the placing of the checkbox for database.
            if parameter_number != 4:
                # Place every QLabel on the grid layout with an of by one, because in sub class, there can be a widget.
                grid_layout.addWidget(self.connection_parameter_label_list[parameter_number], parameter_number + 1, 2)

            # This case happens for the label of the port.
            else:
                # The label is placed further down, so the checkboxes for the database are placed accurate.
                grid_layout.addWidget(self.connection_parameter_label_list[parameter_number], parameter_number + 3, 2)

        # Use an incrementer for the next for loop.
        connection_parameter_edit_incrementer = 1

        # Use the connection parameters key and their related values. The values are QLineEdits and they are placed.
        for connection_parameter, connection_parameter_edit in self.connection_parameter_edit_dictionary.items():
            # Place every QLineEdit on the grid layout.
            grid_layout.addWidget(connection_parameter_edit, connection_parameter_edit_incrementer, 3)
            # Increment the incrementer, so the following QLineEdit is placed below the one before.
            connection_parameter_edit_incrementer += 1

            # Check for the special database case.
            if connection_parameter == "Database":
                # Place the checkbox under the QLineEdit for the database.
                grid_layout.addWidget(self.use_postgres_database_checkbox, connection_parameter_edit_incrementer, 3)
                grid_layout.addWidget(self.load_all_databases_checkbox, connection_parameter_edit_incrementer + 1, 3)
                connection_parameter_edit_incrementer += 2

        # The port as the parameter which belongs to this checkbox is the last one in the list for the user, so this
        # checkbox is placed below the QLineEdit for the port.
        grid_layout.addWidget(self.use_postgres_port_checkbox, connection_parameter_edit_incrementer + 1, 3)

        # Place the button for canceling the input.
        grid_layout.addWidget(self.cancel_parameter_input_button, connection_parameter_edit_incrementer + 4, 4)

        # Place the button for committing the connection parameters below the QLineEdits.
        grid_layout.addWidget(self.new_connection_button, connection_parameter_edit_incrementer + 4, 3)

        grid_layout.addWidget(self.change_global_timeout_label, 1, 4)
        grid_layout.addWidget(self.timeout_label, 3, 4)
        grid_layout.addWidget(self.timeout_line_edit, 4, 4)
        grid_layout.addWidget(self.set_timeout_button, 5, 4)

        # Place the components for a connection check. The first label and the button are two grids wide, so the
        # information in the QLabels with the text and the pixmap can be placed in two grid, which look like one.
        grid_layout.addWidget(self.test_given_connection_label, 3, 5, 1, 2)
        grid_layout.addWidget(self.test_given_connection_status_pixmap_label, 4, 6)
        grid_layout.addWidget(self.test_given_connection_status_label, 4, 5)
        grid_layout.addWidget(self.test_given_connection_button, 5, 5, 1, 2)

        # Place the relevant parts for the list widget and the related buttons.
        grid_layout.addWidget(self.choose_connection_label, 1, 0)
        grid_layout.addWidget(self.connection_parameters_list_widget, 2, 0, 5, 1)
        grid_layout.addWidget(self.connection_order_checkbox, connection_parameter_edit_incrementer + 1, 0)
        grid_layout.addWidget(self.delete_current_connection_button, connection_parameter_edit_incrementer + 4, 2)
        grid_layout.addWidget(self.save_connection_button, connection_parameter_edit_incrementer + 4, 0)

        # Place checkbox with in relation to the connection incrementer.
        grid_layout.addWidget(self.open_at_start_checkbox, connection_parameter_edit_incrementer + 3, 3, 1, 2)

        grid_layout.setSpacing(10)
        self.setLayout(grid_layout)

    def init_connection_status_label(self):
        """
        Design the connection status label content for the first time. They show, if a connection is tested or not. If
        a connection is untested, the labels say so.
        """

        # Set the text label to an untested connection.
        self.test_given_connection_status_label.setText("Not tested yet")
        # Get the relevant connection icon.
        server_status_pixmap_path = os.path.join(os.path.dirname(pygadmin.__file__), "icons", "server_pending.svg")
        # Add pixmap icon with the function to the QLabel.
        self.add_server_pixmap(server_status_pixmap_path)

        # Define the existence of empty line edits as False.
        existence_of_empty_line_edits = False

        # Check the line edit fields in the dictionary, if they are really not empty.
        for line_edit_key, line_edit_field in self.connection_parameter_edit_dictionary.items():
            # Check for an empty field. An empty field is irrelevant for the parameter password, because a database
            # connection can exists without a password.
            if line_edit_field.text() == "" and line_edit_key != "Password":
                # Change the existence of empty fields to True for further usage.
                existence_of_empty_line_edits = True

        # Check, if there are empty line edit fields.
        if existence_of_empty_line_edits is True:
            # Set the button for testing connections disabled, so a connection with empty parameters can not be tested,
            # because the test would lead to an invalid connection.
            self.test_given_connection_button.setEnabled(False)

        # This else branch is for edit fields, which are not empty-
        else:
            # Enable the button for testing a connection,
            self.test_given_connection_button.setEnabled(True)

    def add_server_pixmap(self, pixmap_path):
        """
        Add the pixmap at the given path, if existing, to the QLabel for a pixmap.
        """

        # If the path exists, use the pixmap there.
        if os.path.exists(pixmap_path):
            # Create a QPixmap.
            server_icon = QPixmap(pixmap_path)
            # Set the pixmap to the related label.
            self.test_given_connection_status_pixmap_label.setPixmap(server_icon)

        else:
            logging.warning("Icons were not found for the server status with path {}.".format(pixmap_path))

    def set_port_edit_field_to_checkbox(self):
        """
        Get the current status of the checkbox for the usage of the standard postgres port. If it is checked, save the
        current port and then use the standard postgres port 5432. If not, set the port to the previous port.
        """

        # Check for a checked checkbox.
        if self.use_postgres_port_checkbox.isChecked() is True:
            # Save the current port, because this field could contain a value.
            self.port_to_overwrite = self.connection_parameter_edit_dictionary["Port"].text()
            # Set the port to the postgres standard port 5432.
            self.connection_parameter_edit_dictionary["Port"].setText("5432")

        # Use this branch for an unchecked box.
        else:
            # Set the text to the previous database.
            self.connection_parameter_edit_dictionary["Port"].setText(self.port_to_overwrite)

    def set_database_edit_field_to_checkbox(self):
        """
        Get the current status of the checkbox for the usage of the standard postgres database. If it is checked, save
        the current database and then use the standard postgres database. If not, set the database to the previous
        database.
        """

        # Check for a checked checkbox.
        if self.use_postgres_database_checkbox.isChecked() is True:
            # Save the current database.
            self.database_to_overwrite = self.connection_parameter_edit_dictionary["Database"].text()
            # Set the database to the standard postgres database.
            self.connection_parameter_edit_dictionary["Database"].setText("postgres")

        # Use this branch for an unchecked box.
        else:
            # Set the text to the previous database.
            self.connection_parameter_edit_dictionary["Database"].setText(self.database_to_overwrite)

    def set_given_connection_parameters_wrapper(self):
        """
        Use a wrapper function, which is used by the button and shortcut for committing the connection details. This
        wrapper function can be overwritten by child classes instead of causing an overflow by an overwritten signal,
        which could happen and is extremely unpleasant.
        """

        self.commit_new_parameters_to_yaml()

        global_app_configurator.save_configuration_data()

    def get_given_connection_parameters(self):
        """
        Check the current values in the QLineEdit and if they are valid, return these database connection parameters, so
        a function for committing the data can be used.
        """

        # Create a connection identifier with the stored values in the dictionary for further usage like saving in the
        # password manager or communication to the user for an error case or committing success.
        connection_identifier = "{}@{}:{}/{}".format(self.connection_parameter_edit_dictionary["Username"].text(),
                                                     self.connection_parameter_edit_dictionary["Host"].text(),
                                                     self.connection_parameter_edit_dictionary["Port"].text(),
                                                     self.connection_parameter_edit_dictionary["Database"].text())

        # Define one log message and recycle it later for every error in this function.
        commit_error_message_log = "The following connection parameters were not saved after the try to commit them, " \
                                   "because"

        # Get the result for an empty parameter in the edit fields.
        empty_parameter_result = self.check_for_empty_parameter_edit_fields()

        # If there are empty parameters, the empty parameter result is not False. Normally, it is a list with a boolean
        # for identifying the kind of error and information for showing to the user.
        if empty_parameter_result is not False:
            # Prepare a warning message for the log.
            empty_field_logging_warning = "{} one (or more than one) field was empty: {}".format(
                commit_error_message_log, connection_identifier)

            # If the first element of the list is True, essential parameters for a database connection are empty.
            if empty_parameter_result[0] is True:
                # Show the warning to the user in a message box.
                QMessageBox.critical(self, empty_parameter_result[1], empty_parameter_result[2])
                logging.warning(empty_field_logging_warning)

                return

            # If the first element of the list is None, a question to the user is necessary for the following procedure.
            elif empty_parameter_result[0] is None:
                # Ask the user for proceeding without a password.
                proceed_without_password = QMessageBox.question(self, empty_parameter_result[1],
                                                                empty_parameter_result[2])

                # If the answer is no, then the user does not want to proceed without an empty password and gets the
                # chance to enter one.
                if proceed_without_password == QMessageBox.No:
                    logging.warning(empty_field_logging_warning)

                    return

        # Check for a valid port.
        if self.check_for_valid_port() is False:
            # Create a title and a description for a potential error, which can be used in two cases.
            port_input_error_title = "Invalid input for port"
            port_input_error_description = "The given port number is invalid. Please enter an integer number " \
                                           "between 0 and 65535 for your port."

            QMessageBox.critical(self, port_input_error_title, port_input_error_description)

            # Create a warning in the log, that the current connection cannot be saved with the given identifier.
            logging.warning("{} the port is invalid: {}".format(commit_error_message_log, connection_identifier))

            return

        # Check for a changed password. If the password changed, this value is True.
        changed_password = self.check_for_changed_password(connection_identifier)

        # If there is a changed password, set it.
        if changed_password is True:
            # Try to save the password in the password manager.
            if self.set_password_with_its_identifier(connection_identifier) is False:
                logging.warning("{} an error occurred while saving the password: {}".format(commit_error_message_log,
                                                                                            connection_identifier))

                return

        # Define the parameters in a dictionary which is required by the connection store.
        connection_parameters = {"Host": self.connection_parameter_edit_dictionary["Host"].text(),
                                 "Username": self.connection_parameter_edit_dictionary["Username"].text(),
                                 "Database": self.connection_parameter_edit_dictionary["Database"].text(),
                                 # The port is used as integer number, not as string.
                                 "Port": int(self.connection_parameter_edit_dictionary["Port"].text()),
                                 # Get the status for loading all databases out of the checkbox.
                                 "Load All": self.load_all_databases_checkbox.isChecked()
                                 }

        return connection_parameters, connection_identifier, changed_password

    def commit_new_parameters_to_yaml(self):
        """
        This function is called for a commit of new connection parameters. The current given connection parameters are
        used, if they are valid.
        """

        # Get the current connection parameters.
        connection_information = self.get_given_connection_parameters()

        # If the current parameters are not None, all parameters are valid. There is an error message from the function
        # for getting the connection parameters, if not.
        if connection_information is not None:
            # Get the separate values of the tuple.
            connection_parameters = connection_information[0]
            connection_identifier = connection_information[1]

            # Use the function for committing the parameter to the .yaml file.
            commit_parameters_yaml = global_connection_store.save_connection_parameters_in_yaml_file(
                connection_parameters)

            # Check for the success of the commit of the parameters.
            if commit_parameters_yaml is True:
                # Inform the user about the success.
                QMessageBox.information(self, "Commit Success", "The connection parameters for {} were committed "
                                                                "successfully.".format(connection_identifier))

                self.update_connection_information()

            # Explain the situation to the user.
            elif commit_parameters_yaml is False:
                QMessageBox.warning(self, "Commit Fail",
                                    "The connection parameters for {} could not be committed, because"
                                    " this connection has been committed with the parameters for "
                                    "host, port and user before. The database is irrelevant, "
                                    "because "
                                    "it is used as entry point and all the other databases for this "
                                    "host, port and user are accessible with one database as entry "
                                    "point.".format(connection_identifier))

    def check_for_empty_parameter_edit_fields(self):
        """
        Get the current text in the QLineEdits and check, if they are empty. If they are, show this as error to the
        user, except for an empty password field. The password field is allowed to be empty, because database
        connections without a password can exist.
        """

        # Get all items of the dictionary, which stores the name of a parameter and the corresponding QLineEdit
        for edit_field_name, edit_qt_object in self.connection_parameter_edit_dictionary.items():
            # Check for every parameter except password if it contains an empty string.
            if edit_field_name != "Password" and edit_qt_object.text() == "":
                # Create a title for an error.
                empty_field_title = "Empty field for parameter {}".format(edit_field_name)
                # Create a description of the error.
                empty_field_description = "The field for the parameter {} is empty. Please enter a value.".format(
                    edit_field_name)

                return [True, empty_field_title, empty_field_description]

        # An empty password field describes a corner case, because database connections without a password can be valid.
        if self.connection_parameter_edit_dictionary["Password"].text() == "":
            # Create a title for the information about an empty password.
            password_empty_title = "No password supplied"
            # Create a description for the information about an empty password, which implies a question.
            password_empty_description = "The field for the parameter password is empty. Do you want to proceed with " \
                                         "a database connection without a password?"

            return [None, password_empty_title, password_empty_description]

        return False

    def check_for_valid_port(self):
        """
        Check for a valid port number as an integer variable. A port can be an integer number between 0 and 65535.
        """

        # Try to initiate a check for a valid port.
        try:
            # Try a type convert for the current text in the QLineEdit for the port.
            port_in_integer = int(self.connection_parameter_edit_dictionary["Port"].text())
            # A valid port number is between 0 and 65535
            if 0 <= port_in_integer <= 65535:
                return True

            else:
                return False

        # A ValueError can occur, if the current input for port in the QLineEdit is not a(n integer) number.
        except ValueError:
            return False

    def check_for_changed_password(self, database_connection_identifier):
        """
        Check for a change in password.
        """

        # Get a password identifier based on the connection identifier.
        password_identifier = database_connection_identifier.split("/")[0]

        # Check, if the password in the keyring is identical to the given password, so an extra dialog is not necessary.
        if keyring.get_password(self.service_name, password_identifier) \
                == self.connection_parameter_edit_dictionary["Password"].text():
            return False

        else:
            return True

    def set_password_with_its_identifier(self, database_connection_identifier):
        """
        Save the given password in the password manager of the operating system based on its identifier, which contains
        the name of the user, server, port and database, so a clear identification is possible. Check also for an
        already existing password.
        """

        # Use the password identifier, which is used for the keyring and password storage.
        password_identifier = database_connection_identifier.split("/")[0]

        if keyring.get_password(self.service_name, password_identifier) is not None:
            overwrite_existing_password_title = "Overwrite existing password"
            overwrite_existing_password_description = "Do you want to overwrite the already existing password for " \
                                                      "the database connection with the identifier " \
                                                      "{}?".format(database_connection_identifier)

            overwrite_existing_password = QMessageBox.question(self, overwrite_existing_password_title,
                                                               overwrite_existing_password_description)

            if overwrite_existing_password == QMessageBox.No:
                return False

        try:
            keyring.set_password(self.service_name, password_identifier,
                                 self.connection_parameter_edit_dictionary["Password"].text())

            return True

        except Exception as keyring_error:
            logging.critical("An error occurred during the process of saving the password for {} in the password "
                             "manager: {}".format(database_connection_identifier, keyring_error), exc_info=True)

            return False

    def update_connection_information(self, change_information="new", position=None):
        """
        Update the connection information with the custom signal of the class. There is the default change information
        with the information and the position of a new connection. This is used in the tree model for updating the
        connections. The list widget must also be updated.
        """

        # Emit the signal with information about modified parameters.
        self.get_modified_connection_parameters.emit((self.selected_connection_parameters_dictionary,
                                                      change_information, position))

        # Update the list widget and use the change information to specify the update.
        self.update_list_widget_to_changes(change_information)

    def update_list_widget_to_changes(self, change_information):
        """
        Update the list widget to the changes. The variable change information contains the type of change. A corner
        case for the change information is the information "change", because with this parameter, the connection has
        been updated. The connection for an update ist normally selected and in the next step, it is changed. This
        function ensures the selection of the previous identifier, so the freshly changed connection needs to be found.
        """

        # Check the change type for "change".
        if change_information == "change":
            # Get the old list of connection identifiers for further usage, which is only necessary for the information
            # about "change".
            old_item_list = self.get_all_item_texts_in_list_widget()

        # Get the new and updated content to the list widget.
        self.get_current_connections_to_list_widget()

        # If the selected connection identifier is not None, there was a selected item in the previous list.
        if self.selected_connection_identifier is not None:
            # Use the function for finding the occurrence of the previous selected item (stored in the selected
            # connection identifier). If there is a match, this match is selected and returned.
            identifier_in_list_widget = self.find_occurrence_in_list_widget_and_select_item(
                self.selected_connection_identifier)

            # If the corner case "change" is relevant and the previous selection cannot be found, this previous
            # selection may have changed. This can also happen for "delete", but after a deletion, there is no need to
            # select the previous item.
            if change_information == "change" and identifier_in_list_widget is None:
                # Get a list of all new items.
                new_item_list = self.get_all_item_texts_in_list_widget()
                # Use a set to find the one difference in the old list and the new list. This statement finds the one
                # item, which is part of new item list and not of old item list. This is the changed item. This item is
                # stored in a list instead of a set object.
                item_to_select_in_list = list(set(new_item_list) - set(old_item_list))
                # Use the function for finding a occurrence again, but this time with the different item, which is the
                # changed previous item.
                self.find_occurrence_in_list_widget_and_select_item(item_to_select_in_list[0])

    def find_occurrence_in_list_widget_and_select_item(self, selection_identifier):
        """
        Find the occurrence of a given identifier in the list widget and the select this identifier. Return the
        identifier for possible further usage.
        """

        # Check every item in the list widget based on a for loop for the index.
        for list_widget_item_range in range(self.connection_parameters_list_widget.count()):
            # Get the item at the given index/range.
            list_widget_item = self.connection_parameters_list_widget.item(list_widget_item_range)

            # If the text of the list widget as connection identifier is identical with the given identifier of a
            # current selection, select the item in the list widget.
            if list_widget_item.text() == selection_identifier:
                # Select the item in the list widget.
                list_widget_item.setSelected(True)

                # Return the item for possible further usage.
                return list_widget_item

    def get_all_item_texts_in_list_widget(self):
        """
        Get a list of all item texts in the list widget. These texts are the connection identifiers.
        """

        # Define the list.
        list_widget_item_list = []
        # The count of the list widget is the number of items in this widget, so every item is checked.
        for list_widget_item_range in range(self.connection_parameters_list_widget.count()):
            # Append the text of every item to the list.
            list_widget_item_list.append(self.connection_parameters_list_widget.item(list_widget_item_range).text())

        # Return the freshly filled list.
        return list_widget_item_list

    def test_current_database_connection(self):
        """
        Test the currently available parameters in the QLineEdits and adjust the QLabels, which show the user feedback
        about the connection and the ability to establish a database connection.
        """

        # Get the current text of the QLineEdits and assign them to their purpose.
        host = self.connection_parameter_edit_dictionary["Host"].text()
        user = self.connection_parameter_edit_dictionary["Username"].text()
        database = self.connection_parameter_edit_dictionary["Database"].text()
        password = self.connection_parameter_edit_dictionary["Password"].text()
        port = self.connection_parameter_edit_dictionary["Port"].text()

        # Use the function of the global connection factory to test the connection parameters.
        if global_connection_factory.test_parameters_for_database_connection(host, user, database, password, port) \
                is True:
            # If there is a connection, use variables for further adapting of the layout.
            connection_status_result = "Connection Valid"
            server_status_pixmap_path = os.path.join(os.path.dirname(pygadmin.__file__), "icons",
                                                     "server_valid.svg")

        else:
            # If there is not a connection, use variables for further adapting of the layout.
            connection_status_result = "Connection Invalid"
            server_status_pixmap_path = os.path.join(os.path.dirname(pygadmin.__file__), "icons",
                                                     "server_invalid.svg")

        # Set the text and the pixmap of the QLabels. Their text and picture is based on the results of the connection
        # test.
        self.test_given_connection_status_label.setText(connection_status_result)
        self.add_server_pixmap(server_status_pixmap_path)

    def save_open_at_start_checkbox_configuration(self):
        """
        Save the current configuration of the open at start checkbox in the dictionary of the global configurator.
        """

        global_app_configurator.set_single_configuration(self.open_at_start_configuration,
                                                         self.open_at_start_checkbox.isChecked())

    def init_connection_order_checkbox_configuration(self):
        """
        Load the current configuration of the checkbox for the order of connections in the list widget out of the .yaml
        file for configuration.
        """

        # Get the current configuration, which could also be None for a non-existing configuration.
        current_configuration = global_app_configurator.get_single_configuration(
            self.connection_order_configuration_name)

        # If the configuration is not False, which could be True or None, proceed.
        if current_configuration is not False:
            # Set the checkbox to checked.
            self.connection_order_checkbox.setChecked(True)

        else:
            # Do not set the checkbox to checked.
            self.connection_order_checkbox.setChecked(False)

    def set_connection_to_order_in_list_widget(self):
        """
        Update the order of the connections in the list widget. First of all, clear the current list widget, so it is
        nothing in there. After that, load the current connections in the list widget. Use the identifier of the
        selected connection, which has not changed since the last selection, to find this connection in the new order
        of the list widget and set the selection to this connection. After that, save the configuration of the checkbox
        to the configuration file.
        """

        # Purge all current items of the list widget.
        self.connection_parameters_list_widget.clear()

        # Load the items/connection to the list widget.
        self.get_current_connections_to_list_widget()

        # Iterate over every element of the list widget.
        for count in range(self.connection_parameters_list_widget.count()):
            # Check the item at every count (and so every item in the list widget) for its text. If the text is
            # identical to the previous selection identifier, it is a match.
            if self.selected_connection_identifier == self.connection_parameters_list_widget.item(count).text():
                # Set the selection back to the previous selected item, which is now at another place in the list
                # widget.
                self.connection_parameters_list_widget.setCurrentRow(count)

        # Save the configuration of the checkbox.
        self.set_connection_order_checkbox_configuration()

    def get_current_connections_to_list_widget(self):
        """
        Get all current connections out of the .yaml file with its identifier to the list widget, so the user can select
        them.
        """

        # Clear all current parameters, so nothing will stop a potential (re)population of the widget.
        self.connection_parameters_list_widget.clear()

        # Load all current connections out of the .yaml file, which is administrated by the global connection store.
        connection_parameter_list = global_connection_store.get_connection_parameters_from_yaml_file()

        # The list widget requires an index for inserting items. This variable is used for incrementation in a for loop.
        connection_number_count = 0

        # Check for the current status of the checkbox for the order of the connections in the list widget.
        if self.connection_order_checkbox.isChecked():
            # If the checkbox is checked, reverse the list. The connection list is in its original order from the oldest
            # connection to the newest. After the list is reversed, the first item is the newest connection.
            connection_parameter_list = reversed(connection_parameter_list)

        else:
            # Sort the list with the host as criteria alphabetically.
            connection_parameter_list = sorted(connection_parameter_list, key=lambda k: k["Host"])

        # Create for all parameters a connection identifier.
        for connection_parameter in connection_parameter_list:
            connection_identifier = "{}@{}:{}/{}".format(connection_parameter["Username"],
                                                         connection_parameter["Host"],
                                                         connection_parameter["Port"],
                                                         connection_parameter["Database"])

            # Add the identifier with its index to the list widget.
            self.connection_parameters_list_widget.insertItem(connection_number_count, connection_identifier)
            # Increment the index for the next loop, so the next item is inserted under the previous item.
            connection_number_count += 1

    def set_connection_order_checkbox_configuration(self):
        """
        Save the current configuration of the checkbox for the order of the connections in the list widget. First, set
        the configuration in the global configurator and then, save the data in the .yaml file for configuration.
        """

        # Set the configuration with its name and the current status of the checkbox. If the status ist checked, this
        # value is True. If not, it is False.
        global_app_configurator.set_single_configuration(self.connection_order_configuration_name,
                                                         self.connection_order_checkbox.isChecked())

        # Save the configuration in the .yaml file for configuration.
        global_app_configurator.save_configuration_data()

    def insert_parameters_in_edit_fields(self):
        """
        Insert the parameters of the selected connections to the QLineEdit fields and make commits possible with the
        activation of the required button and shortcut.
        """

        # Get the selected connection with its parameters.
        if self.get_selected_connection():
            # Set all parameters of the dictionary to the related fields in the QLineEdit.
            self.connection_parameter_edit_dictionary["Host"].setText(
                self.selected_connection_parameters_dictionary["Host"])
            self.connection_parameter_edit_dictionary["Username"].setText(
                self.selected_connection_parameters_dictionary["Username"])
            self.connection_parameter_edit_dictionary["Database"].setText(
                self.selected_connection_parameters_dictionary["Database"])
            self.connection_parameter_edit_dictionary["Port"].setText(
                # Use the port as string, because all elements of the QLineEdit have to be strings.
                str(self.selected_connection_parameters_dictionary["Port"]))

            # Get the status for loading all databases for the selected connection.
            load_all_databases = global_connection_store.get_connection_load_all_information(
                self.selected_connection_parameters_dictionary["Host"],
                self.selected_connection_parameters_dictionary["Database"],
                self.selected_connection_parameters_dictionary["Port"],
                self.selected_connection_parameters_dictionary["Username"]
            )

            # Set the status as status of the checkbox.
            self.load_all_databases_checkbox.setChecked(load_all_databases)
            # Save the status in the dictionary for the selected connection.
            self.selected_connection_parameters_dictionary["Load All"] = load_all_databases

            # Define a password identifier for recognition in the password manager and keyring.
            password_identifier = self.selected_connection_identifier.split("/")[0]
            # Set the password as text in the QLineEdit. This is not a security flaw, because it is protected by the
            # user's master password and the password mode of the QLineEdit.
            self.connection_parameter_edit_dictionary["Password"].setText(
                keyring.get_password(self.service_name, password_identifier))

            # Enable the button for saving, because now, a item is selected.
            self.save_connection_button.setEnabled(True)
            # Enable the button for deleting a connection.
            self.delete_current_connection_button.setEnabled(True)

        else:
            self.new_connection_button.setEnabled(True)
            self.new_connection_shortcut.setEnabled(True)
            self.save_connection_button.setEnabled(False)
            self.delete_current_connection_button.setEnabled(False)

    def get_selected_connection(self):
        """
        Check for a selected item and if there is one, use the current selected connection identifier and build a
        dictionary with the connection parameters out of it. Return the success as boolean.
        """

        # Check for a selected connection.
        if self.connection_parameters_list_widget.selectedItems():
            # Use the list of selected items. This list contains one item and the text of this item is the current
            # selected connection identifier.
            self.selected_connection_identifier = self.connection_parameters_list_widget.selectedItems()[0].text()

            # Create a list of parameters with splitting at the different characters to get the single parameter.
            parameter_list = [parameter.strip() for parameter in re.split("[@:/]",
                                                                          self.selected_connection_identifier)]

            # Save the parameters in a dictionary. The position in the list is determined by the structure of the
            # connection identifier and can be used for this relation.
            self.selected_connection_parameters_dictionary = {"Host": parameter_list[1],
                                                              "Username": parameter_list[0],
                                                              "Database": parameter_list[3],
                                                              "Port": int(parameter_list[2])}

            # Return the success with True.
            return True

        # The else branch is used for an empty list of currently selected item, so there is not a selected item.
        else:
            # Return a missing selected connection with false.
            return False

    def delete_selected_connection_after_user_question(self):
        """
        Deleting the current selected connection after asking the user for consent. The idea is, to use this function
        with a delete button. Such a button could be clicked accidentally, so there is a question for the user, if they
        really want to delete the connection.
        """

        # Ask the user with a message box and use the text of the currently selected item to show the user, which
        # connection data will be deleted. A check for a(n un)selected connection is not necessary, because this
        # function is only called with the button for deleting connections.
        really_delete_connection = QMessageBox.question(self, "Delete Connection", " Do you really want to delete the "
                                                                                   "currently selected connection "
                                                                                   "{}?".format(
            self.connection_parameters_list_widget.selectedItems()[
                0].text()),
                                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        # If the user wants to delete the connection, delete the connection.
        if really_delete_connection == QMessageBox.Yes:
            if self.delete_selected_connection() is True:
                self.update_connection_information(change_information="delete")

    def delete_selected_connection(self):
        """
        Delete the current selected connection. The parameters of the current selected connection are stored in a
        class-wide dictionary, so this connection can be deleted in the .yaml file. The password needs to be deleted
        too, so keyring is used for this operation.
        """

        # Use the connection store to delete the connection based on the class-wide parameter dictionary.
        global_connection_store.delete_connection(self.selected_connection_parameters_dictionary)

        # Use a try except statement to delete the password in the keyring, because some errors (for a non existing user
        # for example) need to be caught.
        try:
            # Get the password identifier. The database is not part of it, so there is a split.
            password_identifier = self.selected_connection_identifier.split("/")[0]
            # Delete the password with keyring.
            keyring.delete_password(self.service_name, password_identifier)

            # Return True for a success.
            return True

        except Exception as password_error:
            logging.error("During the deletion of the password for {}, the following error occurred: "
                          "{}".format(self.selected_connection_identifier, password_error), exc_info=True)

    def save_connection_changes(self):
        """
        Save the new connection data.
        """

        # Get the current connection information.
        connection_information = self.get_given_connection_parameters()

        # Proceed, if the current connection information is not None. This variable can be None for errors during the
        # validation process.
        if connection_information is not None:
            # Get the connection parameters and the connection identifier out of the tuple.
            connection_parameters = connection_information[0]
            connection_identifier = connection_information[1]
            password_changed = connection_information[2]

            # Initiate a change of connection and if it was successful, proceed with the if branch.
            if global_connection_store.change_connection(self.selected_connection_parameters_dictionary,
                                                         connection_parameters, password_change=password_changed):

                # Inform the user about the successful commit.
                QMessageBox.information(self, "Commit Success", "The changed connection parameters for {} were "
                                                                "committed successfully.".format(connection_identifier))

                # Get the index of the new connection parameters out of the connection store to use the index in the
                # function for accepting the dialog.
                index_of_new_connection = global_connection_store.get_index_of_connection(connection_parameters)

                # Use the information for a change and the index of the connection as position.
                self.update_connection_information(change_information="change", position=index_of_new_connection)

            else:
                QMessageBox.warning(self, "Commit Fail",
                                    "The changed connection parameters for {} could not be committed, because"
                                    " this connection has been committed with the parameters for "
                                    "host, port and user before. The database is irrelevant, "
                                    "because it is used as entry point and all the other databases for this "
                                    "host, port and user are accessible with one database as entry "
                                    "point.".format(connection_identifier))

    def get_current_timeout(self):
        """
        Get the current timeout time out of the app configurator.
        """

        # Get the configuration.
        current_timeout = global_app_configurator.get_single_configuration("Timeout")

        # If the configuration is not None, set it as text in the line edit.
        if current_timeout is not None:
            self.timeout_line_edit.setText(str(current_timeout))

    def set_current_timeout(self):
        """
        Set the current value in timeout as global timeout value after a check and inform the user about the result.
        """

        # Check for a valid value. If the value is invalid, end the function with a return.
        if self.check_for_valid_timeout() is False:
            # Create a title and a description for an error.
            timeout_input_error_title = "Invalid input for timeout"
            timeout_input_error_description = "The given timeout number is invalid. Please enter an integer number " \
                                              "larger than 0."
            # Show the error to the user in a message box.
            QMessageBox.critical(self, timeout_input_error_title, timeout_input_error_description)

            return

        # Set the timeout time as integer.
        global_app_configurator.set_single_configuration("Timeout", int(self.timeout_line_edit.text()))
        # Save the current configuration.
        global_app_configurator.save_configuration_data()

        self.new_timeout_for_connections.emit(True)

        # Inform the user about the success.
        QMessageBox.information(self, "Timeout set", "The new timeout value is set successfully.")

    def check_for_valid_timeout(self):
        """
        Check for a valid timeout number as an integer variable. A timeout needs to be larger than 0.
        """

        # Try to initiate a check for a valid timeout.
        try:
            # Try a type convert for the current text in the QLineEdit for the port.
            timeout_in_integer = int(self.timeout_line_edit.text())
            # A valid timeout is larger than 0.
            if timeout_in_integer > 0:
                return True

            else:
                return False

        # A ValueError can occur, if the current input for timeout in the QLineEdit is not a(n integer) number.
        except ValueError:
            return False
