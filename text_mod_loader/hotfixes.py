import unrealsdk

from .anti_circular_import import TextModState
from .loader import all_text_mods

any_hotfix_used: bool = False


def mark_hotfixes_used() -> None:
    """
    Marks that a mod using hotfixes has been executed.

    Irreversibly locks all other mods requiring hotfixes.
    """
    global any_hotfix_used

    for mod in all_text_mods.values():
        if mod.state == TextModState.Disabled and mod.spark_service_idx is not None:
            mod.state = TextModState.LockedHotfixes

    any_hotfix_used = True


def is_hotfix_service(idx: int) -> bool:
    """
    Checks if the given Spark Service index corresponds to the hotfix service.

    Args:
        idx: The Spark Service index to check.
    Returns:
        True if the given service is the hotfix service.
    """
    # Assume this is coming from an offline file, which will overwrite it to be valid
    if idx == 0:
        return True

    try:
        # The results for this can change, so better look up each time
        obj = unrealsdk.find_object(
            "SparkServiceConfiguration",
            f"Transient.SparkServiceConfiguration_{idx}",
        )
    except ValueError:
        return False
    return obj.ServiceName.lower() == "micropatch"  # type: ignore
