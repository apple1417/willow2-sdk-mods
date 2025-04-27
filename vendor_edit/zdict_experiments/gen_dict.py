#!/usr/bin/env python
# ruff: noqa: T201
import itertools
import json
from collections import Counter
from pathlib import Path

UNIQUE_PARTS = Path(__file__).parent / "unique_parts.txt"
MIN_SUBSTRING_LEN = 3

# In practice, the output only contains substrings used 8 or more times. Limiting here eliminates
# 90% of the substrings, significantly speeding up our (probably inefficient) N^2 loops
MIN_SUBSTRING_REPEATS = 7

SLIDING_WINDOW_SIZE = 400
TARGET_DICT_SIZE = 0x8000

"""
To start with, gather how often each substring in the part names are used.
"""

print("starting")

# For each part, upper case it, then extract all substrings
substring_counts: Counter[str] = Counter()
for line in UNIQUE_PARTS.read_text().splitlines():
    line = line.upper()
    substring_counts.update(
        line[start:end]
        for start, end in itertools.combinations(range(len(line)), r=2)
        if (end - start) >= MIN_SUBSTRING_LEN
    )

print("got substrings")

# Immediately filter out everything that's used too rarely
substring_counts = Counter(
    {
        substring: count
        for substring, count in substring_counts.items()
        if count >= MIN_SUBSTRING_REPEATS
    },
)

print("removed rare")

# Reverse into a dict of count to possible substrings
reversed_counts: dict[int, set[str]] = {}
for substring, count in substring_counts.most_common():
    if count not in reversed_counts:
        reversed_counts[count] = set()
    reversed_counts[count].add(substring)

print("generated reverse lookup")

"""
A very common situation at this point is the following:

    "ES.SHIELDS.ITEMGRADE": 108,
    "ES.SHIELDS.ITEMGRADE_": 108,
    "ES.SHIELDS.ITEMGRADE_G": 108,
    "ES.SHIELDS.ITEMGRADE_GE": 108,
    "ES.SHIELDS.ITEMGRADE_GEA": 108,
    "ES.SHIELDS.ITEMGRADE_GEAR": 108,
    "ES.SHIELDS.ITEMGRADE_GEAR_": 108,
    "ES.SHIELDS.ITEMGRADE_GEAR_S": 108,
    "ES.SHIELDS.ITEMGRADE_GEAR_SH": 108,
    "ES.SHIELDS.ITEMGRADE_GEAR_SHI": 108,
    "ES.SHIELDS.ITEMGRADE_GEAR_SHIE": 108,
    "ES.SHIELDS.ITEMGRADE_GEAR_SHIEL": 108,
    "ES.SHIELDS.ITEMGRADE_GEAR_SHIELD": 108,

As long as they have the same count, we can trivially remove all the shorter variants, we know
they're all contained in the longest string.
"""

for substring_group in reversed_counts.values():
    seen: set[str] = set()

    # Sort all strings by longest first, so that we know once we've processed a string it can't be
    # a substring of anything else
    for entry in sorted(substring_group, key=len, reverse=True):
        if any(entry in existing for existing in seen):
            # No need for this substring if there's a longer one with the same count
            substring_group.remove(entry)
            continue

        seen.add(entry)


print("removed redundant substrings")

"""
We also have plenty of cases where the counts are different
    "ITE": 2733,
    "TEM": 2707,
    "ITEM": 2705,
    ...
    "_ARTIFACTS.A_ITEM_UNIQUE.A_": 11,

These are a bit tricker, we don't really want to merge the first block with the last one.

We'll use a sliding window.
"""


all_counts = sorted(reversed_counts.keys(), reverse=True)
for idx, count in enumerate(all_counts):
    # Create the windows
    window = set(reversed_counts[count])
    while len(window) < SLIDING_WINDOW_SIZE and (idx + 1) < len(all_counts):
        idx += 1
        # Always add a full group, since we don't know the order within each group
        window.update(reversed_counts[all_counts[idx]])

    substring_group = reversed_counts[count]

    seen: set[str] = set()
    for entry in sorted(window, key=len, reverse=True):
        if any(entry in existing for existing in seen):
            # We might be removing entries from a different group, which were added to the window
            # should probably have a better algorithm for this, but it's quick enough as is
            substring_group.discard(entry)
            continue

        seen.add(entry)

print("sliding window pass")

filtered_counts: dict[str, int] = {}
for size, group in reversed_counts.items():
    # insert by longest string first, since they're worth more
    for entry in group:
        filtered_counts[entry] = size

# Sort by most common first and shortest match second
filtered_counts = dict(
    sorted(
        sorted(filtered_counts.items(), key=lambda x: len(x[0])),
        key=lambda x: x[1],
        reverse=True,
    ),
)


print("re-reversed")

zdict = ""

for substring in filtered_counts:
    # Basic portmanteau-izer
    for n in range(1 - len(substring), 0):
        if zdict.startswith(substring[n:]):
            substring = substring[:n]
            break

    # The most common strings should to go at the end of the dict
    zdict = substring + zdict

    if len(zdict) > TARGET_DICT_SIZE:
        break

print("generated dict")

(Path(__file__).parent / "zdict.wip").write_text(zdict)

with (Path(__file__).parent / "substrings.json").open("w") as file:
    json.dump(filtered_counts, file, indent=4)
