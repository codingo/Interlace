import os.path
import sys
from argparse import ArgumentParser
from math import ceil
from random import sample

from netaddr import IPNetwork, IPRange, IPGlob

from Interlace.lib.threader import Task


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
    def _get_ips_from_range(ip_range):
        ips = set()
        ip_range = ip_range.split("-")

        # parsing the above structure into an array and then making into an IP address with the end value
        end_ip = ".".join(ip_range[0].split(".")[0:-1]) + "." + ip_range[1]

        # creating an IPRange object to get all IPs in between
        range_obj = IPRange(ip_range[0], end_ip)

        for ip in range_obj:
            ips.add(str(ip))

        return ips

    @staticmethod
    def _get_ips_from_glob(glob_ips):
        ip_glob = IPGlob(glob_ips)

        ips = set()

        for ip in ip_glob:
            ips.add(str(ip))

        return ips

    @staticmethod
    def _get_cidr_to_ips(cidr_range):
        ips = set()

        for ip in IPNetwork(cidr_range):
            ips.add(str(ip))

        return ips

    @staticmethod
    def _process_port(port_type):
        if "," in port_type:
            return port_type.split(",")
        elif "-" in port_type:
            tmp = port_type.split("-")
            begin_range = int(tmp[0])
            end_range = int(tmp[1])
            if begin_range >= end_range:
                raise Exception("Invalid range provided")
            return list(range(begin_range, end_range + 1))
        return [port_type]

    @staticmethod
    def _pre_process_commands(command_list, task_name, is_global_task=True):
        task_block = []
        sibling = None
        global_task = None
        for command in command_list:
            command = str(command).strip()
            if not command:
                continue
            if command.startswith('_block:') and command.endswith('_'):
                new_task_name = command.split('_block:')[1][:-1].strip()
                if task_name == new_task_name:
                    return task_block
                for task in InputHelper._pre_process_commands(command_list, new_task_name, False):
                    task_block.append(task)
                    sibling = task
                continue
            else:
                if command == '_blocker_':
                    global_task = sibling
                    continue
                task = Task(command)
                if is_global_task and global_task:
                    print('{} must wait for GLOBAL {}'.format(task.name(), global_task.name()))
                    task.wait_for(global_task.get_lock())
                elif sibling:
                    task.wait_for(sibling.get_lock())
                    print('{} is waiting for {}'.format(task.name(), sibling.name()))
                task_block.append(task)
                sibling = task
        return task_block

    @staticmethod
    def _pre_process_hosts(host_ranges, destination_set, arguments):
        for host in host_ranges:
            host = host.replace(" ", "")
            for ips in host.split(","):
                # check if it is a domain name
                if ips.split(".")[-1][0].isalpha():
                    destination_set.add(ips)
                    continue
                # checking for CIDR
                if not arguments.nocidr and "/" in ips:
                    destination_set.update(InputHelper._get_cidr_to_ips(ips))
                # checking for IPs in a range
                elif "-" in ips:
                    destination_set.update(InputHelper._get_ips_from_range(ips))
                # checking for glob ranges
                elif "*" in ips:
                    destination_set.update(InputHelper._get_ips_from_glob(ips))
                else:
                    destination_set.add(ips)

    @staticmethod
    def _replace_variable_with_commands(commands, variable, replacements):
        def add_task(t, item_list):
            if t not in set(item_list):
                item_list.append(t)

        tasks = []
        for command in commands:
            for replacement in replacements:
                if command.name().find(variable) != -1:
                    new_task = command.clone()
                    new_task.replace(variable, replacement)
                    add_task(new_task, tasks)
                else:
                    add_task(command, tasks)
        return tasks

    @staticmethod
    def _replace_variable_array(commands, variable, replacement):
        # TODO
        if variable not in sample(commands, 1)[0]:
            return

        for counter, command in enumerate(commands):
            command.replace(variable, str(replacement[counter]))

    @staticmethod
    def process_commands(arguments):
        commands = list()
        ranges = set()
        targets = set()
        exclusions_ranges = set()
        exclusions = set()

        if arguments.output and arguments.output[-1] == "/":
            arguments.output = arguments.output[:-1]

        if arguments.port:
            ports = InputHelper._process_port(arguments.port)

        if arguments.realport:
            real_ports = InputHelper._process_port(arguments.realport)

        # process targets first
        if arguments.target:
            ranges.add(arguments.target)
        else:
            target_file = arguments.target_list
            # if not sys.stdin.isatty():
            #     target_file = sys.stdin
            ranges.update([target.strip() for target in target_file if target.strip()])

        # process exclusions first
        if arguments.exclusions:
            exclusions_ranges.add(arguments.exclusions)
        else:
            if arguments.exclusions_list:
                for exclusion in arguments.exclusions_list:
                    exclusion = exclusion.strip()
                    if exclusion:
                        exclusions.add(exclusion)

        # removing elements that may have spaces (helpful for easily processing comma notation)
        InputHelper._pre_process_hosts(ranges, targets, arguments)
        InputHelper._pre_process_hosts(exclusions_ranges, exclusions, arguments)

        # difference operation
        targets -= exclusions

        if len(targets) == 0:
            raise Exception("No target provided, or empty target list")

        if arguments.command:
            commands.append(arguments.command.rstrip('\n'))
        else:
            commands = InputHelper._pre_process_commands(arguments.command_list, '')

        commands = InputHelper._replace_variable_with_commands(commands, "_target_", targets)
        commands = InputHelper._replace_variable_with_commands(commands, "_host_", targets)

        if arguments.port:
            commands = InputHelper._replace_variable_with_commands(commands, "_port_", ports)

        if arguments.realport:
            commands = InputHelper._replace_variable_with_commands(commands, "_realport_", real_ports)

        if arguments.output:
            commands = InputHelper._replace_variable_with_commands(commands, "_output_", [arguments.output])

        if arguments.proto:
            if "," in arguments.proto:
                protocols = arguments.proto.split(",")
            else:
                protocols = arguments.proto
            commands = InputHelper._replace_variable_with_commands(commands, "_proto_", protocols)

        # process proxies
        if arguments.proxy_list:
            proxy_list = [proxy for proxy in arguments.proxy_list if proxy.strip()]
            if len(proxy_list) < len(commands):
                proxy_list = ceil(len(commands) / len(proxy_list)) * proxy_list

            InputHelper._replace_variable_array(commands, "_proxy_", proxy_list)
        return commands


