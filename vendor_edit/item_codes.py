import binascii
import re
import struct
import zlib
from base64 import b64decode, b64encode
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING

import unrealsdk
from mods_base import Game, open_in_mod_dir
from unrealsdk import logging
from unrealsdk.unreal import UObject, WrappedStruct

type ItemDefinitionData = WrappedStruct
type WeaponDefinitionData = WrappedStruct

__all__: tuple[str, ...] = (
    "UnpackResult",
    "pack_item_code",
    "unpack_item_code",
)


class UnpackResult(Enum):
    # Couldn't match an item code in the provided string
    NO_MATCH = auto()
    # The item code started with the wrong game prefix.
    WRONG_GAME = auto()
    # Found an item code, but it was malformed in one way or another - invalid b64, too short, bad
    # checksum, etc.
    MALFORMED_CODE = auto()
    # Found a valid code, but the game itself still rejected it - most likely due to someone
    # manually changing the code's prefix.
    GAME_REJECTED_CODE = auto()
    # Successfully unpacked a weapon code
    FULL_WEAPON = auto()
    # Successfully unpacked an item code
    FULL_ITEM = auto()
    # Successfully unpacked a weapon code, but wasn't able to apply all the modded replacedments.
    PARTIAL_WEAPON = auto()
    # Successfully unpacked an item code, but wasn't able to apply all the modded replacedments.
    PARTIAL_ITEM = auto()


def unpack_item_code(
    code: str,
) -> tuple[UnpackResult, ItemDefinitionData | WeaponDefinitionData | None]:
    """
    Unpacks an item code into it's definition data struct.

    Args:
        code: The item code to unpack.
    Returns:
        A tuple of the result code, and either the unpacked def data on (partial) success, or None.
    """
    return _unpack_item_code_impl(code)


def pack_item_code(def_data: ItemDefinitionData | WeaponDefinitionData) -> str:
    """
    Packs a definition data struct into an item code.

    Args:
        def_data: The def data struct.
    Returns:
        The item code.
    """
    return _pack_item_code_impl(def_data)


# ==================================================================================================

