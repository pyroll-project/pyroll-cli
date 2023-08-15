import logging
from dataclasses import dataclass, field
from pyroll.core import Profile, PassSequence


@dataclass
class State:
    sequence: PassSequence = field(default_factory=lambda: None)
    in_profile: Profile = field(default_factory=lambda: None)
    config: dict = field(default_factory=dict)
    logger: logging.Logger = field(default_factory=lambda: None)
