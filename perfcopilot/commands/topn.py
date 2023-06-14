import argparse
import sys

from perfcopilot.llm import print_streamed_llm_response, chat


command = "topn"
help = "Summarise Top-N output from a profiler and suggest improvements"


def add_to_command_parser(subparsers):
    parser = subparsers.add_parser(command, help=help)
    parser.add_argument(
        'infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
        help="The file containing the Top N. Defaults to stdin.")


prompt = """You are assisting me with understanding the top most expensive functions found by a
software profiler. I will provide you a list of the most expensive
functions, the amount of CPU time spent in each, and the software libraries or programs that each
function is in. If the first line of the input starts with a # then that line is a header, which
describes the format of the following lines.

For each program or library in the input you must produce a report that looks as follows (you will
generate the content in between angular <> brackets). First give a brief, technical explanation of
each library or program and its common use cases. For each function in each library, also give a
brief explanation of its purpose. Group the explanation of the functions in a library or program
together. The format should look like this:

Begin format example.

# <insert program/library name>
<Insert brief technical description of the program/library and its primary use cases>

The functions executed in <insert program/library name> were:
* <insert first function>
* <insert second function>
... etc

End format example.

Then for each library,  suggest ways to optimize or improve the system to make it more
efficient given that this library and its functions are consuming significant CPU resources.

Types of improvements that would be useful to me are improvements that result in:

- Higher performance so that the system runs faster or uses less CPU
- Better memory efficient so that the system uses less RAM
- Better storage efficient so that the system stores less data on disk.
- Better network I/O efficiency so that less data is sent over the network
- Better disk I/O efficiency so that less data is read and written from disk

The format should look like this:

Begin format example.

Here are some suggestions as to how you might optimize your system if the above functions
in <insert program/library name> are consuming significant CPU resources:

## Problem 1: <insert potential problem description>

Observation: <insert what observation you have made about the data that suggests the problem exists>

The following optimisations may help resolve this problem:
Optimisation 1: <insert a description of a change the user could make to remedy the problem>
Expected outcome 1: <insert a description of the the outcome the user should expect to see in their
system as a result of the change>

Optimisation 2: <insert a description of a change the user could make to remedy the problem>
Expected outcome 2: <insert a description of the the outcome the user should expect to see in their
system as a result of the change>

Optimisation 3: <insert a description of a change the user could make to remedy the problem>
Expected outcome 3: <insert a description of the the outcome the user should expect to see in their
system as a result of the change>

... etc.

End format example.

You may identify as many problems per program/library as you want. You can make a maximum of three
optimisation suggestions per problem. If you cannot see any problems based on the functions executed
in a particular program/library then say "No problems identified." instead of listing problems.
If you do not know of any way in which to improve the performance, then say "None available" in
the optimisation suggestions section.

Your optimisation suggestions must meet all of the following criteria:
1. Your suggestions should detailed, accurate, actionable, technical, and include concrete examples.
2. If you suggest replacing the function or library with a more efficient replacement you must
suggest at least one concrete replacement.
3. If you suggest making code changes, then show a code snippet as an example of what you mean,
and explain why it is helpful.
4. Do not suggest making changes to functions that are in large public libraries, like libc, or
the Linux kernel.

Do not suggest to use a CPU profiler or to profile the code. You should favour stopping making
suggestions over suggesting profiling the code with a CPU profiler.

This is an example (you must not tell me to refer to this example in your output):

Example input:
# Index | Process/Library | Function | File | Self CPU | Self+Children CPU
1 | libc.so.6 | __random | ./stdlib/random.c#295 | 2.43% | 2.79%
2 | python | _PyEval_EvalFrameDefault | Python/bytecodes.c#2643 | 1.72% | 32.87%
3 | python | gc_collect_main | Modules/gcmodule.c#1303 | 1.54% | 4.58%
4 | libc.so.6 | _int_malloc | ./malloc/malloc.c#4299 | 0.68% | 0.96%
5 | python | visit_decref | Modules/gcmodule.c#465 | 0.66% | 0.68%

Example output:
# libc.so.6

libc.so.6 is the GNU C Library (glibc) is a core library for the C programming language, providing basic functionality
and system calls.

The functions executed in libc.so.6 were:
   * __random: Generates a random number.
   * _int_malloc: Internal memory allocation function in glibc.

Here are some suggestions as to how you might optimize your system if the above functions in libc.so.6 are
consuming significant CPU resources:

## Problem 1: You are using a potentially inefficient random number generator

Observation: The presence of the __random function in libc.so.6 indicates you are generating random numbers
using the default libc random number generator.

Optimisation: If the random function is a performance bottleneck, consider using a faster
random number generator, such as the xorshift family of algorithms. For example, you could use the xoroshiro128+ or
xorshift128+ algorithms, which are known for their speed and good statistical properties. Implement these algorithms
in your code and replace calls to the random function with calls to your new generator.

Expected outcome: By using a more efficient random number generator the amount of time spent generating
random numbers should decrease.

## Problem 2: You are using a potentially inefficient memory allocator

Observation: The presence of the _int_malloc function in libc.so.6 indicates that you are using the default
libc memory allocator.

Optimisation: Replace the default malloc with a more efficient memory allocator, such as jemalloc or tcmalloc.
These allocators are designed to reduce fragmentation and improve performance in multi-threaded
applications. To use jemalloc, for example, you can link your program with the jemalloc library by
adding `-ljemalloc` to your linker flags.

Expected outcome: By using a more efficicient memory allocator the amount of time spent on memory management
should decrease.

# python

python is the Python interpreter, which executes Python scripts.

The functions executed in python were:

   * _PyEval_EvalFrameDefault: The main interpreter loop for executing Python bytecode.
   * gc_collect_main: The main garbage collection function in Python, responsible for collecting and freeing memory
   from unused objects.
   * visit_decref: A function used during garbage collection to decrease the reference count of an object.

Here are some suggestions as to how you might optimize your system if the above functions in python are
consuming significant CPU resources:

## Problem 1: You are spending significant time performing garbage collection

Observation: The presence of the gc_collect_main and visit_decref functions indicate that
you are spending a significant amount of time performing garbage collection in the python interpreter.

Optimisation 1: Reducing the number of objects created in your program can help reduce the
workload of the garbage collector. This can be achieved by reusing objects, using object pools, or employing data
structures that create fewer temporary objects.

Expected outcome 1: By reducing the number of objects created by your program you should reduce the amount of
work that the garbage collector has to do.

Optimisation 2: Tune Python garbage collection parameters: Python's garbage collector has several tunable parameters,
such as `gc.set_threshold()` and `gc.set_debug()`. Adjusting these parameters can help you find a balance between
garbage collection frequency and CPU usage. For example, you can increase the threshold to reduce the frequency
of garbage collection, which may result in less CPU usage but higher memory consumption.

Expected outcome 2: By reducing the garbage collection frequency you may reduce the CPU usage of your program.

End of example.

This is the list of most expensive functions and the libraries they are in. Please produce a report
with the same format as described above.

{topn}

Your report must not tell me to refer to the example provided above. I will not have access to the example
above when reading the report you produce. You should repeat content if necessary. Do not tell me to refer
to another part of your report instead of repeating content.
"""


def run(args_parser, args):
    topn = args.infile.read()
    if args.echo_input:
        print(topn)

    conversation = print_streamed_llm_response(prompt.format(topn=topn))
    if args.chat:
        chat(conversation)

    return 0
