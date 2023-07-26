from .program import State

from rich.traceback import install
import pyroll.core
import click

install(show_locals=False, suppress=[
    pyroll.core.hooks.__file__,
    click
])

VERSION = "2.0.0"
