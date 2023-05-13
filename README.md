```
                  __                   _
 _ __   ___ _ __ / _|       __ _ _ __ | |_
| '_ \ / _ \ '__| |_ _____ / _` | '_ \| __|
| |_) |  __/ |  |  _|_____| (_| | |_) | |_
| .__/ \___|_|  |_|        \__, | .__/ \__|
|_|                        |___/|_|

Performance analysis and optimisation with LLMs
```

`perf-gpt` is an experimental proof-of-concept, intended to demonstrate how
LLMs can be used to understand profiling data, and assist users in coming up
with ways to resolve performance and stability issues in their systems. The
hypothesis being tested by `perf-gpt` is that LLMs can be used to make users
of profiling tools more efficient at understanding their profiler output, and
more effective in coming up with practical solutions to problems they
encounter.

# Installation

1. Create a `.env` file containing your OpenAPI key, e.g.

```
OPEN_API_KEY="..."
```

2. Install requirements via pip

```
$ python -m venv venv # Create a virtual environment
$ source venv/bin/activate # Activate the virtual environment
$ pip install -r requirements.txt # Install requirements in the virtual environment
```

# Feature requests, bugs and suggestions

Please log them via the Github Issues tab. If you have specific requests or bugs
then great, but I'm also happy to discuss open-ended topics, future work, and
ideas.

# Usage

For now, `perf-gpt` is a command line tool and takes input from profiling tools
either via stdin or from a file. Usage is as follows:

```
usage: ./perf-gpt.py [-h] [-v] [-d] [-e] [-m MODEL] [--temperature TEMPERATURE] {code,findfaster,stacktrace,topn} ...

                  __                   _
 _ __   ___ _ __ / _|       __ _ _ __ | |_
| '_ \ / _ \ '__| |_ _____ / _` | '_ \| __|
| |_) |  __/ |  |  _|_____| (_| | |_) | |_
| .__/ \___|_|  |_|        \__, | .__/ \__|
|_|                        |___/|_|

Performance analysis and optimisation with LLMs

positional arguments:
  {code,findfaster,stacktrace,topn}
                        The sub-command to execute
    code                Summarise profiler-annoted code and suggest optimisations
    findfaster          Search for faster alternatives to a provided library or program
    stacktrace          Summarise a stack trace and suggest changes to optimise the software
    topn                Summarise Top-N output from a profiler and suggest improvements

options:
  -h, --help            show this help message and exit
  -v, --verbose         Verbose output
  -d, --debug           Debug output
  -e, --echo-input      Echo the input provided to perf-gpt. Useful when input is piped in and you want to see what it is
  -m MODEL, --model MODEL
                        The OpenAI model to use. Must be one of the chat completion models.
                        See https://platform.openai.com/docs/models/model-endpoint-compatibility for valid options
  --temperature TEMPERATURE
                        ChatGPT temperature. See OpenAI docs.
```

# Examples

The following has some examples of how to use `perf-gpt` to solve common
problems that come up when profiling and optimising a system. Across all
commands, the purpose of `perf-gpt` is two fold: firstly, help you understand
your profiling data, and secondly help you come up with ideas for optimising
your system.

Note 1: The output of `perf-gpt` is heavily dependent on the input prompts, and
I am still experimenting with them. This means that the output you get from
running `perf-gpt` may differ from what you see below. It may also vary based
on minor differences in your input format, or the usual quirks of LLMs. If you
have an example where the output you get from a command is incorrect or
otherwise not helpful, please file an issue and let me know. If I can figure out
how to get `perf-gpt` to act more usefully, I will.

Note 2: The output of `perf-gpt` is also heavily dependent on the OpenAI model
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

### Finding a faster replacement for gzip

```
./perf-gpt.py findfaster gzip
gzip is a file compression utility that uses the DEFLATE algorithm. It is
widely used and supported on most platforms. However, it is not the fastest
or most memory-efficient compression library available.

Here are three libraries that are confirmed to be faster and more
memory-efficient than gzip:

1. Zstandard (zstd): Zstandard is a modern compression library that provides
high compression ratios and fast decompression speeds. It is optimized for
modern CPUs and supports SIMD instructions. Zstandard is designed to be a
drop-in replacement for gzip and can be used with existing tools and
applications.

2. LZ4: LZ4 is a compression library that provides fast compression and
decompression speeds. It is optimized for speed and uses a simple compression
algorithm that is easy to implement. LZ4 is designed to be a drop-in
replacement for gzip and can be used with existing tools and applications.

3. Brotli: Brotli is a compression library that provides high compression
ratios and fast decompression speeds. It is optimized for modern CPUs and
supports SIMD instructions. Brotli is designed to be a drop-in replacement
for gzip and can be used with existing tools and applications. Brotli is
used by popular web browsers such as Chrome and Firefox to compress web
content.
```

### Finding a faster replacement for Python's JSON library

