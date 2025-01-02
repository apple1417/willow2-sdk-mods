# Table of Contents
- [Table of Contents](#table-of-contents)
- [Built-in Custom Commands](#built-in-custom-commands)
  - [`CE_Debug`](#ce_debug)
  - [`CE_EnableOn`](#ce_enableon)
  - [`CE_NewCmd`](#ce_newcmd)
  - [`chat`](#chat)
  - [`clone`](#clone)
  - [`clone_bpd`](#clone_bpd)
  - [`clone_dbg_suppress_exists`](#clone_dbg_suppress_exists)
  - [`exec_raw`](#exec_raw)
  - [`keep_alive`](#keep_alive)
  - [`load_package`](#load_package)
  - [`py|`](#py)
  - [`regen_balance`](#regen_balance)
  - [`set_early`](#set_early)
  - [`suppress_next_chat`](#suppress_next_chat)
  - [`unlock_package`](#unlock_package)
- [Writing Text Mods](#writing-text-mods)
  - [Parsing Intricacies](#parsing-intricacies)
- [Using Command Extensions in your own SDK mods](#using-command-extensions-in-your-own-sdk-mods)
  - [Adding custom commands](#adding-custom-commands)
  - [Calling custom commands](#calling-custom-commands)

# Built-in Custom Commands

## `CE_Debug`
usage: `CE_Debug [-h] {Enable,Disable}`

Enables/disables Command Extension debug logging. This logs a copy of each
command to be run, useful for checking that your blcm files are being handled
correctly.

| positional arguments |      |
| :------------------- | :--- |
| `{Enable,Disable}`   |      |

| optional arguments |                                 |
| :----------------- | :------------------------------ |
| `-h, --help`       | show this help message and exit |

## `CE_EnableOn`
usage: `CE_EnableOn [-h] {All,Any,Force,Next}`

Can only be used in BLCMM files.

Changes the strategy used to determine if a custom command is enabled or not. Defaults to 'Any'.
This change applies until the end of the category, or until the next instance of this command. It
*does* recurse into subcategories.

Using each strategy, a custom command is enabled if:

|       |                                                                      |
| :---- | :------------------------------------------------------------------- |
| All   | All regular commands in the same category are enabled.               |
| Any   | Any regular command in the same category is enabled.                 |
| Force | It is always enabled.                                                |
| Next  | The next regular command after it (in the same category) is enabled. |


| positional arguments   |      |
| :--------------------- | :--- |
| `{All,Any,Force,Next}` |      |

| optional arguments |                                 |
| :----------------- | :------------------------------ |
| `-h, --help`       | show this help message and exit |

## `CE_NewCmd`
usage: `CE_NewCmd [-h] cmd`

Can only be used in files. As an optimization, when parsing though a file the
known commands are collected all at once, and only executed after. This means
if those commands register new commands, the new ones aren't yet known and
thus won't get collected. This command marks a new command for collection
within a mod file. The command MUST still be registered via normal mechanisms
beforehand in order for it to have any effect.

| positional arguments |                                                           |
| :------------------- | :-------------------------------------------------------- |
| `cmd`                | The command being registered. May not contain whitespace. |

| optional arguments |                                 |
| :----------------- | :------------------------------ |
| `-h, --help`       | show this help message and exit |

## `chat`
usage: chat [-h] [source] msg

Similarly to the `say` command, writes a message in chat, but lets you
customize the message source. Note this does not use the same parsing as the
`say` command, make sure you quote your message if it includes spaces.

| positional arguments |                                                                                                       |
| :------------------- | :---------------------------------------------------------------------------------------------------- |
| `source`             | What the message source should be. Defaults to the same as a normal chat message, username/timestamp. |
| `msg`                | The message to write.                                                                                 |

| optional arguments |                                 |
| :----------------- | :------------------------------ |
| `-h, --help`       | show this help message and exit |

## `clone`
usage: `clone [-h] [-x] base clone`

Creates a clone of an existing object.

| positional arguments |                                  |
| :------------------- | :------------------------------- |
| `base`               | The object to create a copy of.  |
| `clone`              | The name of the clone to create. |

| optional arguments      |                                                                    |
| :---------------------- | :----------------------------------------------------------------- |
| `-h, --help`            | show this help message and exit                                    |
| `-x, --suppress-exists` | Deprecated, does nothing. See `clone_dbg_suppress_exists` instead. |

## `clone_bpd`
usage: `clone_bpd [-h] [-x] base clone`

Creates a clone of a BehaviourProvidierDefinition, as well as recursively
cloning some of the objects making it up. This may not match the exact layout
of the original objects, dump them manually to check what their new names are.

| positional arguments |                                  |
| :------------------- | :------------------------------- |
| `base`               | The bpd to create a copy of.     |
| `clone`              | The name of the clone to create. |

| optional arguments      |                                                                    |
| :---------------------- | :----------------------------------------------------------------- |
| `-h, --help`            | show this help message and exit                                    |
| `-x, --suppress-exists` | Deprecated, does nothing. See `clone_dbg_suppress_exists` instead. |

## `clone_dbg_suppress_exists`
usage: `clone_dbg_suppress_exists [-h] {Enable,Disable}`

Suppresses the 'object already exists' errors which may occur while cloning.
Only intended for debug usage.

| positional arguments |      |
| :------------------- | :--- |
| `{Enable,Disable}`   |      |

| optional arguments |                                 |
| :----------------- | :------------------------------ |
| `-h, --help`       | show this help message and exit |

## `exec_raw`
usage: `exec_raw [-h] ...`

Behaves exactly like an `exec` command, but disables custom command parsing.

| positional arguments |                                 |
| :------------------- | :------------------------------ |
| `args`               | Standard exec command arguments |

| optional arguments |                                 |
| :----------------- | :------------------------------ |
| `-h, --help`       | show this help message and exit |

## `keep_alive`
usage: `keep_alive [-h] [-u] object`

Prevents an object from being garbaged collected, it will always be loaded
until you restart the game.

| positional arguments |                           |
| :------------------- | :------------------------ |
| `object`             | The object to keep alive. |

| optional arguments |                                  |
| :----------------- | :------------------------------- |
| `-h, --help`       | show this help message and exit  |
| `-u, --undo`       | Undo a previous keep alive call. |

## `load_package`
usage: `load_package [-h] [--list] [package]`

Loads a package and all objects contained within it. This freezes the game as
it loads; it should be used sparingly. Supports using glob-style wildcards to
load up to 10 packages at once, though being explicit should still be
preferred.

| positional arguments |                                                                                               |
| :------------------- | :-------------------------------------------------------------------------------------------- |
| `package`            | The package(s) to load. This uses the full upk names; not the shortened version hotfixes use. |

| optional arguments |                                                                              |
| :----------------- | :--------------------------------------------------------------------------- |
| `-h, --help`       | show this help message and exit                                              |
| `--list`           | List all packages matching the given pattern, instead of trying to load any. |

## `py|`
usage: `py| [-h] [-x] [-d] [-p] ...`

Runs a block of python statements, which may span multiple lines. Only one
space after the command is consumed for arg parsing - `py|[3*space]abc`
extracts the line `[2*space]abc`.

| positional arguments |                                       |
| :------------------- | :------------------------------------ |
| `args`               | Python code. Whitespace is preserved. |

| optional arguments |                                 |
| :----------------- | :------------------------------ |
| `-h, --help`       | show this help message and exit |
| `-x, --exec`       | Executes stored lines.          |
| `-d, --discard`    | Discards stored lines.          |
| `-p, --print`      | Prints stored lines.            |

If an optional arg is specified, python code is ignored. Optional args must be
at the start of the command to be recognised.

## `regen_balance`
usage: `regen_balance [-h] balance`

Regenerates the runtime parts list of an item/weapon balance, to reflect
changes in the base part lists. Edits objects in place.

| positional arguments |                            |
| :------------------- | :------------------------- |
| `balance`            | The balance to regenerate. |

| optional arguments |                                 |
| :----------------- | :------------------------------ |
| `-h, --help`       | show this help message and exit |

## `set_early`
usage: `set_early [-h] ...`

Behaves exactly like a `set` command. Only useful in files, as it's run during
custom command parsing instead of afterwards.

| positional arguments |                                |
| :------------------- | :----------------------------- |
| `args`               | Standard set command arguments |

| optional arguments |                                 |
| :----------------- | :------------------------------ |
| `-h, --help`       | show this help message and exit |

## `suppress_next_chat`
usage: `suppress_next_chat [-h] [pattern]`

Prevents the next chat message that matches a given glob pattern from being
printed. Multiple calls to this stack, and suppress multiple messages. This is
intended to be used to suppress an error message, so that it only gets printed
when someone tries to exec your file without running Command Extensions.

| positional arguments |                                                    |
| :------------------- | :------------------------------------------------- |
| `pattern`            | The glob pattern matching the message to suppress. |

| optional arguments |                                 |
| :----------------- | :------------------------------ |
| `-h, --help`       | show this help message and exit |

## `unlock_package`
usage: `unlock_package [-h] [-u] object`

Unlocks an object allowing it to be referenced cross-package.

| positional arguments |                       |
| :------------------- | :-------------------- |
| `object`             | The object to unlock. |

| optional arguments |                                      |
| :----------------- | :----------------------------------- |
| `-h, --help`       | show this help message and exit      |
| `-u, --undo`       | Undo a previous unlock package call. |

# Writing Text Mods
You can automatically use all of these commands inside text mods exactly the same as in console.
Just add them inside BLCMM as comments, the mod automatically picks up `exec` commands and parses
through the files to execute whatever custom commands are stored in them. You can check out
[sanic.blcm](sanic.blcm) as an example.

## Parsing Intricacies
There are a few intricacies to how exactly mod files get parsed, which you might be interested in.

The first thing to realize is that all custom commands are run before any regular ones stored in the
file. When you run an `exec` command, the mod looks through the file, runs any custom commands in
it, and then lets the game handle the file normally. This is the reason for the `set_early` command,
since it's a custom command it will run early alongside the others, which may be useful for things
like setting template properties before cloning an object.

If you `exec` a file that's *not* a BLCMM file, the mod falls back to a naive line-by-line approach.
For each line in the file, if that line matches a custom command, it runs that command. Leading
whitespace is ignored.

BLCMM files use a bit more involved parsing. Custom commands can be enabled and disabled by toggling
the category they're in. This requires a bit a workaround however, which might cause some
interesting behaviour. BLCMM unfortunately only stores if individual set commands enabled. Our custom
commands are technically comments, so they don't get this, and categories themselves don't have a
specific enabled state either. Instead, we have to determine if a custom command is enabled by if
the regular set commands around it are.

By default, a custom command is considered to be enabled if any regular command in the same category
as it also is. This only applies to the current category, it doesn't recurse down into subcategories
or up into parent ones. The state of subcategories also has no effect, only commands on the exact
same level do. In practice, most users will only enable/disable entire categories at a time, so as
long as you put custom commands in the same category as the normal commands that interact with them,
they should all get executed together.

The `CE_EnableOn` command can be used inside BLCMM files to change when a custom command is
considered to be enabled.

# Using Command Extensions in your own SDK mods
## Adding custom commands
Command Extensions is built on top of the command system in `mods_base`. After creating a command
normally, you must register it with command extensions in order to let it work from mod files. You
can do this either by manually calling `command_extensions.register` and
`command_extensions.deregister`, or you can use `command_extensions.autoregister` to do so
automatically when the command is enabled/disabled.

There are a few functions exposed in `command_extensions.builtins` which may be helpful when writing
your own commands.

## Calling custom commands
In previous versions of the sdk, running console commands from Python would not be caught by
Command Extensions, and you had to manually notify it whenever you ran one. This is no longer the
case, you can simply call them as normal.

```py
from mods_base import get_pc
get_pc().ConsoleCommand(f"exec \"{filename}\"")
```
