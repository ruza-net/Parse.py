__author__ = 'Jan Růžička <jan.ruzicka01@gmail.com>'
__version__ = "1.0.0"

from utils import *
from parse import *


def main():
    setIgnored(" \n\t")

    greeting = "Hello " + word() + "!"

if __name__ == "__main__":
    main()