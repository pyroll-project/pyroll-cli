from rich.console import Console

console = Console()

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
