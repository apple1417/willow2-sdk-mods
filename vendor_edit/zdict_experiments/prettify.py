#!/usr/bin/env python
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

RE_EVAL_OUTPUT = re.compile(r"^.+?: (\d+)/\d+$")
RE_NO_SYM = re.compile(rb"[^A-Za-z0-9\._]")
RE_NO_RUNS = re.compile(rb"(.)\1{2,}")

REQUIRED_SIZE = 0x8000


def evaluate(file: Path) -> int:  # noqa: D103
    match = RE_EVAL_OUTPUT.match(
        subprocess.run(
            ["./evaluate", file],
            check=True,
            capture_output=True,
            encoding="utf8",
        ).stdout,
    )
    assert match is not None
    return int(match.group(1))


def transform_upper(data: bytes) -> bytes:  # noqa: D103
    return data.upper()


def transform_no_sym(data: bytes) -> bytes:  # noqa: D103
    return RE_NO_RUNS.sub(data, b"")


zdict_path = Path(sys.argv[1])
print("original:", evaluate(zdict_path))


zdict_bytes = zdict_path.read_bytes()

transforms: list[Callable[[bytes], bytes]] = [
    bytes.upper,
    lambda x: RE_NO_SYM.sub(b"", x),
    lambda x: RE_NO_RUNS.sub(rb"\g<1>\g<1>", x),
    lambda x: x[-REQUIRED_SIZE:],
]

output = Path(__file__).parent / "zdict.pretty"

for key in range(1, (1 << len(transforms))):
    new_bytes = bytes(zdict_bytes)
    for idx, transform in enumerate(transforms):
        if ((1 << idx) & key) == 0:
            continue
        new_bytes = transform(new_bytes)

    if len(new_bytes) < REQUIRED_SIZE:
        continue

    output.write_bytes(new_bytes)
    print(f"{key:0{len(transforms)}b}: {evaluate(output)}")
