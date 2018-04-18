try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': "stuff to mangle MARC",
    'author': "Stefan Schuh",
    'author_email': "stefan.schuh@uni-graz.at",
    'version': "0.1",
    'install_requires': ['pytest', 'pymarc', 'texttable'],
    'packages': ["mangle_marc"],
    'scripts': [],
    'name': 'mangle_marc',
        }

setup(**config)

