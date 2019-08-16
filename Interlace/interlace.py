#!/usr/bin/python3

from Interlace.lib.core.input import InputParser, InputHelper
from Interlace.lib.core.output import OutputHelper, Level
from Interlace.lib.threader import Pool


def build_queue(arguments, output):
    task_list = InputHelper.process_commands(arguments)
    for task in task_list:
        output.terminal(Level.THREAD, task.name(), "Added to Queue")
    return task_list


def main():
    parser = InputParser()
    args = ["-cL", "C:\\Users\\user\\Documents\\PythonProjects\\Interlace\\foo.test",
            "-tL", "C:\\Users\\user\\Documents\\PythonProjects\\Interlace\\bar.test"]
    arguments = parser.parse(args)
    # arguments = parser.parse(sys.argv[1:])

    output = OutputHelper(arguments)

    output.print_banner()

    pool = Pool(arguments.threads, build_queue(arguments, output), arguments.timeout, output, arguments.sober)
    pool.run()


if __name__ == "__main__":
    main()
