import logging

from PyQt5.Qsci import QsciLexerSQL, QsciLexerCustom
from PyQt5.QtGui import QColor

from pygadmin.configurator import global_app_configurator


class SQLLexer(QsciLexerSQL, QsciLexerCustom):
    """
    Create a custom lexer class for style customization. The background color of the lexer, the font color, the color of
    specific keywords are configurable.
    """

    def __init__(self, scintilla):
        super().__init__(scintilla)
        self.init_colors()

    def init_colors(self):
        """
        Initialize the colors of the lexer.
        """

        self.color_parameters_dictionary = {}

        default_style = global_app_configurator.get_default_color_theme_style()

        if default_style:
            self.style_name = default_style[0]
            for color_description, color_string in default_style[1].items():
                self.color_parameters_dictionary[color_description] = QColor(color_string)

        if not default_style:
            self.style_name = "Default"
            self.color_parameters_dictionary = {
                "default_color": QColor("ff000000"),
                "default_paper_color": QColor("#ffffffff"),
                "keyword_color": QColor("#ff00007f"),
                "number_color": QColor("#ff007f7f"),
                "other_keyword_color": QColor("#ff7f7f00"),
                "apostrophe_color": QColor("#ff7f007f")
            }

            self.save_dictionary_with_style_information()

        self.set_lexer_colors(self.color_parameters_dictionary)

    def set_lexer_colors(self, color_dictionary):
        """
        Set the different colors of the lexer, which are given in a color dictionary. Check every item in the dictionary
        for a potential match in the key. This procedure allows to check for the existence of the key and the further
        usage after a match. Check also the color for a QColor, so only a color of the right type is used. Specific
        integers are used in setColor for specifying the component for the color.
        """

        # Check every key and value pair in the dictionary with the colors.
        for color_description, color_value in color_dictionary.items():
            # Check the given color for its instance/type. Proceed for a QColor.
            if isinstance(color_value, QColor):
                # Set the color for the default color.
                if color_description == "default_color":
                    self.setDefaultColor(color_value)

                # Set the default paper color.
                elif color_description == "default_paper_color":
                    self.setDefaultPaper(color_value)
                    # Use the function setColor() with the value 0 for using the given color for the paper for special
                    # words like keywords.
                    self.setColor(color_value, 0)

                # Set the color for keywords.
                elif color_description == "keyword_color":
                    # The integer value 5 is used for the color of keywords.
                    self.setColor(color_value, 5)

                # Set the color for numbers.
                elif color_description == "number_color":
                    # The integer value 4 is used for the color of numbers.
                    self.setColor(color_value, 4)

                # Set the color for other keywords, which are not a part of "normal" keywords.
                elif color_description == "other_keyword_color":
                    # The integer value 8 is used for the color of those other keywords.
                    self.setColor(color_value, 8)

                # Set the color for the apostrophes and the text inside.
                elif color_description == "apostrophe_color":
                    # The integer value 7 is used for the color of apostrophes and the text inside.
                    self.setColor(color_value, 7)

            # Use this else-branch, if the given color value is not a QColor.
            else:
                # Warn in the log about a missing QColor.
                logging.warning("The given color {} for the color description/color key {} is not a QColor. Potential "
                                "changes in the lexer's and editor's color will not be "
                                "applied.".format(color_value, color_description))

    def save_dictionary_with_style_information(self):
        """
        Save the current style information for further usage with the global app configurator.
        """

        # Create an empty dictionary for the information.
        style_information_dictionary = {}

        # Change every value of the dictionary with its key to a usable value for saving in a .yaml file.
        for color_description, color_q_color in self.color_parameters_dictionary.items():
            # Use the name of the color as string for saving.
            style_information_dictionary[color_description] = color_q_color.name()

        # Add the configuration to the app configurator.
        global_app_configurator.add_style_configuration(self.style_name, style_information_dictionary)
        # Add the configuration name as default configuration to all configurations.
        global_app_configurator.set_single_configuration("color_theme", self.style_name)
        # Save the style configuration.
        global_app_configurator.save_style_configuration_data()
        # Save the configuration data.
        global_app_configurator.save_configuration_data()
