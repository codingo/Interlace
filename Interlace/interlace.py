#!/usr/bin/python3

from sys import argv

from Interlace.lib.core.input import InputParser, InputHelper
from Interlace.lib.core.output import OutputHelper, Level
from Interlace.lib.threader import Pool


def task_queue_generator_func(arguments, output, repeat):
    tasks_data = InputHelper.process_data_for_tasks_iterator(arguments)
    tasks_count = tasks_data["tasks_count"]
    yield tasks_count
    tasks_generator_func = InputHelper.make_tasks_generator_func(tasks_data)
    for i in range(repeat):
        tasks_iterator = tasks_generator_func()
        for task in tasks_iterator:
            output.terminal(Level.THREAD, task.name(), "Added to Queue")
            yield task
    print('Generated {} commands in total'.format(tasks_count))
    print('Repeat set to {}'.format(repeat))


def main():
    parser = InputParser()
    arguments = parser.parse(argv[1:])
    output = OutputHelper(arguments)

    output.print_banner()

    if arguments.repeat:
        repeat = int(arguments.repeat)
    else:
        repeat = 1

    pool = Pool(
        arguments.threads,
        task_queue_generator_func(arguments, output, repeat),
        arguments.timeout,
        output,
        arguments.sober,
    )
    pool.run()


if __name__ == "__main__":
    main()