"""
Willow Item Serial Format
=========================

This doesn't seem to be documented well anywhere, so I'll give it my best shot. This file only
slightly touches the raw format, mostly preferring to rely on the game, so this may not be fully
accurate.

Firstly, decode the b64 in the brackets to get the raw bytes. Serial codes are always 40 bytes long,
but it's common to trim trailing FF bytes - add them back just in case.

```
BL2(BwAAAACAVwAHERCgAxIcDgHEA4QFhBzE//////////8VBDuEOsQ=)

07 00000000 8057 00 071110a003121c0e01c4038405841cc4ffffffffffffffff15043b843ac4 ffff
```

I've already spaced this into the key parts:
- B0-6 = version, always 7; B8 = is_weapon 7
- Unique id/seed, scrambles rest of serial when not 0
- Checksum
- Set (aka dlc?) id
- Main contents, more below
- Padding

Most of the item code is scrambled by the unique id. See `decode_serial`, you need to run that first
to convert the rest into usable bytes. This has already been done to the example code.

After decoding, you may want to validate the checksum - see `validate_and_decode_serial_number`.

Next, onto the main contents. This is a bit stream, with fields of uneven bit sizes within it. These
are always read from the LSB towards the MSB, adding each new bit to the MSB of the value. The dumb
easy way to think about this is joining the bits of each byte in reverse, chopping them off from the
left, then reversing again.

```
Hex:          0x07     0x11     0x10
Binary:     00000111 00010001 00010000
Parts:      BBBAAAAA BBBBBBBB       BB

Reversed:   11100000 10001000 00001000
A Bits (5): ^^^^^
B Bits (13):     ^^^ ^^^^^^^^ ^^

A Reversed: 11100
A:          00111 = 7

B Reversed:      000 10001000 00
B:               0000010001000 = 136
```

The sizes of each field change depending on if it's a weapon or item.

Field                          | Bits               | Library
:------------------------------|:-------------------|:----------------
`WeaponTypeDefinition`         | (6 bits, 7 bits)   | `WeaponTypes`
`BalanceDefinition`            | (10 bits, 10 bits) | `BalanceDefs`
`ManufacturerDefinition`       | (7 bits, 4 bits)   | `Manufacturers`
`ManufacturerGradeIndex`       | 7 bits             |
`GameStage`                    | 7 bits             |
`BodyPartDefinition`           | (11 bits, 6 bits)  | `WeaponParts`
`GripPartDefinition`           | (11 bits, 6 bits)  | `WeaponParts`
`BarrelPartDefinition`         | (11 bits, 6 bits)  | `WeaponParts`
`SightPartDefinition`          | (11 bits, 6 bits)  | `WeaponParts`
`StockPartDefinition`          | (11 bits, 6 bits)  | `WeaponParts`
`ElementalPartDefinition`      | (11 bits, 6 bits)  | `WeaponParts`
`Accessory1PartDefinition`     | (11 bits, 6 bits)  | `WeaponParts`
`Accessory2PartDefinition`     | (11 bits, 6 bits)  | `WeaponParts`
`MaterialPartDefinition`       | (11 bits, 6 bits)  | `WeaponParts`
`PrefixPartDefinition`         | (11 bits, 6 bits)  | `WeaponParts`
`TitlePartDefinition`          | (11 bits, 6 bits)  | `WeaponParts`

Field                          | Bits               | Library
:------------------------------|:-------------------|:----------------
`ItemDefinition`               | (8 bits, 9 bits)   | `ItemTypes`
`BalanceDefinition`            | (10 bits, 10 bits) | `BalanceDefs`
`ManufacturerDefinition`       | (7 bits, 4 bits)   | `Manufacturers`
`ManufacturerGradeIndex`       | 7 bits             |
`GameStage`                    | 7 bits             |
`AlphaItemPartDefinition`      | (10 bits, 6 bits)  | `ItemParts`
`BetaItemPartDefinition`       | (10 bits, 6 bits)  | `ItemParts`
`GammaItemPartDefinition`      | (10 bits, 6 bits)  | `ItemParts`
`DeltaItemPartDefinition`      | (10 bits, 6 bits)  | `ItemParts`
`EpsilonItemPartDefinition`    | (10 bits, 6 bits)  | `ItemParts`
`ZetaItemPartDefinition`       | (10 bits, 6 bits)  | `ItemParts`
`EtaItemPartDefinition`        | (10 bits, 6 bits)  | `ItemParts`
`ThetaItemPartDefinition`      | (10 bits, 6 bits)  | `ItemParts`
`MaterialItemPartDefinition`   | (10 bits, 6 bits)  | `ItemParts`
`PrefixItemNamePartDefinition` | (10 bits, 6 bits)  | `ItemParts`
`TitleItemNamePartDefinition`  | (10 bits, 6 bits)  | `ItemParts`

All the parts consist of a pair of ints. If a part is not present, all bits are set to 1.

Lets go parse this example into it's parts. Byte 0 bit 7 is 0, so this is an item.
```
(7, 17)    ItemDefinition
(8, 116)   BalanceDefinition
(16, 1)    ManufacturerDefinition
28         ManufacturerGradeIndex
28         GameStage
(4, 4)     AlphaItemPartDefinition
(15, 4)    BetaItemPartDefinition
(22, 4)    GammaItemPartDefinition
(114, 4)   DeltaItemPartDefinition
(1023, 63) EpsilonItemPartDefinition
(1023, 63) ZetaItemPartDefinition
(1023, 63) EtaItemPartDefinition
(1023, 63) ThetaItemPartDefinition
(87, 4)    MaterialItemPartDefinition
(236, 4)   PrefixItemNamePartDefinition
(234, 4)   TitleItemNamePartDefinition
```

We can already see the item's level 28, and Epsilon-Theta are all None. To convert the rest, we need
the asset library. Gibbed made a tool to extract these into convenient json:
https://raw.githubusercontent.com/gibbed/Borderlands2Dumps/refs/heads/master/Asset%20Library%20Manager.json
https://raw.githubusercontent.com/gibbed/BorderlandsOzDumps/refs/heads/master/Asset%20Library%20Manager.json
https://raw.githubusercontent.com/Natsu235/Gibbed.TinyTinaAoDK.Dumps/refs/heads/main/Asset%20Library%20Manager.json

You can see `config[<lib>]` is where the bit sizes you had to read actually came from.

To get the part back, you want to follow the paths:
```
sets[<set>].libraries[<lib>].sublibraries[<2nd int>].package
sets[<set>].libraries[<lib>].sublibraries[<2nd int>].assets[<1st int>]
```

Our set was 0, so looking at say the Delta part, you'd follow:
```
sets[0].libraries["ItemParts"].sublibraries[4].package     -> "GD_Shields"
sets[0].libraries["ItemParts"].sublibraries[4].assets[114] -> "Accessory.Accessory8_Juggernaut"

Delta: GD_Shields.Accessory.Accessory8_Juggernaut
```
"""

