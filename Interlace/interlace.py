#!/usr/bin/python3
import sys
from Interlace.lib.core.input import InputParser, InputHelper
from Interlace.lib.core.output import OutputHelper, Level
from Interlace.lib.threader import Pool


def build_queue(arguments, output):
    queue = InputHelper.process_commands(arguments)
    for command_list in queue:
        for command in command_list:
            output.terminal(Level.THREAD, command, "Added to Queue")
    return queue

def main():
    parser = InputParser()
    arguments = parser.parse(sys.argv[1:])

    output = OutputHelper(arguments)

    output.print_banner()

    pool = Pool(arguments.threads, build_queue(arguments, output), arguments.timeout, output, arguments.sober)
    pool.run()


if __name__ == "__main__":
    main()
