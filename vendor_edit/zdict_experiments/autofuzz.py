#!/usr/bin/env python
import re
import shutil
import subprocess
from pathlib import Path


def recompile(size: int) -> None:  # noqa: D103
    subprocess.run(
        [
            "clang++",
            "-fsanitize=fuzzer",
            f"-DFUZZ_TARGET={size}",
            "-O3",
            "-march=native",
            "--std=c++20",
            "-lz",
            "eval.cpp",
            "-o",
            "fuzz",
        ],
        check=True,
    )


def fuzz() -> None:  # noqa: D103
    subprocess.run(
        [
            "./fuzz",
            "-max_len=40000",
            "-len_control=0",
            "-only_ascii=1",
            "-use_value_profile=1",
            "-jobs=8",
            "corpus",
        ],
        check=False,
    )


RE_EVAL_OUTPUT = re.compile(r"^.+?: (\d+)/\d+$")


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


this_dir = Path(__file__).parent
corpus_dir = this_dir / "corpus"

highest_suffix = max(int(x.suffix[1:]) for x in this_dir.glob("zdict.wip.*"))
target_size = evaluate(this_dir / f"zdict.wip.{highest_suffix}")

while True:
    recompile(target_size)
    fuzz()

    outputs = list(this_dir.glob("crash-*"))
    smallest = min(outputs, key=evaluate)

    outputs.remove(smallest)
    for out in outputs:
        shutil.move(out, corpus_dir / out.name)

    target_size = evaluate(smallest)

    highest_suffix = max(int(x.suffix[1:]) for x in this_dir.glob("zdict.wip.*"))
    new_name = f"zdict.wip.{highest_suffix + 1}"
    shutil.copy(smallest, corpus_dir / new_name)
    shutil.move(smallest, this_dir / new_name)