```
$ perf-gpt.py findfaster "python json"
Python json is a built-in module that provides methods for encoding and
decoding JSON data. It is a widely used library for working with JSON data
in Python. However, it may not be the most performant or memory-efficient
option for large datasets.

Here are some suggested libraries that can be used as alternatives to python
json for high performance and scalability:

1. ujson: This library is a drop-in replacement for python json and is written
in C. It is highly optimized for speed and memory efficiency, and can be up to
10 times faster than python json. It also supports encoding and decoding of
custom Python objects.

2. rapidjson: This library is a Python wrapper for the C++ rapidjson library.
It is designed for high performance and supports SIMD instructions for faster
processing. It also provides a simple API for encoding and decoding JSON data.

3. orjson: This library is a fast, pure Python JSON library that is optimized
for speed and memory efficiency. It is up to 20 times faster than python json
and supports encoding and decoding of custom Python objects.

4. simdjson: This library is written in C++ and provides a Python wrapper for
SIMD-accelerated JSON parsing. It is designed for high performance and can be
up to 4 times faster than other JSON libraries. It also supports streaming and
incremental parsing of large JSON files.
```

## Explaining a stack trace and suggesting optimisations

Working with CPU profilers involves a lot of time looking at stack traces,
trying to understand them, and then trying to deduce ways to optimise the
software based on that understanding. The `stacktrace` command helps with
this. It will provide you with an example of the important functions in a
stack trace, and then make some suggestions as to things you may be able
to do to optimise your software. The `stacktrace` command is fairly
resilient to variations in the format of the stacktrace provided, so in
theory you should be able to just copy/paste in data from your profiler
of choice.

In this first example we copy and paste a stacktrace directly from the
Elastic Universal Profiler UI.

```
$ perf-gpt.py stacktrace
vmlinux: copy_user_enhanced_fast_string
vmlinux+0xa1fc2d
18
vmlinux: copy_page_to_iter
vmlinux+0x50fd62
17
vmlinux: generic_file_read_iter
vmlinux+0x211f8e
16
vmlinux: ext4_file_read_iter
vmlinux+0x386215
15
vmlinux: new_sync_read
vmlinux+0x2c4e51
14
vmlinux: __vfs_read
vmlinux+0x2c8008
13
vmlinux: vfs_read
vmlinux+0x2c80ad
12
vmlinux: ksys_read
vmlinux+0x2c8246
11
vmlinux: __x64_sys_read
vmlinux+0x2c8299
10
vmlinux: do_syscall_64
vmlinux+0x272d
9
vmlinux: entry_SYSCALL_64_after_hwframe
vmlinux+0xc0008b

This stack trace shows a read operation on a file system, specifically an ext4
file system. The function `copy_user_enhanced_fast_string` is called to copy a
string from user space to kernel space. This is followed by `copy_page_to_iter`
which copies data from a page to an iterator. Then `generic_file_read_iter` is
called to read data from a file. This function calls `ext4_file_read_iter`
which is specific to the ext4 file system. The function `new_sync_read` is
called to perform synchronous read operations. This function calls
`__vfs_read` which is a generic read function for virtual file systems.
Finally, `ksys_read` and `__x64_sys_read` are called to perform the actual
read operation.

To optimise this software, we need to identify the bottleneck in the stack
trace. From the stack trace, it appears that the read operation is the most
CPU-intensive operation. Therefore, we can try to optimise the read operation
by reducing the number of read operations or by making the read operation more
efficient. Here are some suggestions:

1. Reduce the number of read operations: If the application is reading the
same data repeatedly, we can cache the data in memory to reduce the number of
read operations.

2. Use asynchronous I/O: Asynchronous I/O can help to reduce the amount of
time spent waiting for I/O operations to complete. This can be achieved by
using non-blocking I/O or by using threads to perform I/O operations in the
background.

3. Use memory-mapped files: Memory-mapped files can help to reduce the number
of read operations by mapping the file directly into memory. This can improve
performance by reducing the amount of data that needs to be read from disk.

4. Use a faster file system: If the ext4 file system is the bottleneck, we
can try using a faster file system such as XFS or Btrfs.

5. Use a faster storage device: If the storage device is the bottleneck, we
can try using a faster storage device such as an SSD or NVMe drive.
```

In this second example, we will copy and paste in a stack trace from the `perf`
tool.

