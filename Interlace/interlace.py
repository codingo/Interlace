#!/usr/bin/python3

from sys import argv

from Interlace.lib.core.input import InputParser, InputHelper
from Interlace.lib.core.output import OutputHelper, Level
from Interlace.lib.threader import Pool


def build_queue(arguments, output, repeat):
    task_list = InputHelper.process_commands(arguments)
    for task in task_list:
        output.terminal(Level.THREAD, task.name(), "Added to Queue")
    print('Generated {} commands in total'.format(len(task_list)))
    print('Repeat set to {}'.format(repeat))
    return task_list * repeat


def main():
    parser = InputParser()
    arguments = parser.parse(argv[1:])
    output = OutputHelper(arguments)

    output.print_banner()

    if arguments.repeat:
        repeat = int(arguments.repeat)
    else:
        repeat = 1
    
    
    pool = Pool(arguments.threads, build_queue(arguments, output, repeat), arguments.timeout, output, arguments.sober)
    pool.run()


if __name__ == "__main__":
    main()
