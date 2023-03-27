command = "topn"
help = "Analyse Top-N output from a profiler"


def add_to_command_parser(subparsers):
    parser = subparsers.add_parser(command)
    parser.add_argument("-f", help="File containing the Top N data")
