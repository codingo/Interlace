#!/usr/bin/python3
import sys
from lib.core.input import InputParser, InputHelper
from lib.core.output import OutputHelper, Level
from lib.core.threader import Pool


def build_queue(arguments, output):
    queue = list()
    for target in InputHelper.process_targets(arguments):
        for command in InputHelper.process_commands(arguments):
            output.terminal(Level.VERBOSE, target, command, "Added to Queue")
            queue.append(command)
    return queue


def main():
    parser = InputParser()
    arguments = parser.parse(sys.argv[1:])

    output = OutputHelper(arguments)

    output.print_banner()

    pool = Pool(arguments.threads, build_queue(arguments, output), arguments.timeout, output)
    pool.run()


if __name__ == "__main__":
    main()