if TYPE_CHECKING:
    from unrealsdk.unreal._uenum import UnrealEnum  # pyright: ignore[reportMissingModuleSource]

    class SerialNumberState(UnrealEnum):
        SNS_Empty = auto()
        SNS_Writing = auto()
        SNS_Full = auto()
        SNS_Reading = auto()
        SNS_Encrypted = auto()
        SNS_MAX = auto()

else:
    SerialNumberState = unrealsdk.find_enum("SerialNumberState")

type InventorySerialNumber = WrappedStruct


GAME_PREFIX = {
    Game.BL2: "BL2",
    Game.TPS: "BLOZ",
    Game.AoDK: "AODK",
}.get(_game := Game.get_current(), _game.name or "")

RE_GAME_PREFIX = re.compile("BL(OZ|TPS)" if _game is Game.TPS else GAME_PREFIX, flags=re.I)
del _game

RE_ITEM_CODE = re.compile(
    r"^(\w+)(?:\((.+?)\)|MODDED\[(.+?)\|(.+?)\])$",
    flags=re.I,
)


WEAPON_DEF_DATA = unrealsdk.find_object(
    "ScriptStruct",
    "WillowGame.WillowWeaponTypes:WeaponDefinitionData",
)

ITEM_PACK, ITEM_UNPACK = (
    (_tmp := unrealsdk.find_class("WillowItem").ClassDefaultObject).PackSerialNumber,
    _tmp.UnpackSerialNumber,
)
WEAPON_PACK, WEAPON_UNPACK = (
    (_tmp := unrealsdk.find_class("WillowWeapon").ClassDefaultObject).PackSerialNumber,
    _tmp.UnpackSerialNumber,
)
del _tmp

PEAK_IS_WEAPON = unrealsdk.find_class("WillowInventory").ClassDefaultObject.PeekIsWeapon


@dataclass
class FieldData:
    name: str
    mask: int
    is_int: bool = False


WEAPON_FIELDS = (
    FieldData("WeaponTypeDefinition", 0x8000),
    FieldData("BalanceDefinition", 0x4000),
    FieldData("ManufacturerDefinition", 0x2000),
    FieldData("ManufacturerGradeIndex", 0x1000, is_int=True),
    FieldData("BodyPartDefinition", 0x0800),
    FieldData("GripPartDefinition", 0x0400),
    FieldData("BarrelPartDefinition", 0x0200),
    FieldData("SightPartDefinition", 0x0100),
    FieldData("StockPartDefinition", 0x0080),
    FieldData("ElementalPartDefinition", 0x0040),
    FieldData("Accessory1PartDefinition", 0x0020),
    FieldData("Accessory2PartDefinition", 0x0010),
    FieldData("MaterialPartDefinition", 0x0008),
    FieldData("PrefixPartDefinition", 0x0004),
    FieldData("TitlePartDefinition", 0x0002),
    FieldData("GameStage", 0x0001, is_int=True),
)

ITEM_FIELDS = (
    FieldData("ItemDefinition", 0x8000),
    FieldData("BalanceDefinition", 0x4000),
    FieldData("ManufacturerDefinition", 0x2000),
    FieldData("ManufacturerGradeIndex", 0x1000, is_int=True),
    FieldData("AlphaItemPartDefinition", 0x0800),
    FieldData("BetaItemPartDefinition", 0x0400),
    FieldData("GammaItemPartDefinition", 0x0200),
    FieldData("DeltaItemPartDefinition", 0x0100),
    FieldData("EpsilonItemPartDefinition", 0x0080),
    FieldData("ZetaItemPartDefinition", 0x0040),
    FieldData("EtaItemPartDefinition", 0x0020),
    FieldData("ThetaItemPartDefinition", 0x0010),
    FieldData("MaterialItemPartDefinition", 0x0008),
    FieldData("PrefixItemNamePartDefinition", 0x0004),
    FieldData("TitleItemNamePartDefinition", 0x0002),
    FieldData("GameStage", 0x0001, is_int=True),
)

