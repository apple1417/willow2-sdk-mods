# Text Mod Loader
Displays Text Mods from binaries in the SDK mods menu.

# Customizing the description as a Mod Author
Text Mod Loader extracts BLIMP tags, from mod files and uses them to customize how the it displays.
You can read the [full BLIMP spec here](https://github.com/apple1417/blcmm-parsing/tree/master/blimp),
but to summarize, simply add a few tags to the first comment block at the top of the file.

```
@title My Mod
@author apple1417 
@version 1.1
@description Does moddy things.
```

Text Mod Loader supports the following tags.

| Tag Name         | Multiple | Intepretation                                                                                                                                                                                              |
| :--------------- | :------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `@author`        | Allowed  | The mod's author(s), all joined into a list, replacing `TextModLoader`.                                                                                                                                    |
| `@description`   | Allowed  | Joined in the order encountered to create the mod's description. A tag with an empty value (after stripping whitespace) joins surrounding values with a newline, all other pairs are joined using a space. |
| `@main-author`   |  First   | Used as the mod's "main author", placed at the start of the author list.                                                                                                                                   |
| `@title`         |  First   | The mod's title, replacing the filename.                                                                                                                                                                   |
| `@version`       |  First   | The mod's version. Entirely visual, can be any arbitrary string.                                                                                                                                           |
| ---              |   ---    | ---                                                                                                                                                                                                        |
| `@tml-ignore-me` |   n/a    | If any instance of this tag exists, prevents the mod from being listed in the mods menu. Value is ignored.                                                                                                 |

# Changelog

## Text Mod Loader v2
- Complete rewrite for v3 sdk.
- Removed `add_custom_mod_path`, which was never used. The original intent was mostly so that you
  wouldn't need to repeat info such as the mod description, this is now done better via the
  `build_mod` factory.

## Text Mod Loader v1.4
- Added `add_custom_mod_path`, and made a few other internal changes to allow other SDK mods to use
  this as a base.

## Text Mod Loader v1.3
- Updated the file parsing with a few new tweaks we made to BLIMP tags.

## Text Mod Loader v1.2
- Updated the file parsing to better handle non-ascii text. The handling is still not perfect, but
  should cover most cases.

## Text Mod Loader v1.1
- Fixed recommended game detection - you'll now get a warning when trying to run a mod file in a
  game it's not intended for.
- Fixed that editing a mod would cause it to stop being auto-enabled.
- Forced all mod info to be reloaded whenever you update TML.

## Text Mod Loader v1.0
- Inital Release.
