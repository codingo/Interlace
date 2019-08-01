# Interlace
Easily turn single threaded command line applications into a fast, multi-threaded application with CIDR and glob support.

[![Python 3.2|3.6](https://img.shields.io/badge/python-3.2|3.6-green.svg)](https://www.python.org/) [![License](https://img.shields.io/badge/license-GPL3-_red.svg)](https://www.gnu.org/licenses/gpl-3.0.en.html) [![Twitter](https://img.shields.io/badge/twitter-@codingo__-blue.svg)](https://twitter.com/codingo_) [![Twitter](https://img.shields.io/badge/twitter-@sml555__-blue.svg)](https://twitter.com/sml555_) [![Rawsec's CyberSecurity Inventory](https://inventory.rawsec.ml/img/badges/Rawsec-inventoried-FF5050_flat.svg)](https://inventory.rawsec.ml/tools.html#Interlace)

# Reviews / Howto Guides
[Interlace: A Tool to Easily Automate and Multithread Your Pentesting & Bug Bounty Workflow Without Any Coding](https://medium.com/@hakluke/interlace-a-productivity-tool-for-pentesters-and-bug-hunters-automate-and-multithread-your-d18c81371d3d)

# Setup 
Install using:

```bash
$ python3 setup.py install
```
Dependencies will then be installed and Interlace will be added to your path as `interlace`.

# Usage

| Argument   | Description                                                                                                  |
|------------|--------------------------------------------------------------------------------------------------------------|
| (stdin)    | Pipe target lists from another application in comma-delimited format, CIDR notation, or as an individual host|
| -t         | Specify a target or domain name either in comma-delimited format, CIDR notation, or as an individual host    |
| -tL        | Specify a list of targets or domain names                                                                    |
| -e         | Specify a target exclusion either in comma-delimited format, CIDR notation, or as an individual host         |
| -eL        | Specify a list of targets to exclude                                                                         |
| -threads   | Specify the maximum number of threads to run at any one time (DEFAULT:5)                                     |
| -timeout   | Specify a timeout value in seconds for any single thread (DEFAULT:600)                                       |
| -c         | Specify a single command to execute over each target or domain                                               |
| -cL        | Specify a list of commands to execute over each target or domain                                             |
| -o         | Specify an output folder variable that can be used in commands as \_output\_                                 |
| -p         | Specify a list of port variable that can be used in commands as \_port\_. This can be a single port, a comma delimited list, or use dash notation |
| -pL        | Specify a list of proxies                                                                                    |
| --proto    | Specify protocols that can be used in commands as \_proto\_                                    |
| -rp        | Specify a real port variable that can be used in commands as \_realport\_                                    |
| --no-bar / --sober |  If set then progress bar be stripped out                                                             |
| --no-cidr  | If set then CIDR notation in a target file will not be automatically be expanded into individual hosts       |
| --no-color | If set then any foreground or background colours will be stripped out                                        |
| --silent   | If set then only important information will be displayed and banners and other information will be redacted |
| -v         | If set then verbose output will be displayed in the terminal                                                 |

## Further information regarding ports (-p)

| Example | Notation Type                                            |
|---------|----------------------------------------------------------|
| 80      | Single port                                              |
| 1-80    | Dash notation, perform a command for each port from 1-80 |
| 80,443  | Perform a command for both port 80, and port 443         |

## Further information regarding targets (-t or -tL)
Both `-t` and `-tL` will be processed the same. You can pass targets the same as you would when using nmap. This can be done using CIDR notation, dash notation, or a comma-delimited list of targets. A single target list file can also use different notation types per line.

Alternatively, you can pass targets in via stdin and neither -t or -tL will be required.

# Variable Replacements
The following variables will be replaced in commands at runtime:

| Variable  | Replacement                                                             |
|-----------|-------------------------------------------------------------------------|
| \_target\_  | Replaced with the expanded target list that the current thread is running against  |
| \_host\_ | Works the same as \_target\_, can be used interchangeably |
| \_output\_   | Replaced with the output folder variable from interlace              |
| \_port\_     | Replaced with the expanded port variable from interlace                       |
| \_realport\_ | Replaced with the real port variable from interlace                  |
| \_proxy\_    | Replaced with the proxy list from interlace |

# Usage Examples
## Run Nikto Over Multiple Sites
Let's assume that you have a file `targets.txt`  that has the following contents:

```
bugcrowd.com
hackerone.com
```
You could use interlace to run over any number of targets within this file using:
bash
```
➜  /tmp interlace -tL ./targets.txt -threads 5 -c "nikto --host _target_ > ./_target_-nikto.txt" -v
=========================================================================
Interlace v1.0	by Michael Skelton (@codingo_) & Sajeeb Lohani (@sml555_)
=========================================================================
[14:33:23] [THREAD] [nikto --host hackerone.com > ./hackerone.com-nikto.txt] Added to Queue 
[14:33:23] [THREAD] [nikto --host bugcrowd.com > ./bugcrowd.com-nikto.txt] Added to Queue 
```
This would run Nikto over each host and save to a file for each target. Note that in the above example since we're using the `>` operator, the results won't be fed back to the terminal; however this is desired functionality as otherwise we wouldn't be able to attribute which target Nikto results were returning for.

For applications where you desire feedback simply pass commands as you normally would (or use `tee`).

## Run Nikto Over Multiple Sites and Ports
Using the above example, let's assume you want independent scans to be run for both ports `80` and `443` for the same targets. You would then use the following:

```
➜  /tmp interlace -tL ./targets.txt -threads 5 -c "nikto --host _target_:_port_ > ./_target_-_port_-nikto.txt" -p 80,443 -v
=========================================================================
Interlace v1.0	by Michael Skelton (@codingo_) & Sajeeb Lohani (@sml555_)
=========================================================================
[14:33:23] [THREAD] [nikto --host hackerone.com:80 > ./hackerone.com-nikto.txt] Added to Queue 
[14:33:23] [THREAD] [nikto --host bugcrowd.com:80 > ./hackerone.com-nikto.txt] Added to Queue 
[14:33:23] [THREAD] [nikto --host bugcrowd.com:443 > ./bugcrowd.com-nikto.txt] Added to Queue 
[14:33:23] [THREAD] [nikto --host hackerone.com:443 > ./hackerone.com-nikto.txt] Added to Queue 
```
## Run a List of Commands against Target Hosts
Often with penetration tests there's a list of commands you want to run on nearly every job. Assuming that list includes testssl.sh, nikto, and sslscan, you could save a command list with the following in a file called `commands.txt`:

```
nikto --host _target_:_port_ > _output_/_target_-nikto.txt
sslscan _target_:_port_ >  _output_/_target_-sslscan.txt
testssl.sh _target_:_port_ > _output_/_target_-testssl.txt
```
If you were then given a target, `example.com` you could run each of these commands against this target using the following:
```bash
interlace -t example.com -o ~/Engagements/example/ -cL ./commands.txt -p 80,443
```
This would then run nikto, sslscan, and testssl.sh for both port 80 and 443 against example.com and save files into your engagements folder.

## CIDR notation with an application that doesn't support it
Interlace automatically expands CIDR notation when starting threads (unless the `--no-cidr` flag is passed). This allows you to pass CIDR notation to a variety of applications:

To run a virtual host scan against every target within `192.168.12.0/24` using a direct command you could use:
```bash
interlace -t 192.168.12.0/24 -c "vhostscan _target_ -oN _output_/_target_-vhosts.txt" -o ~/scans/ -threads 50
```
This is despite VHostScan not having any inbuilt CIDR notation support. Since Interlace expands the notation before building a queue of threads, VHostScan for all intents is only receiving a list of direct IP addresses to scan.

## Glob notation with an application that doesn't support it
Interlace automatically expands glob ranges when starting threads. This allows you to pass glob ranges to a variety of applications:

To run a virtual host scan against every target within `192.168.12.*` using a direct command you could use:
```bash
interlace -t 192.168.12.* -c "vhostscan _target_ -oN _output_/_target_-vhosts.txt" -o ~/scans/ -threads 50
```
Yet again, VHostScan does not have any inbuilt glob range format support.

## Dash (-) notation with an application that doesn't support it
Interlace automatically expands dash ranges when starting threads. This allows you to pass glob ranges to a variety of applications:

To run a virtual host scan against every target within `192.168.12.1-15` using a direct command you could use:
```bash
interlace -t 192.168.12.1-15 -c "vhostscan _target_ -oN _output_/_target_-vhosts.txt" -o ~/scans/ -threads 50
```
Yet again, VHostScan does not have any inbuilt dash range format support.


## Threading Support for an application that doesn't support it
Run a [virtual host scan](https://github.com/codingo/VHostScan) against each host in a file (`target-lst.txt`), whilst also limiting scans at any one time to 50 maximum threads.

This could be done using a direct command:
```bash
interlace -tL ./target-list.txt -c "vhostscan -t _target_ -oN _output_/_target_-vhosts.txt" -o ~/scans/ -threads 50
```

Or, alternatively, to run the same command as above, but using a command file, this would be done using:
```bash
interlace -cL ./vhosts-commands.txt -tL ./target-list.txt -threads 50 -o ~/scans
```
This presumes that the content of the command file is:
```
vhostscan -t $target -oN _output_/_target_-vhosts.txt
```
This would output a file for each target in the specified output folder. You could also run multiple commands simply by adding them into the command file.

## Exclusions
Interlace automatically excludes any hosts provided when specified via the `-e` or `-eL` arguments. These arguments are also compatible with the above-mentinoed range notations (CIDR, Glob, and dash)

To run a virtual host scan against every target within `192.168.12.0/24` despire targets within `192.168.12.0/26` using a direct command you could use:
```bash
interlace -t 192.168.12.0/24 -e 192.168.12.0/26 -c "vhostscan _target_ -oN _output_/_target_-vhosts.txt" -o ~/scans/ -threads 50
```

## Run Nikto Using Multiple Proxies
Using the above example, let's assume you want independent scans to be via different proxies for the same targets. You would then use the following:

```
➜  /tmp interlace -tL ./targets.txt -pL ./proxies.txt -threads 5 -c "nikto --host _target_:_port_ -useproxy _proxy_ > ./_target_-_port_-nikto.txt" -p 80,443 -v
```



# Authors and Thanks
Originally written by Michael Skelton ([codingo](https://twitter.com/codingo_)) and Sajeeb Lohani ([sml555](https://twitter.com/sml555_)) with help from Charelle Collett ([@Charcol0x89](https://twitter.com/Charcol0x89)) for threading refactoring and overall approach, and Luke Stephens ([hakluke](https://twitter.com/hakluke)) for testing and approach.

# Contributions
Contributions to this project are very welcome. If you're a newcomer to open source and would like some help in doing so, feel free to reach out to us on twitter ([@codingo_](https://twitter.com/codingo_)) / ([@sml555_](https://twitter.com/sml555_)) and we'll assist wherever we can.