class InputParser(object):
    def __init__(self):
        self._parser = self.setup_parser()

    def parse(self, argv):
        return self._parser.parse_args(argv)

    @staticmethod
    def setup_parser():
        parser = ArgumentParser()

        #Is stdin attached?
        requireTargetArg = True
        if not sys.stdin.isatty():
            requireTargetArg = False

        targets = parser.add_mutually_exclusive_group(required=requireTargetArg)

        targets.add_argument(
            '-t', dest='target', required=False,
            help='Specify a target or domain name either in comma format, '
                 'CIDR notation, glob notation, or a single target.'
        )

        targets.add_argument(
            '-tL', dest='target_list', required=False,
            help='Specify a list of targets or domain names.',
            metavar="FILE",
            type=lambda x: InputHelper.readable_file(parser, x)
        )

        # exclusions group
        exclusions = parser.add_mutually_exclusive_group()

        exclusions.add_argument(
            '-e', dest='exclusions', required=False,
            help='Specify an exclusion either in comma format, '
                 'CIDR notation, or a single target.'
        )

        exclusions.add_argument(
            '-eL', dest='exclusions_list', required=False,
            help='Specify a list of exclusions.',
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

        parser.add_argument(
            '-pL', dest='proxy_list', required=False,
            help='Specify a list of proxies.',
            metavar="FILE",
            type=lambda x: InputHelper.readable_file(parser, x)
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
            '--proto', dest='proto',
            help='Specify protocols that can be used in commands as _proto_'
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

        parser.add_argument(
            '--no-bar', '--sober', dest='sober', action='store_true', default=False,
            help='If set then progress bar will be stripped out'
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
