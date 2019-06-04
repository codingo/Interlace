from argparse import ArgumentParser
from netaddr import IPNetwork, IPRange, IPGlob
from Interlace.lib.core.output import OutputHelper, Level
import os.path
from os import access, W_OK
import sys
from re import compile
from random import sample
from math import ceil


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
    def _replace_variable_for_commands(commands, variable, replacements):
        tmp_commands = set()

        test = list()

        if not variable in sample(commands, 1)[0]:
            return commands

        for replacement in replacements:
            for command in commands:
                test.append(str(command).replace(variable, str(replacement)))

        tmp_commands.update(test)
        return tmp_commands
        
    @staticmethod
    def _replace_variable_array(commands, variable, replacement):
        tmp_commands = set()
        counter = 0

        test = list()

        if not variable in sample(commands, 1)[0]:
            return commands

        for command in commands:
            test.append(str(command).replace(variable, str(replacement[counter])))
            counter += 1

        tmp_commands.update(test)
        return tmp_commands


    @staticmethod
    def process_commands(arguments):
        commands = set()
        ranges = set()
        targets = set()
        exclusions_ranges = set()
        exclusions = set()
        final_commands = set()
        output = OutputHelper(arguments)

        # checking for whether output is writable and whether it exists
        if arguments.output:
            if not access(arguments.output, W_OK):
                raise Exception("Directory provided isn't writable")

        if arguments.port:
            if "," in arguments.port:
                ports = arguments.port.split(",")
            elif "-" in arguments.port:
                tmp_ports = arguments.port.split("-")
                if int(tmp_ports[0]) >= int(tmp_ports[1]):
                    raise Exception("Invalid range provided")
                ports = list(range(int(tmp_ports[0]), int(tmp_ports[1]) + 1))
            else:
                ports = [arguments.port]

        if arguments.realport:
            if "," in arguments.realport:
                real_ports = arguments.realport.split(",")
            elif "-" in arguments.realport:
                tmp_ports = arguments.realport.split("-")
                if int(tmp_ports[0]) >= int(tmp_ports[1]):
                    raise Exception("Invalid range provided")
                real_ports = list(range(int(tmp_ports[0]), int(tmp_ports[1]) + 1))
            else:
                real_ports = [arguments.realport]


        # process targets first
        if arguments.target:
            ranges.add(arguments.target)
        else:
            targetFile = arguments.target_list
            if not sys.stdin.isatty():
                targetFile = sys.stdin
            for target in targetFile:
                if target.strip():
                    ranges.add(target.strip())          

        # process exclusions first
        if arguments.exclusions:
            exclusions_ranges.add(arguments.exclusions)
        else:
            if arguments.exclusions_list:
                for exclusion in arguments.exclusions_list:
                    exclusions_ranges.add(target.strip())

        # removing elements that may have spaces (helpful for easily processing comma notation)
        for target in ranges:
            target = target.replace(" ", "")

            for ips in target.split(","):

                # check if it is a domain name
                if ips.split(".")[-1][0].isalpha():
                    targets.add(ips)
                    continue
                # checking for CIDR
                if not arguments.nocidr and "/" in ips:
                    targets.update(InputHelper._get_cidr_to_ips(ips))
                # checking for IPs in a range 
                elif "-" in ips:
                    targets.update(InputHelper._get_ips_from_range(ips))
                # checking for glob ranges
                elif "*" in ips:
                    targets.update(InputHelper._get_ips_from_glob(ips))
                else:
                    targets.add(ips)

        # removing elements that may have spaces (helpful for easily processing comma notation)
        for exclusion in exclusions_ranges:
            exclusion = exclusion.replace(" ", "")

            for ips in exclusion.split(","):
                # check if it is a domain name
                if ips.split(".")[-1][0].isalpha():
                    targets.add(ips)
                    continue
                # checking for CIDR
                if not arguments.nocidr and "/" in ips:
                    exclusions.update(InputHelper._get_cidr_to_ips(ips))
                # checking for IPs in a range 
                elif "-" in ips:
                    exclusions.update(InputHelper._get_ips_from_range(ips))
                # checking for glob ranges
                elif "*" in ips:
                    exclusions.update(InputHelper._get_ips_from_glob(ips))
                else:
                    exclusions.add(ips)

        # difference operation
        targets -= exclusions

        if len(targets) == 0:
            raise Exception("No target provided, or empty target list")

        if arguments.command:
            commands.add(arguments.command.rstrip('\n'))
        else:
            for command in arguments.command_list:
                commands.add(command.rstrip('\n'))

        final_commands = InputHelper._replace_variable_for_commands(commands, "_target_", targets)
        final_commands = InputHelper._replace_variable_for_commands(final_commands, "_host_", targets)

        if arguments.port:
            final_commands = InputHelper._replace_variable_for_commands(final_commands, "_port_", ports)

        if arguments.realport:
            final_commands = InputHelper._replace_variable_for_commands(final_commands, "_realport_", real_ports)

        if arguments.output:
            final_commands = InputHelper._replace_variable_for_commands(final_commands, "_output_", [arguments.output])

        if arguments.proto:
            if "," in arguments.proto:
                protocols = arguments.proto.split(",")
            else:
                protocols = arguments.proto
            final_commands = InputHelper._replace_variable_for_commands(final_commands, "_proto_", protocols)
        
        # process proxies
        if arguments.proxy_list:
            proxy_list = list()
            for proxy in arguments.proxy_list:
                if proxy.strip():
                    proxy_list.append(proxy.strip())

            if len(proxy_list) < len(final_commands):
                proxy_list = ceil(len(final_commands) / len(proxy_list)) * proxy_list

            final_commands = InputHelper._replace_variable_array(final_commands, "_proxy_", proxy_list)

        return final_commands


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
            '--no-bar', '--sober', dest='sober', action='store_true', default=True,
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
