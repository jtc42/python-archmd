# Python-Arch.md

This utility generates an ARCHITECTURE.md file for your project by searching through your project directories for README files, combining them into a single overview of your project structure.

## Installation

`pipx install archmd`

## Basic usage

```none
Usage: archmd [OPTIONS] PATH

Arguments:
  PATH  Input directory  [required]

Options:
  --readme TEXT                   Readme file name  [default: README.md]
  --includeroot / --no-includeroot
                                  Include root readme in output  [default:
                                  False]

  --out TEXT                      Output file path. Outputs to stdout if
                                  empty.  [default: ]

  --title TEXT                    Output file title  [default: Project Root]

  --help                          Show this message and exit.
```
