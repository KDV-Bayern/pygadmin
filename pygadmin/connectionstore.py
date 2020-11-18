import copy
import logging
import os

import yaml


class ConnectionStore:
    """
    Create a class for administration of database connection parameters, which are stored in a .yaml file. It is
    necessary to save connections after the runtime of the program, so connections can be established without entering
    them every time the application starts.
    """

    def __init__(self):
        # Define a path for the configuration files.
        configuration_path = os.path.join(os.path.expanduser("~"), '.pygadmin')

        # If the path for the configuration files does not exist, create it.
        if not os.path.exists(configuration_path):
            os.mkdir(configuration_path)

        # Define the yaml file, which stores the database connection parameters, so it is independent from the user's
        # operating system.
        self.yaml_connection_parameters_file = os.path.join(configuration_path, "connection_parameters.yaml")
        # Create a container list for the data of connection_parameters.yaml and the data, which is going to be dumped
        # in the file.
        self.connection_parameters_yaml = []

        # Check for the existence of the file.
        if not os.path.exists(self.yaml_connection_parameters_file):
            # Create the file as an empty file for writing in it.
            open(self.yaml_connection_parameters_file, "a")

    def get_connection_parameters_from_yaml_file(self):
        """
        Read all the different connection parameters from a .yaml file and store them in a list for further usage.
        """

        # Use a try statement in case of a broken .yaml file.
        try:
            # Use the read mode for getting the content of the file.
            with open(self.yaml_connection_parameters_file, "r") as connection_data:
                # Use the function for a safe load, because the file can be edited manually.
                self.connection_parameters_yaml = yaml.safe_load(connection_data)

                # If the list for the connections parameters out of the .yaml file is empty, it is None after a load.
                # But for preventing further errors, this if branch is used.
                if self.connection_parameters_yaml is None:
                    # Set the connection parameters to an empty list.
                    self.connection_parameters_yaml = []

                # Return a copy of the connection parameters list, so there is no manipulation from the outside.
                return copy.copy(self.connection_parameters_yaml)

        except Exception as file_error:
            logging.error("The file {} cannot be opened and database connection parameter cannot be loaded with the "
                          "following error: {}".format(self.yaml_connection_parameters_file, file_error), exc_info=True)

    def save_connection_parameters_in_yaml_file(self, connection_parameter_dictionary):
        """
        Save given connection parameters in a dictionary in the .yaml file for all connection parameters after a check
        for a duplicate. A dictionary instead of a connection identifier is chosen, because it is more readable end
        editable for a human.
        """

        # Ensure the load of all the current connection parameters, so a later dump in connection_parameters.yaml
        # contains all parameters and none is lost.
        self.get_connection_parameters_from_yaml_file()

        # The list of dictionaries for is None, if the .yaml file is empty and does not contain any connections.
        if self.connection_parameters_yaml is None:
            # Set the storage variable for the connection parameter to an empty list for appending later.
            self.connection_parameters_yaml = []

        if self.check_for_correct_keys_in_dictionary(connection_parameter_dictionary) is False:
            return False

        # Use the function to check for a duplicate, which returns True, if the connection already exists.
        if self.check_parameter_for_duplicate(connection_parameter_dictionary) is True:
            logging.warning("The given parameter already exists in {}.".format(self.yaml_connection_parameters_file))
            # End the current function, because saving the connection parameters is not necessary at this point.
            return False

        # Append the given connection parameters in a dictionary to the list of all connection parameters.
        self.connection_parameters_yaml.append(connection_parameter_dictionary)

        return self.commit_current_list_to_yaml()

    def commit_current_list_to_yaml(self):
        """
        Save the current list with its changes in the .yaml file.
        """

        try:
            # Open the .yaml file in writing mode for dumping the data.
            with open(self.yaml_connection_parameters_file, "w") as connection_data:
                yaml.safe_dump(self.connection_parameters_yaml, connection_data)

                # Report the success.
                return True

        except Exception as file_error:
            logging.error("The file {} cannot be opened and database connection parameter cannot be saved with the "
                          "following error: {}".format(self.yaml_connection_parameters_file, file_error))

    def check_parameter_for_duplicate(self, connection_parameter_dictionary_for_check):
        """
        Check if the given dictionary with connection parameters is already part of the list, which stores the
        parameters of and for the .yaml file. If the host, the user and the port are identical, the database is
        irrelevant, because all connections to accessible databases are established with only one database. This one
        database is used as entry point.
        """

        # Check every element in the given dictionary and the already stored connections.
        for connection_parameter_dictionary in self.connection_parameters_yaml:
            # Check for identical user, host and port.
            if connection_parameter_dictionary["Username"] == connection_parameter_dictionary_for_check["Username"] \
                    and connection_parameter_dictionary["Host"] == connection_parameter_dictionary_for_check["Host"] \
                    and connection_parameter_dictionary["Port"] == connection_parameter_dictionary_for_check["Port"]:
                return True

        # If a duplicate is not found, this else branch is active.
        else:
            # Return False for unique parameters in host, port and user, because it is not a duplicate.
            return False

    @staticmethod
    def check_for_correct_keys_in_dictionary(dictionary_to_check):
        """
        Get a dictionary with the connection parameters and check for the right keys: Host, Username, Database and Port.
        """

        if "Host" in dictionary_to_check and "Username" in dictionary_to_check and "Database" in dictionary_to_check \
                and "Port" in dictionary_to_check:
            return True

        else:
            return False

    def delete_connection(self, connection_dictionary):
        """
        Delete a connection with its given parameters. The parameters are given in a dictionary. A check is required, so
        only if the connection really exists, it is deleted.
        """

        # Check for the given dictionary in the list.
        if connection_dictionary in self.connection_parameters_yaml:
            # Remove the dictionary in the list of all connection parameter dictionaries.
            self.connection_parameters_yaml.remove(connection_dictionary)
            # Save the current list with the deleted dictionary and return the result as result of the success of
            # committing the current list.
            return self.commit_current_list_to_yaml()

        # Return False for a failure.
        return False

    def change_connection(self, old_connection_dictionary, new_connection_dictionary, password_change=False):
        """
        Change the connection parameters in the class-wide list for all connections. Use the old connection and find it
        in the list for all connections. Then, replace the old connection with the new. Save the changes in the .yaml
        file. Use the parameter for a changed password, so if only the password is changed, a duplicate can be found.
        """

        # Check for the correct keys in the new dictionary before inserting them.
        if self.check_for_correct_keys_in_dictionary(new_connection_dictionary) is False:
            return False

        # Proceed, if the password is changed or a duplicate is not found. If the password changed, a duplicate is
        # irrelevant. But there could also be the change of a password and another parameter.
        if password_change is True or self.check_parameter_for_duplicate(new_connection_dictionary) is False:
            # Use a list comprehension to replace the old dictionary with the new one. For this operation, it is
            # necessary to find the old dictionary in the list of all connection dictionaries.
            self.connection_parameters_yaml[:] = [
                new_connection_dictionary if connection_dictionary == old_connection_dictionary
                else connection_dictionary for connection_dictionary in self.connection_parameters_yaml
            ]

            # Commit the new list to the .yaml file and return the result.
            return self.commit_current_list_to_yaml()

        # Return False for a failure.
        return False

    def get_number_of_connection_parameters(self):
        """
        Get the current number of existing dictionaries with connection parameters. The class-wide list contains the
        latest updates and is identical with the connections in the .yaml file.
        """

        return len(self.connection_parameters_yaml)

    def get_index_of_connection(self, connection_parameters_dictionary_to_check):
        """
        Get a dictionary with database connection parameters to check for the index in the current list.
        """

        # Check for every item in the list for a match.
        for index in range(len(self.connection_parameters_yaml)):
            # If the list of all dictionaries contains the given dictionary, there is a match.
            if self.connection_parameters_yaml[index] == connection_parameters_dictionary_to_check:

                # Return the current index of the connection.
                return index

    def get_connection_at_index(self, connection_at_index):
        """
        Use a given index to get a connection at this given index.
        """

        # Use the given index for getting the related connection.
        try:
            connection_at_index = self.connection_parameters_yaml[connection_at_index]
            return connection_at_index

        # Return None for an index out of the bounds of the list.
        except IndexError:
            return None


global_connection_store = ConnectionStore()
