```
                  __                   _
 _ __   ___ _ __ / _|       __ _ _ __ | |_
| '_ \ / _ \ '__| |_ _____ / _` | '_ \| __|
| |_) |  __/ |  |  _|_____| (_| | |_) | |_
| .__/ \___|_|  |_|        \__, | .__/ \__|
|_|                        |___/|_|

Performance analysis and optimisation with LLMs
```

# Examples

## Finding a faster, equivalent, library

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

## Suggesting actions based on a stack trace

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