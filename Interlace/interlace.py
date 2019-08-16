#!/usr/bin/python3
import sys
from Interlace.lib.core.input import InputParser, InputHelper
from Interlace.lib.core.output import OutputHelper, Level
from Interlace.lib.threader import Pool, TaskBlock


def print_command(level, command, message, output):
    if isinstance(command, TaskBlock):
        for c in command:
            print_command(level, c, message, output)
    else:
        output.terminal(Level.THREAD, command.name(), "Added to Queue")


def build_queue(arguments, output):
    task_queue = InputHelper.process_commands(arguments)
    task_list = []
    for task in task_queue:
        print_command(Level.THREAD, task, "Added to Queue", output)
        task_list.append(task)
    return task_list


def main():
    parser = InputParser()
    arguments = parser.parse(sys.argv[1:])

    output = OutputHelper(arguments)

    output.print_banner()

    pool = Pool(arguments.threads, build_queue(arguments, output), arguments.timeout, output, arguments.sober)
    pool.run()


if __name__ == "__main__":
    main()
