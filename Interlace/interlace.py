#!/usr/bin/python3
import sys
from lib.core.input import InputParser, InputHelper
from lib.core.output import OutputHelper, Level


def main():
    parser = InputParser()
    arguments = parser.parse(sys.argv[1:])
    output = OutputHelper(arguments)

    output.print_banner()

    for target in InputHelper.process_targets(arguments):
        for command in InputHelper.process_commands(arguments):
            output.terminal(Level.THREAD, target, command)

if __name__ == "__main__":
    main()