from typing import Any

from mods_base import HookType, hook
from unrealsdk.hooks import Block
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

__all__: tuple[str, ...] = ("hooks",)

"""
There's a vanilla bug in vendors where if you compare against the item of the day, then exit, your
selection will jump back to the main item list. There's clearly code showing the intention was to
remain over the item of the day. This fixes it.

The culprit of this is the following function:

```
function PanelOnItemSelected(BaseInventoryPanelGFxObject Panel, WillowInventory Thing) {
    if (bOnItemOfTheDay && !TwoPanelInterface.IsTransferring()) {
        SwitchToPanels();
    }
}
```

The intended purpose of this is to switch back to the main list when you select another item.

Unfortunately for us, when you stop comparing, `PanelOnItemSelected` is called for every item in the
vendor, and `IsTransferring` starts returning False immediately. This means this code always calls
`SwitchToPanels`, switching back to the main view and setting `bOnItemOfTheDay` to false before the
later code can try restore it.

To fix it, we simply block all calls to `SwitchToPanels` during the transition.
"""


@hook("WillowGame.VendingMachineExGFxMovie:SwitchToPanels")
def block_switch_to_panels(*_: Any) -> type[Block]:
    return Block


@hook("WillowGame.VendingMachineExGFxMovie:FinishCompare")
def on_finish_compare_iotd(
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    if obj.bOnItemOfTheDay:
        block_switch_to_panels.enable()


@hook("WillowGame.VendingMachineExGFxMovie:MainInputKey")
def end_finish_compare_iotd(*_: Any) -> None:
    block_switch_to_panels.disable()


hooks: tuple[HookType, ...] = (on_finish_compare_iotd, end_finish_compare_iotd)