MODDED_CODE_VERSION = b"\x00"

with open_in_mod_dir(Path(__file__).parent / "zdict", binary=True) as file:
    _zdict = file.read()

_BASE_COMPRESSOR = zlib.compressobj(level=zlib.Z_BEST_COMPRESSION, zdict=_zdict)
_BASE_DECOMPRESSOR = zlib.decompressobj(zdict=_zdict)

del _zdict


def compress(data: bytes) -> bytes:
    """
    Compresses a byte buffer using the modded code settings.

    Args:
        data: The data to compress.
    Returns:
        The compressed data.
    """
    compressor = _BASE_COMPRESSOR.copy()
    return compressor.compress(data) + compressor.flush()


def decompress(data: bytes) -> bytes:
    """
    Decompresses a byte buffer using the modded code settings.

    Args:
        data: The data to decompress.
    Returns:
        The decompressed data.
    """
    compressor = _BASE_DECOMPRESSOR.copy()
    return compressor.decompress(data) + compressor.flush()


@dataclass
class _SafeUnpackRes:
    success: bool
    is_weapon: bool
    def_data: ItemDefinitionData | WeaponDefinitionData


def safe_unpack(serial_num: bytes | bytearray) -> _SafeUnpackRes:
    """
    Unpacks the given serial number, safely handling cases the game rejects but we find ok.

    Args:
        serial_num: The serial number to unpack.
        is_weapon: True if the serial number is for a weapon.
    Returns:
        If unpacking succeeded, if it was a weapon, and the unpacked definition data.
    """
    decoded = decode_serial(serial_num)
    is_weapon = (decoded[0] >> 7) != 0

    # Also detect if we're missing the weapon/item definition from the raw serial bits
    if is_weapon:
        unpacker, definition_slot_name = WEAPON_UNPACK, "WeaponTypeDefinition"

        # Weapons read the first 13 bits after the header
        no_definition = decoded[8] == 0xFF and (decoded[9] & 0x1F) == 0x1F  # noqa: PLR2004
    else:
        unpacker, definition_slot_name = ITEM_UNPACK, "ItemDefinition"

        # Items read the first 17 bits after the header
        no_definition = decoded[8] == 0xFF and decoded[9] == 0xFF and (decoded[10] & 0x01) == 0x01  # noqa: PLR2004

    unpack_args = WrappedStruct(unpacker.func)
    (serial_num_struct := unpack_args.SerialNumber).Buffer = decoded
    serial_num_struct.State = SerialNumberState.SNS_Full
    success, _, unpacked_def_data = unpacker(unpack_args)

    # If we're missing a definition, the unpacker still works, but reports an error. Fake a success.
    # This does miss the case where we have some other error at the same time. The most likely one
    # would be copying a `TPSMODDED[...]` code without a definition into BL2, where some of the base
    # parts don't exist - but then you should really also get an error on the modded parts.
    if no_definition and not success and getattr(unpacked_def_data, definition_slot_name) is None:
        success = True

    return _SafeUnpackRes(success=success, is_weapon=is_weapon, def_data=unpacked_def_data)


