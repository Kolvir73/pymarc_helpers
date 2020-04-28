try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': "Helper functions for pymarc",
    'author': "Stefan Schuh",
    'author_email': "stefan.schuh@uni-graz.at",
    'version': "0.2",
    'install_requires': ['pytest', 'pymarc', 'texttable'],
    'packages': ["pymarc_helpers"],
    'scripts': [],
    'name': 'pymarc_helpers',
    'entry_points': {
        "console_scripts": [
            "process_marc=pymarc_helpers.cli:main"
        ]
    }
        }

setup(**config)

