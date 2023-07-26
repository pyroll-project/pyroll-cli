from rich import get_console

console = get_console()

from rich.traceback import install
import pyroll.core
import click

install(
    console=console,
    show_locals=False,
    suppress=[
        pyroll.core.hooks.__file__,
        click
    ]
)