def _unpack_item_code_impl(
    code: str,
) -> tuple[UnpackResult, ItemDefinitionData | WeaponDefinitionData | None]:
    # Start by trying to parse out the two main sections of the code, the encoded serial number and
    # the compressed modded replacements
    parse_result = parse_item_code(code)
    if isinstance(parse_result, UnpackResult):
        return parse_result, None
    encoded_serial, compressed_replacements = parse_result

    # We do need to do some validation before we can pass these to the game
    # If you pass a serial number which is too short, it immediately crashes
    decoded_serial = validate_and_decode_serial_number(encoded_serial)
    if decoded_serial is None:
        return UnpackResult.MALFORMED_CODE, None

    # Since we're doing it anyway, also validate the modded replacements if we have any
    if compressed_replacements is not None:
        decompressed_replacements = validate_and_decompress_modded_replacements(
            compressed_replacements,
        )
        if decompressed_replacements is None:
            return UnpackResult.MALFORMED_CODE, None
    else:
        decompressed_replacements = None

    # Create the new definition data. Start by unpacking the serial.
    unpack_res = safe_unpack(decoded_serial)

    # Now even if the code looked valid before, the game can still reject it - e.g. if someone
    # changed the game prefix, it might be asking for parts which don't exist in this game.
    if not unpack_res.success:
        return UnpackResult.GAME_REJECTED_CODE, None

    # If we don't have any replacements, we're done
    if decompressed_replacements is None:
        return (
            UnpackResult.FULL_WEAPON if unpack_res.is_weapon else UnpackResult.FULL_ITEM,
            unpack_res.def_data,
        )

    # Otherwise, need to apply them all too
    success = apply_modded_replacements(
        unpack_res.def_data,
        bytearray(decompressed_replacements),
        WEAPON_FIELDS if unpack_res.is_weapon else ITEM_FIELDS,
    )

    result = (
        (UnpackResult.PARTIAL_ITEM, UnpackResult.PARTIAL_WEAPON),
        (UnpackResult.FULL_ITEM, UnpackResult.FULL_WEAPON),
    )[success][unpack_res.is_weapon]
    return result, unpack_res.def_data


def parse_item_code(code: str) -> UnpackResult | tuple[bytes, bytes | None]:
    """
    Parses an item code into the two byte buffers contained within.

    Args:
        code: The item code to parse.
    Returns:
        On success, a tuple of the encoded serial number and the compressed modded replacements (if
        given).
        On error, the relevant UnpackResult.
    """
    match = RE_ITEM_CODE.match(code.strip())
    if match is None:
        return UnpackResult.NO_MATCH

    if RE_GAME_PREFIX.match(match.group(1)) is None:
        return UnpackResult.WRONG_GAME

    base_serial_b64 = match.group(2) or match.group(3)
    replacements_b64 = match.group(4)

    try:
        encoded_serial = b64decode(base_serial_b64, validate=True)
        compressed_replacements = (
            None if replacements_b64 is None else b64decode(replacements_b64, validate=True)
        )
    except binascii.Error:
        return UnpackResult.MALFORMED_CODE

    return encoded_serial, compressed_replacements


def validate_and_decode_serial_number(encoded_serial: bytes) -> bytearray | None:
    """
    Decodes a serial number, and validates that it looks sane.

    Args:
        encoded_serial: The encoded serial number to decode.
    Returns:
        The decoded serial number, padded to 40 bytes, or None on error.
    """
    # 1 byte prefix, 4 byte key, 2 byte checksum, and assume at least 1 byte of data = 8 min
    # The buffer it's going into accepts 40 max
    if len(encoded_serial) not in range(8, 40 + 1):
        return None

    decoded_buffer = decode_serial(encoded_serial).ljust(40, b"\xff")

    # Make sure the checksum is valid
    (original_check,) = struct.unpack_from(">H", decoded_buffer, 5)

    decoded_buffer[5:7] = (0xFF, 0xFF)
    check = calc_serial_checksum(decoded_buffer)

    if check != original_check:
        return None

    return decoded_buffer


def validate_and_decompress_modded_replacements(compressed_replacements: bytes) -> bytearray | None:
    """
    Decompresses a modded replacements list, and validates that it looks sane.

    Args:
        compressed_replacements: The compressed replacement list to try decompress.
    Returns:
        The decompressed replacements list, or None on error.
    """

    # 1 byte version, 2 byte zlib header, 4 byte zlib dict id, 4 byte zlib addler, and assume at
    # least 1 byte of compressed data = 12 min
    if len(compressed_replacements) < 12:  # noqa: PLR2004
        return None
    # Only version 0 is supported
    if compressed_replacements[0] != 0:
        return None
    try:
        decompressed = decompress(compressed_replacements[1:])
    except zlib.error:
        return None

    return bytearray(decompressed)