```
$ ./perf-gpt.py stacktrace
-   64.57%  gzip     gzip                                 [.] longest_match
   - 64.44% longest_match
      - 64.10% zip
           treat_file.part.0
           treat_file.part.0
           main
           __libc_start_call_main
           __libc_start_main@@GLIBC_2.34
           _start
Based on the stack trace, the software is running the gzip compression
algorithm on a file. The function `longest_match` is consuming the most CPU
time, followed by `zip` and `treat_file.part.0`.

`longest_match` is a function in the gzip algorithm that searches for the
longest  matching string in the input data. It is a critical part of the
compression process and is called repeatedly during compression.

`zip` is likely a function that handles the overall compression process,
including calling `longest_match` and other functions.

`treat_file.part.0` is likely a function that handles the input and output
of the file being compressed.

The bottleneck in this stack trace is the `longest_match` function, which
is consuming the majority of the CPU time. This suggests that the compression
 algorithm is spending a lot of time searching for matching strings in the
 input data.

To improve performance, some actions that could be taken include:

1. Optimize the `longest_match` function: This could involve analyzing the
 algorithm and finding ways to make it more efficient. For example, using
 a more efficient data structure for searching or optimizing the search
 algorithm itself.

2. Use a different compression algorithm: If the `longest_match` function
cannot be optimized further, it may be worth exploring other compression
algorithms that are more efficient. For example, the LZ4 algorithm is
known for its fast compression and decompression speeds.

3. Use parallel processing: If the input file is large, it may be worth
exploring parallel processing to speed up the compression process. This
could involve splitting the file into smaller chunks and compressing them
in parallel.

Overall, improving the performance of the gzip compression algorithm will
 likely involve a combination of optimizing the `longest_match` function,
  exploring alternative compression algorithms, and potentially using
  parallel processing.
```

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

The `perf-gpt topn` command helps with this. Provide it with your Top-N, and
it will try to summarise what each program, library and function is doing, as
well as providing you with some suggestions as to what you might do to
optimise your system. In the following we paste in some data from `perf`, but
you could also copy/paste from your favourite commercial profiler of choice.
The ideal format is similar to perfs, with a header line describing each
column, followed by the data, but `perf-gpt` will make a fair attempt at
interpreting the data even if it doesn't follow this exact format.

```
$ ./perf-gpt.py topn
# Children      Self  Command  Shared Object  Symbol
# ........  ........  .......  .............  ......
#
    64.57%    64.57%  gzip     gzip                 [.] longest_match
    14.44%    14.44%  gzip     gzip                 [.] zip
     5.41%     5.41%  gzip     gzip                 [.] updcrc
     3.74%     3.74%  gzip     gzip                 [.] compress_block
     3.33%     3.33%  gzip     gzip                 [.] send_bits
     2.93%     2.93%  gzip     gzip                 [.] ct_tally
     2.08%     2.08%  gzip     gzip                 [.] pqdownheap
     0.39%     0.39%  gzip     gzip                 [.] fill_window
     0.36%     0.36%  gzip     gzip                 [.] build_tree.lto_priv.0
     0.33%     0.33%  gzip     [kernel.kallsyms]    [k] copy_user_enhanced_fast_string

The system is running the gzip compression program, and the profiler has
identified the most expensive functions in terms of CPU time.

gzip: gzip is a file compression program that uses the Lempel-Ziv algorithm
for compression. It is commonly used to compress files for storage or
transmission. The functions executed in gzip are as follows:
    * longest_match: This function is responsible for finding the longest
        matching string in the input data. It is a critical part of the
        Lempel-Ziv algorithm used by gzip.
    * zip: This function is responsible for compressing the input data using
        the Lempel-Ziv algorithm.
    * updcrc: This function updates the cyclic redundancy check (CRC) value
        used to verify the integrity of the compressed data.
    * compress_block: This function compresses a block of input data using
        the Huffman coding algorithm.
    * send_bits: This function sends a bit string to the output buffer.
    * ct_tally: This function updates the Huffman coding tree used to compress
        the input data.
    * pqdownheap: This function is used to maintain the priority queue used by
        the Huffman coding algorithm.
    * fill_window: This function fills the input buffer with data from the
        input file.
    * build_tree.lto_priv.0: This function builds the Huffman coding tree used
        to compress the input data.

[kernel.kallsyms]: This library is part of the Linux kernel and provides a
symbol table of kernel functions. The function executed in this library is:
    * copy_user_enhanced_fast_string: This function is used to copy a string
         from user space to kernel space.

Based on the profiler output, the bottleneck in the system is the gzip
compression algorithm, specifically the longest_match function, which is
responsible for finding the longest matching string in the input data. This
function accounts for 64.57% of the CPU time spent by the program.

To improve the performance of the system, the user may take the following
actions:
    1. Use a faster compression algorithm, such as LZ4 or Zstandard, which
        are designed to be faster than the Lempel-Ziv algorithm used by gzip.
    2. Use a multi-threaded compression library, such as zlib-ng, which can
        take advantage of multiple CPU cores to improve performance.
    3. Increase the amount of available memory to the program, which can reduce
         the amount of time spent on memory allocation and improve overall
         performance.
    4. Use a hardware accelerator, such as a GPU or FPGA, to offload the
        compression workload from the CPU and improve performance.
    5. Use a more powerful CPU with a higher clock speed or more cores to
        improve the performance of the compression algorithm.
```
