# Pygadmin
Pygadmin is a database administration tool written in Python with the framework Qt (PyQt) 
for the user interface and psycopg2 as a database adapter. The tool is meant for the management
of PostgreSQL databases. 

## Running Pygadmin
Pygadmin is intended to be run as a normal user and with its GUI. Just run the file `__main__.py` 
after the installation.

## Requirements
* Python (3.6+)
* psycopg2
* PyYAML
* PyQt5
* QScintilla
* keyring

## Installing Pygadmin
The file `setup.py` contains all the requirements. After cloning the repository, Pygadmin can
be installed with pip. Just navigate into the pygadmin folder and use `pip install .` for 
installing.

