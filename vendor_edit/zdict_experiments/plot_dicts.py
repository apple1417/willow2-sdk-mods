#!/usr/bin/env python
# ruff: noqa: T201
import re
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt  # pyright: ignore[reportMissingImports]

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


zdicts = list(Path(__file__).parent.glob("zdict.wip.*"))
zdicts.sort(key=lambda x: int(x.suffix[1:]))

scores = [evaluate(z) for z in zdicts]
times = [datetime.fromtimestamp(z.stat().st_ctime, tz=UTC) for z in zdicts]  # pyright: ignore[reportDeprecated]

if False:
    times.append(datetime.now(tz=UTC))
    scores.append(scores[-1])

# Created .0 the day before, so set it to just before the start of fuzzing instead
times[0] = times[1] - timedelta(minutes=1)

# system crashed, so close the gap
crash_time = times[103] - times[102] - timedelta(minutes=5)
for idx in range(103, len(times)):
    times[idx] -= crash_time


print("total time:", times[-1] - times[0])

delta_mins = [(x - times[0]).total_seconds() / 60 for x in times]

if False:
    import numpy as np

    derivative_mins = [delta_mins[idx] - delta_mins[idx - 1] for idx in range(1, len(delta_mins))]
    rolling = np.cumsum(derivative_mins, dtype=float)
    N = 10
    rolling[N:] = rolling[N:] - rolling[:-N]
    rolling = rolling[N - 1 :] / N
    plt.bar(range(1, len(delta_mins)), derivative_mins)  # type: ignore
    plt.plot(range(N, len(delta_mins)), rolling, color="orange")  # type: ignore

    plt.xlabel("dict num")  # type: ignore
    plt.ylabel("time to find (min)")  # type: ignore

else:
    plt.step(delta_mins, scores)  # type: ignore

    plt.xlabel("fuzz time (mins)")  # type: ignore
    plt.ylabel("compressed size (bytes)")  # type: ignore

plt.show()  # type: ignore
