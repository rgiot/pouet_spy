# Pouet spy

## Purpose

The aim of this tool is to automatically browse the <http://pouet.net> database to collect the new productions of
 your platforms of interest as well as the new comments and broken download links for productions of your groups of interest.
 It is usefull when you do not browse  pouet.net too much often.

The output is provided in an HTLM webpage automatically opened.

It's still work in progress. Feel free to send improvement patches.

## Usage

```
python.exe .\spy.py --help
usage: .\spy.py [-h] [-p [PLATFORM ...]] [-g [GROUP ...]]

Automatically browse pouet.net to collect the new productions of your platform of interest and the new comments for productions of your groups of interest. Usefull when you do     
not browse pouet.net too much often.

optional arguments:
  -h, --help            show this help message and exit
  -p [PLATFORM ...], --platform [PLATFORM ...]
                        Specify the name of the plateform for which you want to collect new prods (for example Amstrad CPC)
  -g [GROUP ...], --group [GROUP ...]
                        Specify the id of the group for which you want to collect the new comments(for example 253 for Benediction)

Still work in progress. Feel free to send improvement patches.
```