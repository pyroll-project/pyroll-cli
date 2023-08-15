from rich import get_console

console = get_console()

from rich.traceback import install
import pyroll.core
import click

SUPPRESS_TRACEBACKS = [
    pyroll.core.hooks.__file__,
    click
]

install(
    console=console,
    show_locals=False,
    suppress=SUPPRESS_TRACEBACKS
)
