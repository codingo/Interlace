""" __Doc__ File handle class """
from setuptools import find_packages, setup
from Interlace.lib.core.__version__ import __version__


def dependencies(imported_file):
    """ __Doc__ Handles dependencies """
    with open(imported_file) as file:
        return file.read().splitlines()


with open("README.md") as file:
    num_installed = True
    try:
        import numpy
        num_installed = True
    except ImportError:
        pass
    setup(
        name="Interlace",
        license="GPLv3",
        description="Adds Multi Threading and CIDR support for applications that don't support it, "
                    "or better managed threads for those that do."
                    "Multiple commands over multiple hosts.",
        long_description=file.read(),
        author="codingo",
        version=__version__,
        author_email="codingo@protonmail.com",
        url="https://github.com/codingo/Interlace",
        packages=find_packages(exclude=('tests')),
        package_data={'Interlace': ['*.txt']},
        entry_points={
            'console_scripts': [
                'interlace = Interlace.interlace:main'
            ]
        },
        install_requires=dependencies('requirements.txt'),
        tests_require=dependencies('test-requirements.txt'),
        include_package_data=True)
