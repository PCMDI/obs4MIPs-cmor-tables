from pathlib import Path, PurePath
import sys

import obs4mips


class TableError(Exception):
    """Exception raised for unknown tables.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message

    def __str__(self):
        return f"{self.message} Exception occured in {self.expression}."


def get_path_to_table(table_name):
    """Return path of obs4MIPs <table_name>."""
    basepath = PurePath(sys.prefix).joinpath("obs4mips_tables")
    outpath = basepath.joinpath(f"{table_name}.json")
    outpath_expanded = basepath.joinpath(f"obs4MIPs_{table_name}.json")
    if Path(outpath).is_file():
        return outpath.as_posix()
    elif Path(outpath_expanded).is_file():
        return outpath_expanded.as_posix()
    else:
        raise TableError('get_path_to_table', f"Table '{table_name}' unknown.")
