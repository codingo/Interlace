# Interlace
A threading management application that allows controlled execution of multiple commands, over multiple targets.

[![Python 3.2|3.6](https://img.shields.io/badge/python-3.2|3.6-green.svg)](https://www.python.org/) [![License](https://img.shields.io/badge/license-GPL3-_red.svg)](https://www.gnu.org/licenses/gpl-3.0.en.html) [![Build Status](https://travis-ci.org/codingo/Reconnoitre.svg?branch=master)](https://travis-ci.org/codingo/Reconnoitre) [![Twitter](https://img.shields.io/badge/twitter-@codingo__-blue.svg)](https://twitter.com/codingo_)

# Usage

| Argument   | Description                                                                                                  |
|------------|--------------------------------------------------------------------------------------------------------------|
| -t         | Specify a target or domain name                                                                              |
| -tL        | Specify a list of targets or domain names                                                                    |
| -threads   | Specify the maximum number of threads to run at any one time (DEFAULT:5)                                     |
| -timeout   | Specify a timeout value in seconds for any one thread (DEFAULT:600)                                          |
| -c         | Specify a single command to execute over each target or domain                                               |
| -cL        | Specify a list of commands to execute over each target or domain                                             |
| -o         | Specify an output folder variable that can be used in commands                                               |
| -p         | Specify a port variable that can be used in commands                                                         |
| -rp        | Specify a real port variable that can be used in commands                                                    |
| --no-cidr  | If set then CIDR notation in a target file will not be automatically be expanded into individual hosts.      |
| --no-color | If set then any foreground or background colours will be stripped out                                        |
| --silent   | If set then only important information will be displayed and banners and other information will be redacted. |
| -v         | If set then verbose output will be displayed in the terminal                                                 |


# Variable Replacements
The following varaibles will be replaced in commands at runtime:

| Variable  | Replacement                                                         |
|-----------|---------------------------------------------------------------------|
| $target   | Replaced with the target that the current thread is running against |
| $output   | Replaced with the output folder variable from interlace             |
| $port     | Replaced with the port variable from interlace                      |
| $realport | Replaced with the real port variable from interlace                 |

# Usage Examples
## Max Virtual Host Scanning Example
Run a [virtual host scan](https://github.com/codingo/VHostScan) against each host in a file (target-lst.txt), whilst also limiting scans at any one time to 50 maximum threads:
### Example 1 - direct command
```bash
interlace -tL ./target-list.txt -c "vhostscan -t $target -oN $output/$target-vhosts.txt" -o ~/Bounties/Targets/ -threads 50
```
### Example 2- command file
To run the same command as above, but using a command file, this would be done using:
```bash
interlace -cL ./vhosts-commands.txt -tL ./target-list.txt -threads 50 -o ~/Bounties/Targets/
```
This presumes that the contents of the command file is:
```
vhostscan -t $target -oN $output/$target-vhosts.txt
```

This would output a file for each target in the specified output folder.