def apply_modded_replacements(
    def_data: WeaponDefinitionData | ItemDefinitionData,
    replacements: bytearray,
    fields: tuple[FieldData, ...],
) -> bool:
    """
    Applies any modded replacements to the given definition data.

    Args:
        def_data: The definition data to apply replacements to.
        replacements: The modded replacements list.
        fields: The set of fields which apply to this definition data.
    Returns:
        True on success, False if any replacement failed to apply.
    """
    (replacements_bitmap,) = struct.unpack_from("<H", replacements, 0)
    replacements = replacements[2:]

    missed_any_object = False
    replacement_fields = (f for f in fields if (f.mask & replacements_bitmap) != 0)
    for field in replacement_fields:
        if field.is_int:
            (value,) = struct.unpack_from("<i", replacements)
            replacements = replacements[4:]
        else:
            obj_name, _, replacements = replacements.partition(b"\x00")
            if obj_name:
                decoded = None
                try:
                    decoded = obj_name.decode("utf8")
                    value = unrealsdk.find_object("Object", decoded)
                except ValueError, UnicodeDecodeError:
                    if decoded is None:
                        decoded = repr(obj_name)
                    logging.warning(f"Couldn't find part '{decoded}' while unpacking item code")
                    missed_any_object = True
                    value = None
            else:
                value = None

        setattr(def_data, field.name, value)

    return not missed_any_object


def _pack_item_code_impl(def_data: ItemDefinitionData | WeaponDefinitionData) -> str:
    if def_data._type == WEAPON_DEF_DATA:
        packer, fields = WEAPON_PACK, WEAPON_FIELDS
    else:
        packer, fields = ITEM_PACK, ITEM_FIELDS

    # Start by packing the item code
    serial_num_struct, _ = packer(def_data)
    # The return value isn't quite in a usable format yet - convert it to one
    serial_number = bytearray(serial_num_struct.Buffer)

    # Comparing the code we have from in game, vs what a save editor gives:
    # editor:  87 00000000 4a7e 0081c7034004e10198c3708541000302c6ff7f09181b30feff9fc36082310ce3
    # in game: 87 d1620929 ffff 0081c7034004e10198c3708541000302c6ff7f09181b30feff9fc36082310ce3 ff
    #               key    check                                                             padding
    # This code still has padding, it doesn't have a checksum yet, and despite having a key it's not
    # encoded yet.

    # Zero the encoding key.
    serial_number[1:5] = (0, 0, 0, 0)

    # Then fix the checksum
    check = calc_serial_checksum(serial_number)
    struct.pack_into(">H", serial_number, 5, check)

    # Now try unpack the code again, so we can tell if anything changed and thus needs a replacement
    unpack_res = safe_unpack(serial_number)
    if not unpack_res.success:
        raise RuntimeError(
            "failed to unpack serial code right after packing, when checking for replacements!",
            serial_number,
            unpack_res.def_data,
        )

    # Check if any slot changed
    replacement_bits = 0
    replacement_data = b""
    for field in fields:
        if (original := getattr(def_data, field.name)) == getattr(unpack_res.def_data, field.name):
            continue

        # Something changed, so write it to the replacements
        replacement_bits |= field.mask

        match original:
            case int():
                assert field.is_int
                replacement_data += struct.pack("<i", original)
            case UObject():
                assert not field.is_int
                replacement_data += original._path_name().upper().encode("utf8") + b"\x00"
            case None:
                assert not field.is_int
                replacement_data += b"\x00"
            case _:
                raise RuntimeError(f"Got unexpected value while encoding item code: {original}")

    # Now convert the code to text format. Get rid of any trailing FF padding, and b64 it.
    base_code = b64encode(serial_number.rstrip(b"\xff")).decode("ascii")

    # If we don't have any modded replacements, can return this directly as a base game code
    if replacement_bits == 0:
        return f"{GAME_PREFIX}({base_code})"

    # Otherwise, finish up the modded code
    compressed_data = compress(struct.pack("<H", replacement_bits) + replacement_data)
    modded_code = b64encode(MODDED_CODE_VERSION + compressed_data).decode("ascii")

    return f"{GAME_PREFIX}MODDED[{base_code}|{modded_code}]"


