## Changelog

### Vendor Edit v3
- Reworked how the possible parts on items are selected, fixing that many items would show
  impossible parts which would cause them to get sanity checked (e.g. you could set a custom payload
  on a fastball).

- Changed from re-initializing items to completely removing and replacing them, to fix issues where
  some stats would grow infinitely. Hopefully this hasn't introduced any duping bugs...
  
- When changing an item's level, rather than going back to the main menu, now immediately re-opens
  the level menu. This should make it a little nicer when making large level changes.

### Vendor Edit v2
- Initial Release. I forgot to update the version number after copying, hence no v1.
