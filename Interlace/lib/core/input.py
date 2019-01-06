from argparse import ArgumentParser
import os.path


class InputHelper(object):
    @staticmethod
    def readable_file(parser, arg):
        if not os.path.exists(arg):
            parser.error("The file %s does not exist!" % arg)
        else:
            return open(arg, 'r')  # return an open file handle

    @staticmethod
    def check_positive(parser, arg):
        ivalue = int(arg)
        if ivalue <= 0:
            raise parser.ArgumentTypeError("%s is not a valid positive integer!" % arg)

        return arg

    @staticmethod
    def process_targets(arguments):
        targets = set()

        # build list of targets from file/input
        if arguments.target:
            targets.add(arguments.target)
        else:
            for target in arguments.target_list:
                targets.add(target.strip())
                print('[DEBUG] Added Target')

        # take list of targets and expand CIDR / comma notation
        if not arguments.nocidr:
            # expand CIDR from net addr
            pass

        # expand comma notation

        # return list of unique hosts
        return targets

    @staticmethod
    def process_commands(arguments):
        commands = set()
        print("[DEBUG] Commands argument: %s" % arguments.command)
        if arguments.command:
            commands.add(arguments.command)
            print("[DEBUG] Added command")
        else:
            for command in arguments.command_list:
                commands.add(command.strip())
                print("[DEBUG] Added command")

        targets = InputHelper.process_targets(arguments)

        for target in targets:
            # replace flags
            for command in commands:
                command = command.replace("_target_", target)
                command = command.replace("_output_", arguments.output)
                command = command.replace("_port_", arguments.port)
                command = command.replace("_realport_", arguments.realport)
                commands.add(command)
                print("[DEBUG] Added command")
        return commands


class InputParser(object):
    def __init__(self):
        self._parser = self.setup_parser()

    def parse(self, argv):
        return self._parser.parse_args(argv)

    @staticmethod
    def setup_parser():
        parser = ArgumentParser()

        targets = parser.add_mutually_exclusive_group(required=True)

        targets.add_argument(
            '-t', dest='target', required=False,
            help='Specify a target or domain name either in comma format, '
                 'CIDR notation, or a single target.'
        )

        targets.add_argument(
            '-tL', dest='target_list', required=False,
            help='Specify a list of targets or domain names.',
            metavar="FILE",
            type=lambda x: InputHelper.readable_file(parser, x)
        )

        parser.add_argument(
            '-threads', dest='threads', required=False,
            help="Specify the maximum number of threads to run (DEFAULT:5)",
            default=5,
            type=lambda x: InputHelper.check_positive(parser, x)
        )

        parser.add_argument(
            '-timeout', dest='timeout', required=False,
            help="Command timeout in seconds (DEFAULT:600)",
            default=600,
            type=lambda x: InputHelper.check_positive(parser, x)
        )

        commands = parser.add_mutually_exclusive_group(required=True)
        commands.add_argument(
            '-c', dest='command',
            help='Specify a single command to execute.'
        )

        commands.add_argument(
            '-cL', dest='command_list', required=False,
            help='Specify a list of commands to execute',
            metavar="FILE",
            type=lambda x: InputHelper.readable_file(parser, x)
        )

        parser.add_argument(
            '-o', dest='output',
            help='Specify an output folder variable that can be used in commands as _output_'
        )

        parser.add_argument(
            '-p', dest='port',
            help='Specify a port variable that can be used in commands as _port_'
        )

        parser.add_argument(
            '-rp', dest='realport',
            help='Specify a real port variable that can be used in commands as _realport_'
        )

        parser.add_argument(
            '--no-cidr', dest='nocidr', action='store_true', default=False,
            help='If set then CIDR notation in a target file will not be automatically '
                 'be expanded into individual hosts.'
        )

        parser.add_argument(
            '--no-color', dest='nocolor', action='store_true', default=False,
            help='If set then any foreground or background colours will be '
                 'stripped out.'
        )

        output_types = parser.add_mutually_exclusive_group()
        output_types.add_argument(
            '-v', '--verbose', dest='verbose', action='store_true', default=False,
            help='If set then verbose output will be displayed in the terminal.'
        )
        output_types.add_argument(
            '--silent', dest='silent', action='store_true', default=False,
            help='If set only findings will be displayed and banners '
                 'and other information will be redacted.'
        )

        return parser
