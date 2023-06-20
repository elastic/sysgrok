```
                  __                       _ _       _
                 / _|                     (_) |     | |
 _ __   ___ _ __| |_ ______ ___ ___  _ __  _| | ___ | |_
| '_ \ / _ \ '__|  _|______/ __/ _ \| '_ \| | |/ _ \| __|
| |_) |  __/ |  | |       | (_| (_) | |_) | | | (_) | |_
| .__/ \___|_|  |_|        \___\___/| .__/|_|_|\___/ \__|
| |                                 | |
|_|                                 |_|

Performance analysis and optimisation with LLMs

Contact: sean.heelan@elastic.co
```

`perf-copilot` is an experimental proof-of-concept, intended to demonstrate how
LLMs can be used to help SWEs and SREs to optimise the performance of their systems
and resolve stability and reliability problems.

It can do things like:

* Take the top most expensive functions and processes identified by a profiler, explain
the functionality that each provides, and suggest optimisations.
* Take a host and a description of a problem that host is encountering and automatically
debug the issue and suggest remediations.
* Take source code that has been annotated by a profiler, explain the hot paths, and
suggest ways to improve the performance of the code.

See the Command Overview section below for an overview of the full list of available
commands that it supports.

Here's an example using the `analyzecmd` sub-command, which connects to a remote host,
executes one or more commands, and summarises the result. The demo shows how this can be
used to automate the process described in Brendan Gregg's article -
[Linux Performance Analysis in 60 seconds](https://www.brendangregg.com/Articles/Netflix_Linux_Perf_Analysis_60s.pdf).

[![asciicast](https://asciinema.org/a/cIg4I8XjSwnJfQnLgYnambdRC.svg)](https://asciinema.org/a/cIg4I8XjSwnJfQnLgYnambdRC)

# Installation

1. Copy `.env.example` to `.env` and fill the required variables. The `GAI_API_TYPE` must be either "azure" or "openai",
and the `GAI_API_KEY` must be your API key. If you are using an Azure endpoint then you must also provide the
`GAI_API_BASE` and `GAI_API_VERSION` variables. The correct values for these can be found in your Azure portal.

2. Install requirements via pip

```
$ python -m venv venv # Create a virtual environment
$ source venv/bin/activate # Activate the virtual environment
$ pip install -r requirements.txt # Install requirements in the virtual environment
```

# Usage

For now, `perf-copilot` is a command line tool and takes input either via stdin
or from a file, depending on the command. Usage is as follows:

```
usage: ./perf-copilot.py [-h] [-d] [-e] [-c] [--output-format OUTPUT_FORMAT] [-m MODEL] [--temperature TEMPERATURE] [--max-concurrent-queries MAX_CONCURRENT_QUERIES]
                         {analyzecmd,code,explainfunction,explainprocess,debughost,findfaster,stacktrace,topn} ...

                  __                       _ _       _
                 / _|                     (_) |     | |
 _ __   ___ _ __| |_ ______ ___ ___  _ __  _| | ___ | |_
| '_ \ / _ \ '__|  _|______/ __/ _ \| '_ \| | |/ _ \| __|
| |_) |  __/ |  | |       | (_| (_) | |_) | | | (_) | |_
| .__/ \___|_|  |_|        \___\___/| .__/|_|_|\___/ \__|
| |                                 | |
|_|                                 |_|

Performance analysis and optimisation with LLMs

positional arguments:
  {analyzecmd,code,explainfunction,explainprocess,debughost,findfaster,stacktrace,topn}
                        The sub-command to execute
    analyzecmd          Summarise the output of a command, optionally with respect to a problem under investigation
    code                Summarise profiler-annoted code and suggest optimisations
    explainfunction     Explain what a function does and suggest optimisations
    explainprocess      Explain what a process does and suggest optimisations
    debughost           Debug an issue by executing CLI tools and interpreting the output
    findfaster          Search for faster alternatives to a provided library or program
    stacktrace          Summarise a stack trace and suggest changes to optimise the software
    topn                Summarise Top-N output from a profiler and suggest improvements

options:
  -h, --help            show this help message and exit
  -d, --debug           Debug output
  -e, --echo-input      Echo the input provided to perf-copilot. Useful when input is piped in and you want to see what it is
  -c, --chat            Enable interactive chat after each LLM response
  --output-format OUTPUT_FORMAT
                        Specify the output format for the LLM to use
  -m MODEL, --model-or-deployment-id MODEL
                        The OpenAI model, or Azure deployment ID, to use.
  --temperature TEMPERATURE
                        ChatGPT temperature. See OpenAI docs.
  --max-concurrent-queries MAX_CONCURRENT_QUERIES
                        Maximum number of parallel queries to OpenAI
```

# Feature Requests, Bugs and Suggestions

Please log them via the Github Issues tab. If you have specific requests or bugs
then great, but I'm also happy to discuss open-ended topics, future work, and
ideas.

# Adding a New Command

Adding a new command is easy. You need to:
1. Create a file, yourcommand.py, in the `perfcopilot/commands` directory. It's
likely easiest to just copy an existing command, e.g. `stacktrace.py`
2. Your command file needs to have the following components:
    * A top level `command` variable which is the name users will use to invoke
    your command
    * A top level `help` variable describing the command, and which will appear
    when the `-h` flag is passed.
    * A `add_to_command_subparsers` function which should add a sub-parser
    which will handle the command line arguments that are specific to your
    command.
    * A `run` function that is the interface to your command. It will be the
    function that creates the LLM queries and produces a result. It should
    return 0 upon success, or -1 otherwise.
3. Update `perf-copilot.py`:
    * Add your command to the imports
    * Add your command to the `commands` dict.

# Examples

Note 1: The output of `perf-copilot` is heavily dependent on the input prompts, and
I am still experimenting with them. This means that the output you get from
running `perf-copilot` may differ from what you see below. It may also vary based
on minor differences in your input format, or the usual quirks of LLMs. If you
have an example where the output you get from a command is incorrect or
otherwise not helpful, please file an issue and let me know. If I can figure out
how to get `perf-copilot` to act more usefully, I will.

Note 2: The output of `perf-copilot` is also heavily dependent on the OpenAI model
used. The default is `gpt-3.5-turbo` and these examples have been generated
using that. See the usage docs for other options. If the results you get are not
good enough with `gpt-3.5-turbo` then try `gpt-4`. It is slower and more
expensive but may provide higher quality output.

## Finding faster replacement programs and libraries

One of the easiest wins in optimisation is replacing an existing library with
a functionally equivalent, faster, alternative. Usually this process begins
with an engineering looking at the Top-N output of their profiler, which lists
the most expensive libraries and functions in their system, and then going on
a hunt for an optimised version. The `findfaster` command solves this problem
for you. Here are some examples.

[![asciicast](https://asciinema.org/a/SikklBJXeLOISK0Fwz3eyFENT.svg)](https://asciinema.org/a/SikklBJXeLOISK0Fwz3eyFENT)

## Analysing the TopN functions and suggesting optimisations

A good starting place for analysing a system is often looking at what libraries
and functions your profiler tells you are using the most CPU. Most commercial
profilers will have a tab for this information, and you can get it from `perf`
via `perf report --stdio --max-stack=0`. One of the stumbling blocks when
encountering this data is that firstly you need to understand what each
program, library and function actually is, and then you need to come up with
ideas for how to optimise them. This is made even more complicated in the
world of whole-system, or whole-data-center, profiling, where there are a
huge number of programs and libraries running, and you are often unfamiliar
with many of them.

The `perf-copilot topn` command helps with this. Provide it with your Top-N, and
it will try to summarise what each program, library and function is doing, as
well as providing you with some suggestions as to what you might do to
optimise your system.

[![asciicast](https://asciinema.org/a/Iv4NYKpbcccHx742kY1FMfbap.svg)](https://asciinema.org/a/Iv4NYKpbcccHx742kY1FMfbap)

## Explaining a specific function and suggesting optimisations

If you know a particular function is using signficant CPU then, using the
`explainfunction` command, you can ask for an explanation of that
specific function, and for optimistion suggestions, instead of asking about
the entire Top N.

[![asciicast](https://asciinema.org/a/lErwolZTG21bgxGPYiXgSwab1.svg)](https://asciinema.org/a/lErwolZTG21bgxGPYiXgSwab1)

## Analysing command output, diagnosing issues, and suggesting remdiations

The `analyzecmd` command takes a host and one or more Linux commands to execute.
It connects to the host, executes the commands and summarises the results. You can
also provide it with an optional description of an issue you are investigating, and
the command output will be summarised with respect to that problem.

This first example shows how one or more commands can be executed.

[![asciicast](https://asciinema.org/a/SHGe9XQnehXmKAsstVMnbEUAz.svg)](https://asciinema.org/a/SHGe9XQnehXmKAsstVMnbEUAz)

We can also use `analyzecmd` to analyse commands that produce logs.

[![asciicast](https://asciinema.org/a/ILYKfhfmHq6qFgmx5h8gTqTCr.svg)](https://asciinema.org/a/ILYKfhfmHq6qFgmx5h8gTqTCr)

And in this final example we execute and analyze the commands recommended by
Brendan Gregg  in his article "Linux Performance Analysis in 60 seconds".

[![asciicast](https://asciinema.org/a/cIg4I8XjSwnJfQnLgYnambdRC.svg)](https://asciinema.org/a/cIg4I8XjSwnJfQnLgYnambdRC)