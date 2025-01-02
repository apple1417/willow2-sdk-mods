# Command Extensions
Adds a few new console commands, and provides functionality for other mods to do the same. All these
commands are fully compatible with blcmm files, you can just put them in your mod and have users
merge it with other files and enable/disable various categories and it all just keeps working fine.

[See here for info on the builtin commands and how to write mods using them.](Writing-Mods.md)

### Coop Support
Coop support largely depends on the exact mod making use of this. Command Extensions itself runs
completely client slide, but specific mods may have more in depth requirements. Some commands are
simply incompatible with multiplayer, so anything relying on them too much will not work. Like
always, it's best practice to make sure all players run the exact same set of mods.

### Why does it take longer to `exec` my mods now?
This mod has to look through your mod file to handle the extra commands. This has to be done before
the game looks through it, which just takes some extra, unavoidable, time. You can speed it up by
making your mod file smaller - enable structural edits then delete any categories you don't have
enabled (and won't suddenly re-enable soon).

## Changelog

### Command Extensions v3
- Changed the `py`, `pyexec`, and `pyb` commands back to run closer to how they did in v1.9,
  including running them under legacy mod compatibility.
  
  These commands should now be considered deprecated, they will automatically be disabled when
  legacy mod compatibility is.

- Added the new `py|` command, which is exactly equivalent to `pyb`, but runs *without* legacy mod
  compatibility.

### Command Extensions v2
- Complete rewrite for v3 sdk.
- Added the `CE_NewCmd` command, for use in mod files that attempt to register their own commands.
- Deprecated the `--suppress-exists` arg on `clone_bpd` and `clone`, existing uses are noop'd. While
  developing, you can use the `clone_dbg_suppress_exists` command instead, which suppresses the
  warning for all clone commands.
- Removed the `set_material` command.

### Command Extensions v1.9
- Added the `pyb` command.
- Fixed that `clone_bpd` no longer cloned skills on `Behavior_DeactivateSkill`.

### Command Extensions v1.8
- Added the `regen_balance` command.
- Made the `clone_bpd` command clone skills of `Behavior_ActivateListenerSkill` objects.
- Updated the native file parser with a better [BLCMM preprocessor](https://github.com/apple1417/blcmm-parsing).
  This should fix some obscure parsing errors when doing dumb things with your files.

### Command Extensions v1.7
- Added the `exec_raw` command.
- Added the `--list` argument to the `load_package` command.

### Command Extensions v1.6
- Moved file parsing to a native module - `exec`ing large mod files should now be faster.
- Added the `chat` command.
- Deprecated the `set_material` command.

### Command Extensions v1.5
- Added the `unlock_package` command.
- Added the `--undo` optional argument to `keep_alive`.
- The `clone` and `clone_bpd` commands now set the `ObjectArchetype` field to whatever the source
  object used, rather than having it reference the source object directly.

### Command Extensions v1.4
- The `clone` and `clone_bpd` commands now output an error if the target already exists, and don't
  try to clone it again. This error message can be suppressed with an optional argument.
- Fixed handling of `exec` commands when using files outside of Binaries.
- Add support for the sdk's builtin `py` and `pyexec` commands to blcmm files. Also explicitly raise
  errors when a mod tries to unregister these, which never worked properly in the first place.
- Cleanup handling of subclasses so they're less likely to break if you start trying to create
  custom classes.

### Command Extensions v1.2 + v1.3
- Added the `set_early` command.

### Command Extensions v1.1
- Added the `CE_Debug`, `clone_bpd`, and `set_material` commands.
- Explicitly raise errors when a mod tries to register `set` or unregister `CE_EnableOn` - neither
  of these worked properly in the first place.
- Switched the demo mod file to "online" mode.

### Command Extensions v1.0
- Initial Release.
