# Interlace
A threading management application that allows controlled execution of multiple commands, over multiple targets.

[![Python 3.2|3.6](https://img.shields.io/badge/python-3.2|3.6-green.svg)](https://www.python.org/) [![License](https://img.shields.io/badge/license-GPL3-_red.svg)](https://www.gnu.org/licenses/gpl-3.0.en.html) [![Build Status](https://travis-ci.org/codingo/Reconnoitre.svg?branch=master)](https://travis-ci.org/codingo/Reconnoitre) [![Twitter](https://img.shields.io/badge/twitter-@codingo__-blue.svg)](https://twitter.com/codingo_)

# Contributions
Contributions to this project are very welcome. If you're a newcomer to open source and would like some help in doing so, feel free to reach out to me on twitter ([@codingo_](https://twitter.com/codingo_)) and I'll assist wherever I can.

# Setup 
Install using:

```bash
$ python3 setup.py install
```
Dependencies will then be installed and Interlace will be added to your path as `interlace`.

# Usage

| Argument   | Description                                                                                                  |
|------------|--------------------------------------------------------------------------------------------------------------|
| -t         | Specify a target or domain name either in comma format, CIDR notation, or as an individual host.             |
| -tL        | Specify a list of targets or domain names                                                                    |
| -threads   | Specify the maximum number of threads to run at any one time (DEFAULT:5)                                     |
| -timeout   | Specify a timeout value in seconds for any one thread (DEFAULT:600)                                          |
| -c         | Specify a single command to execute over each target or domain                                               |
| -cL        | Specify a list of commands to execute over each target or domain                                             |
| -o         | Specify an output folder variable that can be used in commands as \_output\_                                 |
| -p         | Specify a list of port variablse that can be used in commands as \_port\_. This can be a single port, a comma delimeted list, or use dash notation |
| -rp        | Specify a real port variable that can be used in commands as \_realport\_                                    |
| --no-cidr  | If set then CIDR notation in a target file will not be automatically be expanded into individual hosts.      |
| --no-color | If set then any foreground or background colours will be stripped out                                        |
| --silent   | If set then only important information will be displayed and banners and other information will be redacted. |
| -v         | If set then verbose output will be displayed in the terminal                                                 |

## Further information regarding ports (-p)

| Example | Notation Type                                            |
|---------|----------------------------------------------------------|
| 80      | Single port                                              |
| 1-80    | Dash notation, perform a command for each port from 1-80 |
| 80,443  | Perform a command for both port 80, and port 443         |

## Further information regarding targets (-t or -tL)
Both `-t` and `-tL` will be processed the same. You can pass targets the same as you would when using nmap. This can be using CIDR notation, dash notatin, or a comma dilimited list of targets. A single target list file can also use different notation types per line.

# Variable Replacements
The following varaibles will be replaced in commands at runtime:

| Variable  | Replacement                                                             |
|-----------|-------------------------------------------------------------------------|
| \_target\_   | Replaced with the expanded target list that the current thread is running against  |
| \_output\_   | Replaced with the output folder variable from interlace              |
| \_port\_     | Replaced with the expanded port variable from interlace                       |
| \_realport\_ | Replaced with the real port variable from interlace                  |

# Usage Examples
## Run Nikto Over Multiple Sites
Let's assume that you had a file `targets.txt`  that had the following contents:

```
bugcrowd.com
hackerone.com
```
You could use interlace to run over any number of targets within this file using:
bash
```
➜  /tmp interlace -tL ./targets.txt -threads 5 -c "nikto --host _target_:_port_ > ./_target_-nikto.txt" -v
==============================================
Interlace v1.0	by Michael Skelton (@codingo_)
==============================================
[14:33:23] [INTERLACE] [nikto --host hackerone.com > ./hackerone.com-nikto.txt] Added to Queue 
[14:33:23] [INTERLACE] [nikto --host bugcrowd.com > ./bugcrowd.com-nikto.txt] Added to Queue 
```
This would run nikto over each host and save to a file for each target. Note that in the above example since we're using the `>` operator so results won't be fed back to the terminal, however this is desired functionality as otherwise we wouldn't be able to attribute which target Nikto results were returning for.

For applications where you desire feedback simply pass commands as you normally would (or use `tee`).

## Run Nikto Over Multiple Sites and Ports
Using the above example, let's assume you want independant scans to be run for both ports `80` and `443` for the same targets. You would then use the following:

```
➜  /tmp interlace -tL ./targets.txt -threads 5 -c "nikto --host _target_ > ./_target_-nikto.txt" -p 80,443 -v
==============================================
Interlace v1.0	by Michael Skelton (@codingo_)
==============================================
[14:33:23] [INTERLACE] [nikto --host hackerone.com:80 > ./hackerone.com-nikto.txt] Added to Queue 
[14:33:23] [INTERLACE] [nikto --host hackerone.com:80 > ./hackerone.com-nikto.txt] Added to Queue 
[14:33:23] [INTERLACE] [nikto --host bugcrowd.com:443 > ./bugcrowd.com-nikto.txt] Added to Queue 
[14:33:23] [INTERLACE] [nikto --host hackerone.com:443 > ./hackerone.com-nikto.txt] Added to Queue 
```

## CIDR notation with an application that doesn't support it
Interlace automatically expands CIDR notation when starting threads (unless the --no-cidr flag is passed). This allows you to pass CIDR notation to a variety of applications:

To run a virtual host scan against every target within 192.168.12.0/24 using a direct command you could use:
```bash
interlace -t 192.168.12.0/24 -c "vhostscan $target -oN $output/$target-vhosts.txt" -o ~/scans/ -threads 50
```
This is despite VHostScan not having any inbuilt CIDR notation support. Since Interlace expands the notation before building a queue of threads, VHostScan for all intents is only receiving a list of direct IP addresses to scan.

## Threading Support for an application that doesn't support it
Run a [virtual host scan](https://github.com/codingo/VHostScan) against each host in a file (target-lst.txt), whilst also limiting scans at any one time to 50 maximum threads.

This could be done using a direct command:
```bash
interlace -tL ./target-list.txt -c "vhostscan -t _target_ -oN _output_/_target_-vhosts.txt" -o ~/scans/ -threads 50
```

Or, alternatively, to run the same command as above, but using a command file, this would be done using:
```bash
interlace -cL ./vhosts-commands.txt -tL ./target-list.txt -threads 50 -o ~/scans
```
This presumes that the contents of the command file is:
```
vhostscan -t $target -oN _output_/_target_-vhosts.txt
```

This would output a file for each target in the specified output folder. You could also run multiple commands simply by adding them into the command file.
