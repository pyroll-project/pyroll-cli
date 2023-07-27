import importlib.util
import sys
from pathlib import Path
import click as click
from rich.pretty import pretty_repr
from pyroll.core import Profile, PassSequence

from .state import State
from ..config import DEFAULT_INPUT_PY_FILE


@click.command()
@click.option(
    "-f", "--file",
    help="File to load from.",
    type=click.Path(exists=True, dir_okay=False, writable=False, path_type=Path),
    default=DEFAULT_INPUT_PY_FILE, show_default=True
)
@click.pass_obj
def input_py(state: State, file: Path):
    """
    Reads input data from the Python script FILE.
    The script must define two attributes:

    in_profile:\t\tProfile object defining the entry shape in the first pass
    sequence:\titerable of Unit objects (RollPass or Transport) defining the pass sequence
    """

    state.logger.info(f"Reading input from: %s", file.absolute())

    try:
        spec = importlib.util.spec_from_file_location("__pyroll_input__", file)
        module = importlib.util.module_from_spec(spec)
        sys.modules["__pyroll_input__"] = module
        spec.loader.exec_module(module)
        sequence = getattr(module, "sequence")
        state.sequence = sequence if isinstance(sequence, PassSequence) else PassSequence(sequence)
        state.in_profile = getattr(module, "in_profile")
    except Exception as e:
        state.logger.exception("Error during reading of input file.", exc_info=e)
        raise

    state.logger.info(f"Finished reading input.")

    state.logger.info("Loaded in profile: %s", pretty_repr(state.in_profile, expand_all=True))
    state.logger.info("Loaded pass sequence: %s", pretty_repr(state.sequence))
