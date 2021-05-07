import functools
import itertools
import os.path
import socket
import struct
import sys
from argparse import ArgumentParser
from io import TextIOWrapper
from random import choice

from Interlace.lib.threader import Task
from netaddr import IPGlob, IPRange, IPSet, glob_to_iprange


class InputHelper(object):
    @staticmethod
    def check_path(parser, arg):
        if not os.path.exists(arg):
            parser.error("The path %s does not exist!" % arg)
        else:
            return arg

    @staticmethod
    def readable_file(parser, arg):
        if InputHelper.check_path(parser, arg):
            return open(arg, 'r')  # return an open file handle

    @staticmethod
    def check_positive(parser, arg):
        try:
            ivalue = int(arg)
            if ivalue <= 0:
                raise parser.ArgumentTypeError("%s is not a valid positive integer!" % arg)
        except ValueError:
            raise parser.ArgumentValueError("%s is not a a number!" % arg)

        return arg

    @staticmethod
    def _get_files_from_directory(arg):
        files = list()

        for file in os.listdir(arg):
            location = os.path.join(arg, file)
            if os.path.isfile(location):
                files.append(location)

        return files

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
    def _pre_process_commands(command_list, task_name=None, is_global_task=True):
        """
        :param command_list:
        :param task_name: all tasks have 'scope' and all scopes have unique names, global scope defaults None
        :param is_global_task: when True, signifies that all global tasks are meant to be run concurrently
        :return: list of possibly re-adjusted commands
        """
        task_block = []
        sibling = None
        blocker = None
        for command in command_list:
            command = str(command).strip()
            if len(command) == 0:
                continue
            # the start or end of a command block
            if (command.startswith('_block:') and command.endswith('_')) or\
                    command == '_block_':
                # if this is the end of a block, then we're done
                new_task_name = ''
                if command.startswith('_block:'):
                    new_task_name = command.split('_block:')[1][:-1].strip()
                if task_name and task_name == new_task_name:
                    return task_block
                # otherwise pre-process all the commands in this new `new_task_name` block
                tasks = InputHelper._pre_process_commands(command_list, new_task_name, False)
                if blocker:
                    for task in tasks:
                        task.wait_for(task_block)
                task_block += tasks
                if len(tasks) > 0:
                    sibling = tasks[-1]
                continue
            else:
                # if a blocker is encountered, all commands following the blocker must wait until the last
                # command in the block is executed. All block commands are synchronous
                if command == '_blocker_':
                    blocker = sibling
                    continue
                task = Task(command)
                # if we're in the global scope and there was a previous _blocker_ encountered, we wait for the last
                # child of the block
                if is_global_task and blocker:
                    task.wait_for(task_block)
                # all but the first command in a block scope wait for its predecessor
                elif sibling and not is_global_task:
                    task.wait_for([sibling])
                task_block.append(task)
                sibling = task
        return task_block

    @staticmethod
    def _replace_target_variables_in_commands(tasks, str_targets, ipset_targets):
        TARGET_VAR = "_target_"
        HOST_VAR = "_host_"
        CLEANTARGET_VAR = "_cleantarget_"
        for task in tasks:
            command = task.name()
            if TARGET_VAR in command or HOST_VAR in command:
                for dirty_target in itertools.chain(str_targets, ipset_targets):
                    yielded_task = task.clone()
                    dirty_target = str(dirty_target)
                    yielded_task.replace(TARGET_VAR, dirty_target)
                    yielded_task.replace(HOST_VAR, dirty_target)
                    yielded_task.replace(
                        CLEANTARGET_VAR,
                        dirty_target.replace("http://", "").replace(
                            "https://", "").rstrip("/").replace("/", "-"),
                    )
                    yield yielded_task
            elif CLEANTARGET_VAR in command:
                for dirty_target in itertools.chain(str_targets, ipset_targets):
                    yielded_task = task.clone()
                    dirty_target = str(dirty_target)
                    yielded_task.replace(CLEANTARGET_VAR,dirty_target.replace(
                        "http://", "").replace("https://", "").rstrip("/").replace("/", "-"),
                        )
                    yield yielded_task
            else:
                yield task

    @staticmethod
    def _replace_variable_in_commands(tasks_generator_func, variable, replacements):
        for task in tasks_generator_func():
            if variable in task.name():
                for replacement in replacements:
                    yielded_task = task.clone()
                    yielded_task.replace(variable, str(replacement))
                    yield yielded_task
            else:
                yield task

    @staticmethod
    def _replace_variable_array(
        tasks_generator_func, variable, replacements_iterator
    ):
        for task in tasks_generator_func():
            task.replace(variable, str(next(replacements_iterator)))
            yield task

    @staticmethod
    def _process_targets(arguments):
        def pre_process_target_spec(target_spec):
            target_spec = "".join(
                filter(lambda char: char not in (" ", "\n"), target_spec)
            )
            return target_spec.split(",")
            # If ","s not in target_spec, this returns [target_spec], so this
            # static method always returns a list

        if arguments.target:
            target_specs = pre_process_target_spec(arguments.target)
        else:
            target_specs_file = arguments.target_list
            if not isinstance(target_specs_file, TextIOWrapper):
                if not sys.stdin.isatty():
                    target_specs_file = sys.stdin
            target_specs = (
                target_spec.strip() for target_spec in target_specs_file
            )
            target_specs = (
                pre_process_target_spec(target_spec) for target_spec in
                target_specs if target_spec
            )
            target_specs = itertools.chain(*target_specs)

        def parse_and_group_target_specs(target_specs, nocidr):
            str_targets = set()
            ips_list = list()
            for target_spec in target_specs:
                if (
                    target_spec.startswith(".") or
                    (target_spec[0].isalpha() or target_spec[-1].isalpha()) or
                    (nocidr and "/" in target_spec)
                ):
                    str_targets.add(target_spec)
                else:
                    if "-" in target_spec:
                        start_ip, post_dash_segment = target_spec.split("-")
                        end_ip = start_ip.rsplit(".", maxsplit=1)[0] + "." + \
                            post_dash_segment
                        target_spec = IPRange(start_ip, end_ip)
                    elif "*" in target_spec:
                        target_spec = glob_to_iprange(target_spec)
                    else:  # str IP addresses and str CIDR notations
                        if "/" in target_spec:
                            target_spec = IPSet((target_spec,))
                        else:
                            target_spec = [target_spec]
                    
                    for i in target_spec:
                        ips_list.append(str(i))
                    print(f"updating: {target_spec}")
            return (str_targets, set(ips_list))

        str_targets, ipset_targets = parse_and_group_target_specs(
            target_specs=target_specs,
            nocidr=arguments.nocidr,
        )

        if arguments.exclusions or arguments.exclusions_list:
            if arguments.exclusions:
                exclusion_specs = pre_process_target_spec(arguments.exclusions)
            elif arguments.exclusions_list:
                exclusion_specs = (
                    exclusion_spec.strip() for exclusion_spec in
                    arguments.exclusions_list
                )
                exclusion_specs = (
                    pre_process_target_spec(exclusion_spec) for exclusion_spec
                    in exclusion_specs if exclusion_spec
                )
                exclusion_specs = itertools.chain(*exclusion_specs)
            str_exclusions, ipset_exclusions = parse_and_group_target_specs(
                target_specs=exclusion_specs,
                nocidr=arguments.nocidr,
            )

            str_targets -= str_exclusions
            ipset_targets -= ipset_exclusions

        return (str_targets, ipset_targets)

    @staticmethod
    def process_data_for_tasks_iterator(arguments):
        # removing the trailing slash if any
        if arguments.output and arguments.output[-1] == "/":
            arguments.output = arguments.output[:-1]

        ports = InputHelper._process_port(arguments.port) if arguments.port \
            else None

        real_ports = InputHelper._process_port(arguments.realport) if \
            arguments.realport else None

        str_targets, ipset_targets = InputHelper._process_targets(
            arguments=arguments,
        )
        targets_count = len(str_targets) + len(ipset_targets)

        if not targets_count:
            raise Exception("No target provided, or empty target list")

        if arguments.random:
            files = InputHelper._get_files_from_directory(arguments.random)
            random_file = choice(files)
        else:
            random_file = None

        tasks = list()
        if arguments.command:
            tasks.append(Task(arguments.command.rstrip('\n')))
        else:
            tasks = InputHelper._pre_process_commands(arguments.command_list)

        if arguments.proto:
            protocols = arguments.proto.split(",")
        else:
            protocols = None

        # Calculate the tasks count, as we will not have access to the len() of
        # the tasks iterator
        tasks_count = len(tasks) * targets_count
        if ports:
            tasks_count *= len(ports)
        if real_ports:
            tasks_count *= len(real_ports)
        if protocols:
            tasks_count *= len(protocols)

        return {
            "tasks": tasks,
            "str_targets": str_targets,
            "ipset_targets": ipset_targets,
            "ports": ports,
            "real_ports": real_ports,
            "random_file": random_file,
            "output": arguments.output,
            "protocols": protocols,
            "proxy_list": arguments.proxy_list,
            "tasks_count": tasks_count,
        }

    @staticmethod
    def make_tasks_generator_func(tasks_data):
        tasks_generator_func = functools.partial(
            InputHelper._replace_target_variables_in_commands,
            tasks=tasks_data["tasks"],
            str_targets=tasks_data["str_targets"],
            ipset_targets=tasks_data["ipset_targets"],
        )

        ports = tasks_data["ports"]
        if ports:
            tasks_generator_func = functools.partial(
                InputHelper._replace_variable_in_commands,
                tasks_generator_func=tasks_generator_func,
                variable="_port_",
                replacements=ports,
            )

        real_ports = tasks_data["real_ports"]
        if real_ports:
            tasks_generator_func = functools.partial(
                InputHelper._replace_variable_in_commands,
                tasks_generator_func=tasks_generator_func,
                variable="_realport_",
                replacements=real_ports,
            )

        random_file = tasks_data["random_file"]
        if random_file:
            tasks_generator_func = functools.partial(
                InputHelper._replace_variable_in_commands,
                tasks_generator_func=tasks_generator_func,
                variable="_random_",
                replacements=[random_file],
            )

        output = tasks_data["output"]
        if output:
            tasks_generator_func = functools.partial(
                InputHelper._replace_variable_in_commands,
                tasks_generator_func=tasks_generator_func,
                variable="_output_",
                replacements=[output],
            )

        protocols = tasks_data["protocols"]
        if protocols:
            tasks_generator_func = functools.partial(
                InputHelper._replace_variable_in_commands,
                tasks_generator_func=tasks_generator_func,
                variable="_proto_",
                replacements=protocols,
            )

        proxy_list = tasks_data["proxy_list"]
        if proxy_list:
            proxy_list_iterator = itertools.cycle(
                proxy for proxy in (
                    proxy.strip() for proxy in proxy_list
                ) if proxy
            )
            tasks_generator_func = functools.partial(
                InputHelper._replace_variable_array,
                tasks_generator_func=tasks_generator_func,
                variable="_proxy_",
                replacements_iterator=proxy_list_iterator,
            )

        return tasks_generator_func


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
            '-random', dest='random',
            help='Specify a directory of files that can be randomly used in commands as _random_',
            type=lambda x: InputHelper.check_path(parser, x)
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

        parser.add_argument(
            '--repeat', dest='repeat',
            help='repeat the given command x number of times.'
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
