import io
import os
import subprocess
from setuptools import setup, find_packages


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(filename):
    with io.open(os.path.join(os.path.dirname(__file__), filename)) as f:
        return f.read()


def determine_version():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    ver_file = os.path.join(dir_path, "version.txt")
    version = "0.0.0"
    if os.path.exists(ver_file):
        version = read(ver_file)
    # If this is a release file and no git is found, use version.txt
    if not os.path.isdir(os.path.join(dir_path, ".git")):
        return version
    # Derive version from git
    try:
        output = subprocess.check_output(['git', 'describe', '--tags', '--dirty'], cwd=dir_path) \
            .decode('utf-8').strip().split('-')
        if len(output) == 1:
            return output[0]
        elif len(output) == 2:
            return "{}.dev0".format(output[0])
        else:
            release = 'dev' if len(output) == 4 and output[3] == 'dirty' else ''
            return "{}.{}{}+{}".format(output[0], release, output[1], output[2])
    except subprocess.CalledProcessError:
        try:
            commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()
            status = subprocess.check_output(['git', 'status', '-s']).decode('utf-8').strip()
            return "{}.dev0+{}".format(version, commit) if len(status) > 0 else "{}+{}".format(version, commit)
        except subprocess.CalledProcessError:
            # finding the git version has utterly failed, use version.txt
            return version


setup(
    name="Pygadmin",
    version=determine_version(),
    author="KDV",
    author_email="pygadmin@kdv.bayern",
    description="A QT-based database administration tool for PostgreSQL databases",
    url="https://www.kdv.bayern/",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: Unix",
        "Operating System :: Microsoft :: Windows"
    ],
    python_requires='>=3.6',
    install_requires=[
        "psycopg2",
        "PyYAML",
        "PyQt5",
        "QScintilla",
        "keyring",
    ],
    packages=find_packages(),
    package_data={
        'pygadmin': [
                'icons/*',
                'logging.yaml',
        ],
    },
    entry_points={
        "gui_scripts": [
            "pygadmin = pygadmin:main",
        ]
    },
)
