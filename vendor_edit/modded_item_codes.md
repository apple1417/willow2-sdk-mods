# Modded Item Format
A modded item code takes the following basic format, where angled brackets denote replacements:
```
<game>MODDED[<b64 base serial>|<b64 modded replacements>]
```

This can be matched with the regex `(\w+)MODDED\[(.+?)\|(.+?)\]` (where the dots could be replaced
with a more detailed b64 match).

The game prefix and b64 base serial are taken straight from the standard item code format, without
modification, so should be handled by tools the exact same way.

When an item has modded parts, they can't be represented in the base serial, and get zero'd. In this
case the modded replacements stores that the relevant slot should be replaced with a given modded
part. The replacements are encoded into a byte buffer, which is then also b64'd before being written
into the code - it keeps them looking similar to normal one.

After decoding the b64, the first byte is reserved for a version number or feature flags. At this
point, none are defined, so tools must reject any value other than 0. The remainder of the buffer is
zlib-compressed, using the custom dictionary provided in [`zdict`](zdict). This is done to try
shorten the modded code as much as possible, since shorter codes are more usable. We use a custom
dictionary to help compress it further, since the decompressed buffers are generally still relatively
short, too short to reach full efficiency - adding the dict halves the average compressed size.

Finally, once you've decompressed the buffer, we get to the actual replacement data. A full set of
replacements is approximately formatted as follows:

```
   LSB    MSB   variable length ...                                             LSB                  MSB
+------+------+====================+====================+====================+------+------+------+------+
| ToReplace   | Definition         | Balance            | Manufacturer       | ManufacturerGradeIndex    |
+------+------+====================+====================+====================+------+------+------+------+
... variable length ...
+====================+====================+====================+====================+====================+
| Body/Alpha         | Grip/Beta          | Barrel/Gamma       | Sight/Delta        | Stock/Epsilon      |
+====================+====================+====================+====================+====================+
... variable length ...
+====================+====================+====================+====================+====================+
| Element/Zeta       | Accessory1/Eta     | Accessory2/Theta   | Material           | Prefix             |
+====================+====================+====================+====================+====================+
... variable length    LSB                  MSB
+====================+------+------+------+------+
| Title              | GameStage                 |
+====================+------+------+------+------+
```

The `ToReplace` is a little endian u16, `ManufacturerGradeIndex` and `GameStage` are little endian
i32s, all other fields are variable length null terminated utf8 strings.

Now most codes won't look like this however. `ToReplace` is a bitmap of what fields actually need
replacements, and only those that do are written to the buffer. `ToReplace` must never be zero,
since that implies there are no replacements and you could've generated a regular item code instead.

Within `ToReplace`, the bits are assigned as follows. Fields which need replacements are set to 1.

|  Bit | Weapon                     | Item                           |
| ---: | :------------------------- | :----------------------------- |
|   15 | `WeaponTypeDefinition`     | `ItemDefinition`               |
|   14 | `BalanceDefinition`        | `BalanceDefinition`            |
|   13 | `ManufacturerDefinition`   | `ManufacturerDefinition`       |
|   12 | `ManufacturerGradeIndex`   | `ManufacturerGradeIndex`       |
|   11 | `BodyPartDefinition`       | `AlphaItemPartDefinition`      |
|   10 | `GripPartDefinition`       | `BetaItemPartDefinition`       |
|    9 | `BarrelPartDefinition`     | `GammaItemPartDefinition`      |
|    8 | `SightPartDefinition`      | `DeltaItemPartDefinition`      |
|    7 | `StockPartDefinition`      | `EpsilonItemPartDefinition`    |
|    6 | `ElementalPartDefinition`  | `ZetaItemPartDefinition`       |
|    5 | `Accessory1PartDefinition` | `EtaItemPartDefinition`        |
|    4 | `Accessory2PartDefinition` | `ThetaItemPartDefinition`      |
|    3 | `MaterialPartDefinition`   | `MaterialItemPartDefinition`   |
|    2 | `PrefixPartDefinition`     | `PrefixItemNamePartDefinition` |
|    1 | `TitlePartDefinition`      | `TitleItemNamePartDefinition`  |
|    0 | `GameStage`                | `GameStage`                    |

From MSB -> LSB, this is the same order as the fields are written to the buffer.

`ManufacturerGradeIndex` and `GameStage` hold the exact integer to replace them with. The other
string fields hold the full object path name of the part to replace them with - no class name, just
`GD_Weap_Pistol.Sight.Pistol_Sight_Torgue`. As a special case, an empty string means the part must
be replaced with None.

While not required, these part names should have `a-z` uppercased to `A-Z` to compress better (the
dictionary is entirely uppercase). The casing of other letters, e.g. `ä` vs `Ä` is left unspecified.
The game treats object names case insensitively.

# Example
As an example, let's replace the `ManufacturerGradeIndex` with 1234, the `Accessory1PartDefinition`
with `My.Custom.Part©`, and the `TitlePartDefinition` with None.

```
ToReplace:
    ManufacturerGradeIndex
         | Accessory1PartDefinition
         |       | TitlePartDefinition
         v       v   v
    0b0001000000100010 -> b"\x22\x10"

ManufacturerGradeIndex:
    1234 -> b"\xd2\x04\x00\x00"

Accessory1PartDefinition:
    "My.Custom.Part©" -> "MY.CUSTOM.PART©"
    "MY.CUSTOM.PART©" -> b"\x4d\x59\x2e\x43\x55\x53\x54\x4f\x4d\x2e\x50\x41\x52\x54\xc2\xa9\x00"
    
TitlePartDefinition:
    None -> b"\x00"

   LSB    MSB   LSB                  MSB
+------+------+------+------+------+------+====================+====================+
| ToReplace   | ManufacturerGradeIndex    | Accessory1/Eta     | Title              |
+------+------+------+------+------+------+====================+====================+

00000000  22 10 d2 04 00 00 4d 59  2e 43 55 53 54 4f 4d 2e  |".....MY.CUSTOM.|
00000010  50 41 52 54 c2 a9 00 00                           |PART....|
00000018
```
This buffer is then compressed, has the version byte prepended, and is converted to b64.
