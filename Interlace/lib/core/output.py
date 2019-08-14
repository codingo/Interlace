from enum import IntEnum
from time import localtime, strftime

from colorclass import Color
from colorclass import disable_all_colors

from Interlace.lib.core.__version__ import __version__


class OutputHelper(object):
    def __init__(self, arguments):
        if arguments.nocolor:
            disable_all_colors()

        self.verbose = arguments.verbose
        self.silent = arguments.silent
        self.seperator = "====================================================="

    def print_banner(self):
        if self.silent:
            return

        print(self.seperator)
        print("Interlace v%s\tby Michael Skelton (@codingo_)" % __version__)
        print("                  \t& Sajeeb Lohani (@sml555_)")
        print(self.seperator)

    def terminal(self, level, target, command, message=""):
        if level == 0 and not self.verbose:
            return

        formatting = {
            0: Color('{autoblue}[VERBOSE]{/autoblue}'),
            1: Color('{autogreen}[THREAD]{/autogreen}'),
            3: Color('{autobgyellow}{autored}[ERROR]{/autored}{/autobgyellow}')
        }

        leader = formatting.get(level, '[#]')

        format_args = {
           'time': strftime("%H:%M:%S", localtime()),
           'target': target,
           'command': command,
           'message': message,
            'leader': leader
        }

        if not self.silent:
            if level == 1:
                template = '[{time}] {leader} [{target}] {command} {message}'
            else:
                template = '[{time}] {leader} [{target}] {command} {message}'
            
            print(template.format(**format_args))


class Level(IntEnum):
    VERBOSE = 0
    THREAD = 1
    ERROR = 3
