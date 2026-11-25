import sys
from rich.console import Console
from art import tprint
from .parser import args_parser

console = Console()

def header():
    tprint("Binocular", font="small")
    args = args_parser(sys.argv[1:])