# This code all ported from Gibbed's editor.
# https://github.com/gibbed/Gibbed.Gearbox/blob/cdb03b048e4989c2272162ebc40f5f34f14712fd/Gibbed.Gearbox.Common/CRC32.cs#L38


def decode_serial(encoded_serial: bytes | bytearray) -> bytearray:
    """
    Decode an encoded serial number.

    Args:
        encoded_serial: The encoded serial number.
    Returns:
        The decoded serial number.
    """
    (key_and_steps,) = struct.unpack_from(">i", encoded_serial, 1)
    key = key_and_steps >> 5

    if key == 0:
        return bytearray(encoded_serial)

    xored = bytearray()
    for byte in encoded_serial[5:]:
        key = (key * 0x10A860C1) % 0xFFFFFFFB
        xored.append((byte ^ key) & 0xFF)

    steps = (key_and_steps & 0b11111) % len(xored)
    return bytearray((encoded_serial[0], 0, 0, 0, 0)) + xored[-steps:] + xored[:-steps]


def calc_serial_checksum(serial: bytearray) -> int:
    """
    Calculates the 16-bit checksum stored in bytes 5 and 6 of a serial number.

    Args:
        serial: The serial number to calculate the checksum of.
    Returns:
        The checksum
    """
    crc = gearbox_crc(serial)
    return (crc >> 16) ^ (crc & 0xFFFF)


def gearbox_crc(buffer: bytearray) -> int:
    """
    Calculates a crc using gearbox's special settings.

    Args:
        buffer: The bytes to crc.
    Returns:
        The crc, as an integer.
    """
    wip_hash = 0xFFFFFFFF
    for byte in buffer.ljust(40, b"\xff"):
        wip_hash = CRC_TABLE[(wip_hash ^ byte) & 0xFF] ^ (wip_hash >> 8)

    return (~wip_hash) & 0xFFFFFFFF


