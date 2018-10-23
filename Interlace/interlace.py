#!/usr/bin/python3
import sys
from lib.core.input import InputParser

def main():
    parser = InputParser()
    arguments = parser.parse(sys.argv[1:])


if __name__ == "__main__":
    main()