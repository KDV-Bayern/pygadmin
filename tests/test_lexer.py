import unittest

from PyQt5.QtGui import QColor

from pygadmin.models.lexer import SQLLexer


class TestLexerMethods(unittest.TestCase):
    """
    Use a class for testing the SQLLexer and its methods.
    """

    def test_lexer_color_parameters_dictionary(self):
        """
        Check the color parameter dictionary of the lexer, which should be not empty.
        """

        lexer = SQLLexer(None)

        assert lexer.color_parameters_dictionary != {}

    def test_qcolor_lexer(self):
        """
        Check the correct instance of the color in the color parameter dictionary of the lexer.
        """

        lexer = SQLLexer(None)

        for value in lexer.color_parameters_dictionary.values():
            assert isinstance(value, QColor)

    def test_correct_color_parameter_keys(self):
        """
        Check for the right keys in the color parameter dictionary of the lexer.
        """

        lexer = SQLLexer(None)
        # Define the relevant color keys.
        color_keys = ["default_color", "default_paper_color", "keyword_color", "number_color", "other_keyword_color",
                      "apostrophe_color"]

        # Check every necessary key for its existence.
        for color in color_keys:
            assert lexer.color_parameters_dictionary[color]

    def test_set_color(self):
        """
        Test the method of the lexer for setting a color defined by a color dictionary with the color keyword and a
        QColor for testing the color set.
        """

        lexer = SQLLexer(None)
        # Define a color dictionary with tests.
        color_dictionary = {"default_color": QColor("ff0000ff"),
                            "default_paper_color": QColor("#ffffff00"),
                            "keyword_color": QColor("#ff00000f"),
                            "number_color": QColor("#ff000f0f"),
                            "other_keyword_color": QColor("#ff0f0f00"),
                            "apostrophe_color": QColor("#ff0f0000")
                            }

        # Set the colors in the lexer.
        lexer.set_lexer_colors(color_dictionary)

        # Check, if every color has been set properly.
        assert color_dictionary["default_color"].name() == lexer.defaultColor(10).name()
        assert color_dictionary["default_paper_color"].name() == lexer.defaultPaper(0).name()
        assert color_dictionary["default_paper_color"].name() == lexer.color(0).name()
        assert color_dictionary["keyword_color"].name() == lexer.color(5).name()
        assert color_dictionary["number_color"].name() == lexer.color(4).name()
        assert color_dictionary["other_keyword_color"].name() == lexer.color(8).name()
        assert color_dictionary["apostrophe_color"].name() == lexer.color(7).name()

