# Changelog

## Alt Use Vendors v3
- Upgraded to v3 sdk.

## Alt Use Vendors v2.3
Thanks to @Siggless

- Spending money triggers the removal of the Doppelganger's Money is Power stacks.
- Voicelines play from the vendor instead of the player.
- Prevent null object error on deploying Axton's turret.

## Alt Use Vendors v2.2
- Added sound effects and voicelines, thanks to @Siggless

## Alt Use Vendors v2.1
- Fixed that ammo vendors wouldn't realise when you were full if you had a fractional max ammo count (i.e. you had a max launcher ammo relic), and would keep charging you for ammo you'd never get.

## Alt Use Vendors v2.0
Near complete rewrite.
- Removed dependency on AsyncUtil. Added decepency to Enums.
- Added the option to sell all trash at weapon vendors.
- Fixed that if updating costs were on, and if the displayed cost was higher than your wallet, you'd be unable to buy health/ammo even if you could afford the actual cost.
- No longer hiding the alt use icon if you have nothing to buy, to allow other coop players to use them.
- Removed the updating costs option. It's now always on, and uses hooks instead of polling.

## Alt Use Vendors v1.7
- Fixed crash that occurred when switching maps while standing near a vending machine.

## Alt Use Vendors v1.6
- Added more optimization in anticipation of SDK version 0.7.10. Will fall back to current implementation when running on older versions.

## Alt Use Vendors v1.5
- Optimized a lot of the code - should help anyone who was having stutters.
  As the description mentions (and has for a bit), if you're still having stutters, disable the updating costs option.

## Alt Use Vendors v1.4
- Updated to use some of the new features from SDK version 0.7.8.
  - Most notably, the enabled state is now saved over game launches.
- Fixed that the "can't afford" warning was not shown when updating costs was off.

## Alt Use Vendors v1.3
- Fixed crashes caused by enabling this mod then exiting the game - it didn't actually affect anything but people kept asking.

## Alt Use Vendors v1.2
- Now opens a webpage listing requirements when you don't install them all.

## Alt Use Vendors v1.1
- Made vendor prices only update while a player is near them, which should be more lag friendly.
- Also added an option to disable vendor price updating entirely - you won't see the prices anymore, but it should be even more lag friendly.

## Alt Use Vendors v1.0
- Initial Release.
