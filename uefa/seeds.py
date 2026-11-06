"""One way to invent a seed, used wherever the user did not give one."""

import secrets

SEED_BITS = 32


def new_seed():
    """A fresh integer seed from 0 to 2**32 - 1 (4 294 967 296 values, up to 10 digits).

    secrets reads the operating system's entropy, so it neither depends on
    nor changes the state of Python's shared `random` generator.

    It is an integer on purpose. The old float seeds were shown with 6
    decimals, and a rounded copy typed back into the app was read as a
    string, which seeds the generator differently: the run could not be
    replayed. An integer prints exactly and replays exactly.
    """
    return secrets.randbits(SEED_BITS)