# fmt: off
CRC_TABLE: tuple[int, ...] = (
    0x00000000, 0x77073096, 0xEE0E612C, 0x990951BA,
    0x076DC419, 0x706AF48F, 0xE963A535, 0x9E6495A3,
    0x0EDB8832, 0x79DCB8A4, 0xE0D5E91E, 0x97D2D988,
    0x09B64C2B, 0x7EB17CBD, 0xE7B82D07, 0x90BF1D91,
    0x1DB71064, 0x6AB020F2, 0xF3B97148, 0x84BE41DE,
    0x1ADAD47D, 0x6DDDE4EB, 0xF4D4B551, 0x83D385C7,
    0x136C9856, 0x646BA8C0, 0xFD62F97A, 0x8A65C9EC,
    0x14015C4F, 0x63066CD9, 0xFA0F3D63, 0x8D080DF5,
    0x3B6E20C8, 0x4C69105E, 0xD56041E4, 0xA2677172,
    0x3C03E4D1, 0x4B04D447, 0xD20D85FD, 0xA50AB56B,
    0x35B5A8FA, 0x42B2986C, 0xDBBBC9D6, 0xACBCF940,
    0x32D86CE3, 0x45DF5C75, 0xDCD60DCF, 0xABD13D59,
    0x26D930AC, 0x51DE003A, 0xC8D75180, 0xBFD06116,
    0x21B4F4B5, 0x56B3C423, 0xCFBA9599, 0xB8BDA50F,
    0x2802B89E, 0x5F058808, 0xC60CD9B2, 0xB10BE924,
    0x2F6F7C87, 0x58684C11, 0xC1611DAB, 0xB6662D3D,
    0x76DC4190, 0x01DB7106, 0x98D220BC, 0xEFD5102A,
    0x71B18589, 0x06B6B51F, 0x9FBFE4A5, 0xE8B8D433,
    0x7807C9A2, 0x0F00F934, 0x9609A88E, 0xE10E9818,
    0x7F6A0DBB, 0x086D3D2D, 0x91646C97, 0xE6635C01,
    0x6B6B51F4, 0x1C6C6162, 0x856530D8, 0xF262004E,
    0x6C0695ED, 0x1B01A57B, 0x8208F4C1, 0xF50FC457,
    0x65B0D9C6, 0x12B7E950, 0x8BBEB8EA, 0xFCB9887C,
    0x62DD1DDF, 0x15DA2D49, 0x8CD37CF3, 0xFBD44C65,
    0x4DB26158, 0x3AB551CE, 0xA3BC0074, 0xD4BB30E2,
    0x4ADFA541, 0x3DD895D7, 0xA4D1C46D, 0xD3D6F4FB,
    0x4369E96A, 0x346ED9FC, 0xAD678846, 0xDA60B8D0,
    0x44042D73, 0x33031DE5, 0xAA0A4C5F, 0xDD0D7CC9,
    0x5005713C, 0x270241AA, 0xBE0B1010, 0xC90C2086,
    0x5768B525, 0x206F85B3, 0xB966D409, 0xCE61E49F,
    0x5EDEF90E, 0x29D9C998, 0xB0D09822, 0xC7D7A8B4,
    0x59B33D17, 0x2EB40D81, 0xB7BD5C3B, 0xC0BA6CAD,
    0xEDB88320, 0x9ABFB3B6, 0x03B6E20C, 0x74B1D29A,
    0xEAD54739, 0x9DD277AF, 0x04DB2615, 0x73DC1683,
    0xE3630B12, 0x94643B84, 0x0D6D6A3E, 0x7A6A5AA8,
    0xE40ECF0B, 0x9309FF9D, 0x0A00AE27, 0x7D079EB1,
    0xF00F9344, 0x8708A3D2, 0x1E01F268, 0x6906C2FE,
    0xF762575D, 0x806567CB, 0x196C3671, 0x6E6B06E7,
    0xFED41B76, 0x89D32BE0, 0x10DA7A5A, 0x67DD4ACC,
    0xF9B9DF6F, 0x8EBEEFF9, 0x17B7BE43, 0x60B08ED5,
    0xD6D6A3E8, 0xA1D1937E, 0x38D8C2C4, 0x4FDFF252,
    0xD1BB67F1, 0xA6BC5767, 0x3FB506DD, 0x48B2364B,
    0xD80D2BDA, 0xAF0A1B4C, 0x36034AF6, 0x41047A60,
    0xDF60EFC3, 0xA867DF55, 0x316E8EEF, 0x4669BE79,
    0xCB61B38C, 0xBC66831A, 0x256FD2A0, 0x5268E236,
    0xCC0C7795, 0xBB0B4703, 0x220216B9, 0x5505262F,
    0xC5BA3BBE, 0xB2BD0B28, 0x2BB45A92, 0x5CB36A04,
    0xC2D7FFA7, 0xB5D0CF31, 0x2CD99E8B, 0x5BDEAE1D,
    0x9B64C2B0, 0xEC63F226, 0x756AA39C, 0x026D930A,
    0x9C0906A9, 0xEB0E363F, 0x72076785, 0x05005713,
    0x95BF4A82, 0xE2B87A14, 0x7BB12BAE, 0x0CB61B38,
    0x92D28E9B, 0xE5D5BE0D, 0x7CDCEFB7, 0x0BDBDF21,
    0x86D3D2D4, 0xF1D4E242, 0x68DDB3F8, 0x1FDA836E,
    0x81BE16CD, 0xF6B9265B, 0x6FB077E1, 0x18B74777,
    0x88085AE6, 0xFF0F6A70, 0x66063BCA, 0x11010B5C,
    0x8F659EFF, 0xF862AE69, 0x616BFFD3, 0x166CCF45,
    0xA00AE278, 0xD70DD2EE, 0x4E048354, 0x3903B3C2,
    0xA7672661, 0xD06016F7, 0x4969474D, 0x3E6E77DB,
    0xAED16A4A, 0xD9D65ADC, 0x40DF0B66, 0x37D83BF0,
    0xA9BCAE53, 0xDEBB9EC5, 0x47B2CF7F, 0x30B5FFE9,
    0xBDBDF21C, 0xCABAC28A, 0x53B39330, 0x24B4A3A6,
    0xBAD03605, 0xCDD70693, 0x54DE5729, 0x23D967BF,
    0xB3667A2E, 0xC4614AB8, 0x5D681B02, 0x2A6F2B94,
    0xB40BBE37, 0xC30C8EA1, 0x5A05DF1B, 0x2D02EF8D,
)
# fmt: on
