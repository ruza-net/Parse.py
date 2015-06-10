__author__ = 'Jan Růžička <jan.ruzicka01@gmail.com>'
__version__ = "0.5.0"

from utils import *
from parse import *

def main():
    rule = word() + word() + liter("!")

if __name__ == "__main__":
    main()