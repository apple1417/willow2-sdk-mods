# Spawn Multiplier
## Softlocks
This mod is known to cause softlocks. The game handles "kill all enemies" objectives in half a dozen
different ways for example, and not all of them interact with this properly. When something
softlocks, SQing and disabling the mod, completing the objective without it, and then re-enabling
it, should let you progress further.

These softlocks are not considered bugs, they're just the cost of doing business. The only bugs are
ones that break your save, and prevent progressing even after disabling the mod. This is not to say
that spawns which softlock won't be blacklisted at some point, just that I won't spend time actively
hunting them all down.

The current list of blacklisted enemies is:
- Thousand Cuts Brick - You can't hand in the note if there are extras.
- First Bunker autocannon - Extras will be invicible, but have to be killed to progress the quest.
- Claptrap worshippers - Extras will be friendly, but must be killed to progress the quest.
- Story kill Uranus - Extras don't spawn, but must be killed to open the doorway back.
- The first four resurrected skeletons in each grave during My Dead Brother - Extras don't spawn,
  but must be killed to progress.

## Changelog

### Spawn Multiplier v4
- Added support for BL1, thanks to @RedxYeti.

### Spawn Multiplier v3
- Added the ability to set custom spawn limit multipliers, thanks to @AldebaraanMKII.

### Spawn Multiplier v2
- Upgraded to v3 sdk.

### Spawn Multiplier v1.5
- Updated to use some of the new features from SDK version 0.7.8. Most notably, the enabled state is
  now saved over game launches.

### Spawn Multiplier v1.4
- Fixed a few places where enemy spawns had an additional cap, which will now be increased along
  with the others.
- Blacklisted a few enemies that would cause softlocks if multiplied.
- Fixed potential compatibility issue with an upcoming version of the sdk.

### Spawn Multiplier v1.3
- Prevented multiplying spawn counts for some non-enemy actors, which could cause softlocks in some
  cases (e.g. Burrows' generators).

### Spawn Multiplier v1.2
- Fixed that spawn limit changes would not be reapplied on map change, they'd always revert to
  standard.
- Fixed some more instances where spawn counts would round down to 0.

### Spawn Multiplier v1.1
- Fixed that changing the multiplier could occasionally round spawn counts down to 0.
- Fixed that disabling the mod would not revert spawn counts.

### Spawn Multiplier v1.0
- Initial Release.
