import unrealsdk
from mods_base import Game, ObjectFlags
from unrealsdk.unreal import UObject

type Actor = UObject
type AkEvent = UObject

# Sound AkEvents for playing
AKE_BUY: str = "Ake_UI.UI_Vending.Ak_Play_UI_Vending_Buy"
AKE_SELL: str = "Ake_UI.UI_Vending.Ak_Play_UI_Vending_Sell"

AKE_INTERACT_BY_VENDOR_NAME: dict[str, str] = {
    Game.BL2: {
        "InteractiveObj_VendingMachine_GrenadesAndAmmo": (
            "Ake_VOCT_Contextual.Ak_Play_VOCT_Marcus_Vending_Munition_Purchase"
        ),
        "InteractiveObj_VendingMachine_HealthItems": (
            "Ake_VOCT_Contextual.Ak_Play_VOCT_Zed_Store_Welcome"
        ),
        "VendingMachine_Weapons_Definition": (
            "Ake_VOCT_Contextual.Ak_Play_VOCT_Marcus_Vending_Munition_Bye"
        ),
        "IO_Aster_VendingMachine_GrenadesAndAmmo": (
            "Ake_Aster_VO.VOCT.Ak_Play_VOCT_Aster_Marcus_Store_Purchase"
        ),
        "IO_Aster_VendingMachine_HealthItems": (
            "Ake_Aster_VO.VOCT.Ak_Play_VOCT_Aster_Zed_Store_Purchase"
        ),
        "VendingMachine_Aster_Weapons_Definition": (
            "Ake_Aster_VO.VOCT.Ak_Play_VOCT_Aster_Marcus_Store_Bye"
        ),
        "VendingMachine_TorgueToken": "Ake_Iris_VO.Ak_Play_Iris_TorgueVendingMachine_Purchase",
    },
    Game.TPS: {
        "InteractiveObj_VendingMachine_GrenadesAndAmmo": (
            "Ake_VOCT_Contextual.Ak_Play_VOCT_Marcus_Vending_Munition_Purchase"
        ),
        "InteractiveObj_VendingMachine_HealthItems": (
            "Ake_Cork_VOCT_Contextuals.Cork_VOCT_NurseNina.Ak_Play_VOCT_Cork_NurseNina_Store_Purchase"
        ),
        "VendingMachine_Weapons_Definition": (
            "Ake_VOCT_Contextual.Ak_Play_VOCT_Marcus_Vending_Munition_Bye"
        ),
        "InteractiveObj_VendingMachine_GrenadesAndAmmo_Marigold": (
            "Ake_VOCT_Contextual.Ak_Play_VOCT_Marcus_Vending_Munition_Purchase"
        ),
        "InteractiveObj_VendingMachine_HealthItems_Marigold": (
            "Ake_Cork_VOCT_Contextuals.Cork_VOCT_NurseNina.Ak_Play_VOCT_Cork_NurseNina_Store_Purchase"
        ),
        "VendingMachine_Weapons_Definition_Marigold": (
            "Ake_VOCT_Contextual.Ak_Play_VOCT_Marcus_Vending_Munition_Bye"
        ),
        "InteractiveObj_VendingMachine_GrenadesAndAmmo_Marigold_BL1": (
            "Ake_VOCT_Contextual.Ak_Play_VOCT_Marcus_Vending_Munition_Purchase"
        ),
        "InteractiveObj_VendingMachine_HealthItems_Marigold_BL1": (
            "Ake_Marigold_VOCT_Contextuals.Dlc_Marigold_VOCT_Zed.Ak_Play_Dlc_Marigold_VOCT_Zed_Vending_Welcome"
        ),
        "VendingMachine_Weapons_Definition_Marigold_BL1": (
            "Ake_VOCT_Contextual.Ak_Play_VOCT_Marcus_Vending_Munition_Bye"
        ),
    },
    Game.AoDK: {
        "IO_Aster_VendingMachine_GrenadesAndAmmo": (
            "Ake_Aster_VO.VOCT.Ak_Play_VOCT_Aster_Marcus_Store_Purchase"
        ),
        "IO_Aster_VendingMachine_HealthItems": (
            "Ake_Aster_VO.VOCT.Ak_Play_VOCT_Aster_Zed_Store_Purchase"
        ),
        "VendingMachine_Aster_Weapons_Definition": (
            "Ake_Aster_VO.VOCT.Ak_Play_VOCT_Aster_Marcus_Store_Bye"
        ),
    },
}[Game.get_current()]


# AkEvents are not loaded by default, and we don't want to do an "expensive" find object call, or a
# truely expensive load package, so we'll just cache them (and keep alive) as we use them
akevent_cache: dict[str, AkEvent] = {}


def find_and_play_akevent(actor: Actor, event_name: str) -> None:
    """
    Attempts to find and play an AkEvent.

    Silently drops it on failure.

    Args:
        actor: The actor to play at.
        event_name: The object name of the event to play.
    """

    event = akevent_cache.get(event_name)
    if event is None:
        try:
            event = unrealsdk.find_object("AkEvent", event_name)
        except ValueError:
            return
        event.ObjectFlags |= ObjectFlags.KEEP_ALIVE
        akevent_cache[event_name] = event

    actor.PlayAkEvent(event)
