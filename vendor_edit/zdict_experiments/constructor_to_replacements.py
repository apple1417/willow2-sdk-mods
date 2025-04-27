#!/usr/bin/env python
# ruff: noqa: T201
import json
import struct
from io import BufferedWriter
from pathlib import Path
from typing import Any

WEAPON_SLOTS = {
    "WeaponTypeDefinition": 15,
    "BalanceDefinition": 14,
    "ManufacturerDefinition": 13,
    # "ManufacturerGradeIndex": 12,  # noqa: ERA001
    "BodyPartDefinition": 11,
    "GripPartDefinition": 10,
    "BarrelPartDefinition": 9,
    "SightPartDefinition": 8,
    "StockPartDefinition": 7,
    "ElementalPartDefinition": 6,
    "Accessory1PartDefinition": 5,
    "Accessory2PartDefinition": 4,
    "MaterialPartDefinition": 3,
    "PrefixPartDefinition": 2,
    "TitlePartDefinition": 1,
    # "GameStage": 0,  # noqa: ERA001
}

ITEM_SLOTS = {
    "ItemDefinition": 15,
    "BalanceDefinition": 14,
    "ManufacturerDefinition": 13,
    # "ManufacturerGradeIndex": 12,  # noqa: ERA001
    "AlphaItemPartDefinition": 11,
    "BetaItemPartDefinition": 10,
    "GammaItemPartDefinition": 9,
    "DeltaItemPartDefinition": 8,
    "EpsilonItemPartDefinition": 7,
    "ZetaItemPartDefinition": 6,
    "EtaItemPartDefinition": 5,
    "ThetaItemPartDefinition": 4,
    "MaterialItemPartDefinition": 3,
    "PrefixItemNamePartDefinition": 2,
    "TitleItemNamePartDefinition": 1,
    # "GameStage": 0,  # noqa: ERA001
}


VANILLA_PARTS = {
    part
    for filename in (
        "unique_balances.txt",
        "unique_definitions.txt",
        "unique_manufacturers.txt",
        "unique_parts.txt",
    )
    for part in (Path(__file__).parent / filename).read_text().splitlines()
}
VANILLA_PARTS.add("None")

total_items = 0


def append_replacements(item: dict[str, Any], slots: dict[str, int], file: BufferedWriter) -> None:  # noqa: D103
    bitmap = 0
    replacements = b""
    for slot, bit in slots.items():
        part: str = item[slot]
        if part in VANILLA_PARTS:
            continue
        bitmap |= 1 << bit
        replacements += part.upper().encode("utf8") + b"\x00"

    if bitmap == 0:
        return

    global total_items
    total_items += 1

    file.write(struct.pack("<HH", len(replacements) + 2, bitmap))
    file.write(replacements)


with (Path(__file__).parent / "save0806.json").open() as file:
    save_file = json.load(file)

with (Path(__file__).parent / "replacements.bin").open("wb") as file:
    for weap in save_file["Wpn_Equipped"]:
        append_replacements(weap, WEAPON_SLOTS, file)
    for weap in save_file["Weapons"]:
        append_replacements(weap, WEAPON_SLOTS, file)
    for item in save_file["Itm_Equipped"]:
        append_replacements(item, ITEM_SLOTS, file)
    for item in save_file["Items"]:
        append_replacements(item, ITEM_SLOTS, file)

print("total items:", total_items)
