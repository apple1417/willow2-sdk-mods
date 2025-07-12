## Changelog

### Apple's Borderlands Cheats v2
Major rewrite, upgrading to v3 sdk.

To help avoid needlessly cluttering your keybinds, added a new cheats menu, though which you can get
to any of the other binds. Additionally, all previously toggleable/cycleable cheats now have a
spinner you can set directly from the mod options, rather than being forced to use a bind.

Presets have been removed. They were quite a complex system, and their need is now better served by
configuring the spinners to your desired defaults, and enabling/disabling the entire mod.

### Apple's Borderlands Cheats v1.13
Fixed `One Shot Mode` not getting loaded properly.

### Apple's Borderlands Cheats v1.12
Fixed `Infinite Ammo` not applying to offhand weapons.

### Apple's Borderlands Cheats v1.11
Fixed `Level Up` not syncing your exp points.
Made `Instant Cooldown` remove any currently active cooldown when you enable it.

### Apple's Borderlands Cheats v1.10
Added hidden option to disable one shot mode in tps - it can sometimes cause crashes simply by existing.

### Apple's Borderlands Cheats v1.9
Updated to use some of the new features from SDK version 0.7.8.
Most notably, the enabled state is now saved over game launches.

### Apple's Borderlands Cheats v1.8
Add preliminary support for upcoming sdk version.

### Apple's Borderlands Cheats v1.7
Kill all no longer kills friendlies.
Fixed that the game would crash if you save quit while in ghost mode, then tried to enter ghost mode again in the same level.
Renamed the ghost mode keybind to `Toggle Ghost Mode` to be more in line with the others - this will reset any bind you already have.
Fixed that changing the value of a cheat in the presets menu, then attempting to change it again without having saved inbetween, would instantly close the menu without saving.
Rewrote a bunch of internals to make adding new cheats more straightforward.
Now opens a webpage to warn you when requirements are outdated.

### Apple's Borderlands Cheats v1.6
Now opens a webpage listing requirements when you don't install them all.

### Apple's Borderlands Cheats v1.5
One shot mode will no longer set friendly NPC's health to 1.
Added a "Revive Self" cheat.

### Apple's Borderlands Cheats v1.4
Improved the hook for 1hp god mode, it should actually no longer be possible to take lethal damage.
Made the hook for one shot mode use a parent class, which might fix issues if there's ever an entity that's not a `WillowPawn`.

### Apple's Borderlands Cheats v1.3
Updated for SDK versions 0.7.4-0.7.6.

### Apple's Borderlands Cheats v1.2
Added configurable presets, which let you change the state of or run as many cheats as you want with a single keypress. For example, a single keypress could enable full infinite ammo, 1hp god mode, and kill all enemies. You can open the menu to create and configure as many presets as you like by pressing `P` when you have the mod selected.

Added new cheats:
- Free shops mode
- Ghost mode
- Teleport between fast travel stations
- Teleport between level transitions
- Reset shops

Reworded a few cheat names/options
Fixed that the mod couldn't be disabled
Fixed some cases where you would take lethal damage in 1hp god mode, though it may still be possible (at least it's rarer)
Fixed that one shot mode didn't account for shields
Fixed that some forms of splash damage still dealt regular damage in one shot mode
Fixed that enemies could become invincible in one shot mode if you managed to deal less than 1 damage

Fixed that infinite ammo would affect all players in the lobby
Fixed that instant cooldown mode would affect all players in the lobby
Fixed that kill all would also kill other players in the lobby

### Apple's Borderlands Cheats v1.1
Added Instant Cooldowns (for action skills and melee overrides)
Added a 'Add OP Level' button
Added a suicide button
One Shot mode now properly awards you xp for all your hard work

### Apple's Borderlands Cheats v1.0
Renamed to Apple's Borderlands Cheats.
Currently contains:
- Infinite Ammo
- God Mode
- One Shot Mode
- Passive Mode
- A 'Kill All' Button
- A 'Level Up' Button

### AmmoCheats
Initial Release.
Adds a keybind to cycle through infinite ammo modes. You can choose to have true infinite ammo, just free reloads, or to turn it off altogether. Also affects grenades.
