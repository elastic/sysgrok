import argparse
import sys

import openai

from .shared import get_base_messages

command = "topn"
help = "Summarise Top-N output from a profiler and suggest improvements"


def add_to_command_parser(subparsers):
    parser = subparsers.add_parser(command, help=help)
    parser.add_argument(
        'infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
        help="The file containing the Top N. Defaults to stdin.")


prompt = """You are assisting me with understanding the top most expensive functions found by a
software profiler, such as pprof or perf record. I will provide you an ordered list of the most expensive
functions, the amount of CPU time spent in each, and the software libraries or programs that each
function is in. If the first line of the input starts with a # then that line is a header, which
describes the format of the following lines.

Your task is to brief, technical explanation of each library or program and its common
use cases. For each function in each library, also give a brief explanation of its purpose. Group
the explanation of the functions in a library or program together. For each library, then suggest
ways to optimize or improve the system to make it more efficient given that this library and its
functions are consuming significant CPU resources.

Types of improvements that would be useful to me are improvements that result in:

- Higher performance so that the system runs faster or uses less CPU
- Better memory efficient so that the system uses less RAM
- Better storage efficient so that the system stores less data on disk.
- Better network I/O efficiency so that less data is sent over the network
- Better disk I/O efficiency so that less data is read and written from disk

Make a maximum of three suggestions per library or program. Favour providing a small number of
accurate, concise, concrete, technically correct and actionable suggestions, over a larger number
of ones that do not have these properties. If you do not know of any way in which to improve the
performance then say "None available" in the optimisation suggestions section for that library.

Your suggestions must meet all of the following criteria:
1. Your suggestions should detailed, accurate, technical and include concrete examples.
2. Your suggestions should be specific to the provided input data. For each library, when making
optimisation suggestions they must be specific to that library and the functions that were
executed in it. Do not make generic suggestions.
3. If you suggest replacing the function or library with a more efficient replacement you must
suggest at least one concrete replacement.
4. If you suggest making code changes, then show a code snippet as an example of what you mean,
and explain why it is helpful.
5. Do not suggest making changes to functions that are in large public libraries, like libc, or
the Linux kernel.

Do not suggest to use a CPU profiler or to profile the code. I have already profiled the code
using a CPU profiler. You should favour stopping making suggestions over suggesting profiling
the code with a CPU profiler.

This is an example:

Input:
# Index | Process/Library | Function | File | Self CPU | Self+Children CPU
1 | sha1sum | sha1_process_block | lib/sha1.c#436 | 3.18% | 3.18%
2 | libc.so.6 | __random | ./stdlib/random.c#295 | 2.43% | 2.79%
3 | python | _PyEval_EvalFrameDefault | Python/bytecodes.c#2643 | 1.72% | 32.87%
4 | python | gc_collect_main | Modules/gcmodule.c#1303 | 1.54% | 4.58%
5 | python | _PyEval_EvalFrameDefault | Python/generated_cases.c.h#3539 | 0.95% | 2.55%
6 | vmlinux | clear_page_erms |  | 0.78% | 0.78%
7 | libc.so.6 | _int_malloc | ./malloc/malloc.c#4299 | 0.68% | 0.96%
8 | python | visit_decref | Modules/gcmodule.c#465 | 0.66% | 0.68%
9 | python | deduce_unreachable | ../Modules/gcmodule.c#1143 | 0.64% | 1.72%
10 | vmlinux | copy_user_enhanced_fast_string |  | 0.42% | 1.55%

Output:
sha1sum
========
sha1sum is a command-line utility for computing and verifying SHA-1 hashes. It is commonly used for verifying file
integrity.

The functions executed in sha1sum here:
   * sha1_process_block: Processes a block of data and updates the SHA-1 hash state.

Optimisation Suggestions
------------------------

1. Consider using a more modern and efficient hashing algorithm like SHA-256 or SHA-3. These algorithms provide better
security and may have better performance characteristics. For example, you could use the OpenSSL library, which
provides implementations of various hashing algorithms, including SHA-256 and SHA-3.

libc.so.6
=========

libc.so.6 is the GNU C Library (glibc) is a core library for the C programming language, providing basic functionality
and system calls.

The functions executed in libc.so.6 were:
   * __random: Generates a random number.
   * _int_malloc: Internal memory allocation function in glibc.

Optimisation Suggestions
------------------------

1. Use a faster random number generator: If the random function is a performance bottleneck, consider using a faster
random number generator, such as the xorshift family of algorithms. For example, you could use the xoroshiro128+ or
xorshift128+ algorithms, which are known for their speed and good statistical properties. Implement these algorithms
in your code and replace calls to the random function with calls to your new generator.

2. Use a custom memory allocator: Replace the default malloc with a more efficient memory allocator, such as
jemalloc or tcmalloc. These allocators are designed to reduce fragmentation and improve performance in multi-threaded
applications. To use jemalloc, for example, you can link your program with the jemalloc library by adding `-ljemalloc`
to your linker flags.

python
======

python is the Python interpreter, which executes Python scripts.

The functions executed in python were:

   * _PyEval_EvalFrameDefault: The main interpreter loop for executing Python bytecode.
   * gc_collect_main: The main garbage collection function in Python, responsible for collecting and freeing memory
   from unused objects.
   * visit_decref: A function used during garbage collection to decrease the reference count of an object.
   * deduce_unreachable: A function used during garbage collection to identify unreachable objects.

Optimisation Suggestions
------------------------

1. Minimize Python object creation: Reducing the number of objects created in your program can help reduce the
workload of the garbage collector. This can be achieved by reusing objects, using object pools, or employing data
structures that create fewer temporary objects.

2. Tune Python garbage collection parameters: Python's garbage collector has several tunable parameters,
such as `gc.set_threshold()` and `gc.set_debug()`. Adjusting these parameters can help you find a balance between
garbage collection frequency and CPU usage. For example, you can increase the threshold to reduce the frequency
of garbage collection, which may result in less CPU usage but higher memory consumption.

vmlinux
=======
vmlinux is the Linux kernel.

The functions executed in vmlinux were:
   * copy_user_enhanced_fast_string: A kernel function that copies data between user space and kernel space
   using the Enhanced REP MOVSB/STOSB (ERMS) feature.
   * clear_page_erms: A kernel function that clears a memory page using the Enhanced REP MOVSB/STOSB (ERMS)
   feature.

Optimisation Suggestions
------------------------
1. Optimize data copying: If your application frequently copies data between user space and kernel space,
consider optimizing the data structures and algorithms to minimize the amount of data that needs to be copied.

2. Use zero-copy techniques: If possible, use zero-copy techniques, such as the `splice()` system call or
memory-mapped files, to avoid unnecessary data copying between user space and kernel space.

End of example.

This is the list of most expensive functions and the libraries they are in.

{topn}
"""


def run(args_parser, args):
    topn = args.infile.read()
    if args.echo_input:
        print(topn)

    messages = get_base_messages(args)
    messages.append({
        "role": "user",
        "content": prompt.format(topn=topn)
    })

    completion = openai.ChatCompletion.create(
        model=args.model,
        temperature=args.temperature,
        stream=True,
        messages=messages
    )

    wrote_reply = False
    for chunk in completion:
        delta = chunk["choices"][0]["delta"]
        if "content" not in delta:
            continue
        sys.stdout.write((delta["content"]))
        wrote_reply = True

    if wrote_reply:
        sys.stdout.write("\n")
    return 0
