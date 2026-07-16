import functools
from collections import Counter
from typing import TYPE_CHECKING

import unrealsdk
from mods_base import command
from unrealsdk import logging

from . import obj_name_splitter, parse_object
from .clone import clone_object, parse_clone_target

if TYPE_CHECKING:
    import argparse
    from collections.abc import Callable

    from unrealsdk.unreal import UClass, UObject


# There are a bunch of different fields skills can be stored in, hence the field arg
def fixup_skill_field(field: str, behavior: UObject, known_clones: dict[UObject, UObject]) -> None:
    """
    Clones skills referenced in skill bpds, as well as other bpds stored on those skills.

    Args:
        field: The name of the field on the behavior object which the skill's stored in.
        behavior: The behavior object which references a skill.
        known_clones: A dict of objects to their clones, used to prevent double-cloning.
    """
    skill = getattr(behavior, field)
    if skill is None:
        return

    if skill in known_clones:
        setattr(behavior, field, known_clones[skill])
        return

    cloned_skill = clone_object(
        skill,
        behavior,
        # Empty string gives us the auto numbering back
        "" if skill.Name == skill.Class.Name else skill.Name,
    )
    if cloned_skill is None:
        return
    known_clones[skill] = cloned_skill

    setattr(behavior, field, cloned_skill)

    bpd = cloned_skill.BehaviorProviderDefinition
    if bpd is None:
        return

    if bpd in known_clones:
        cloned_skill.BehaviorProviderDefinition = known_clones[bpd]
        return

    cloned_bpd = clone_object(bpd, cloned_skill, "" if bpd.Name == bpd.Class.Name else bpd.Name)
    if cloned_bpd is None:
        return
    known_clones[bpd] = cloned_bpd

    cloned_skill.BehaviorProviderDefinition = cloned_bpd
    fixup_bpd(cloned_bpd, known_clones)


"""
Dict mapping behavior class names to functions that perform extra fixups on them, incase there are
 extra objects that need to be cloned.
"""
extra_behaviour_fixups: dict[UClass, Callable[[UObject, dict[UObject, UObject]], None]] = {
    unrealsdk.find_class("Behavior_AttributeEffect"): functools.partial(
        fixup_skill_field,
        "AttributeEffect",
    ),
    unrealsdk.find_class("Behavior_ActivateSkill"): functools.partial(
        fixup_skill_field,
        "SkillToActivate",
    ),
    unrealsdk.find_class("Behavior_ActivateListenerSkill"): functools.partial(
        fixup_skill_field,
        "SkillToActivate",
    ),
    unrealsdk.find_class("Behavior_DeactivateSkill"): functools.partial(
        fixup_skill_field,
        "SkillToDeactivate",
    ),
}


def fixup_bpd(cloned: UObject, known_clones: dict[UObject, UObject]) -> None:
    """
    Looks through a BPD for subobjects which still need to be cloned.

    Args:
        cloned: The cloned BPD.
        known_clones: A dict of objects to their clones, used to prevent double-cloning.
    """
    class_counter: Counter[UClass] = Counter()
    for sequence in cloned.BehaviorSequences:
        # There are a bunch of other fields, but this seems to be the only used one
        for data in sequence.BehaviorData2:
            behavior = data.Behavior
            if behavior is None:
                continue

            if behavior in known_clones:
                data.Behavior = known_clones[behavior]
                continue

            cloned_behavior = clone_object(
                behavior,
                cloned,
                f"{behavior.Class.Name}_{class_counter[behavior.Class.Name]}",
            )
            if cloned_behavior is None:
                continue
            class_counter[behavior.Class.Name] += 1
            known_clones[behavior] = cloned_behavior

            data.Behavior = cloned_behavior

            for cls, fixup in extra_behaviour_fixups.items():
                if cloned_behavior.Class._inherits(cls):
                    fixup(cloned_behavior, known_clones)


@command(
    splitter=obj_name_splitter,
    description=(
        "Creates a clone of a BehaviourProvidierDefinition, as well as recursively cloning some of"
        " the objects making it up. Names are done through counting appearances of each class,"
        " this ensures fixed naming, dump them manually to check what their new names are."
    ),
)
def clone_bpd(args: argparse.Namespace) -> None:  # noqa: D103
    src = parse_object(args.base)
    if src is None:
        return
    if not src.Class._inherits(unrealsdk.find_class("BehaviorProviderDefinition")):
        logging.error(f"Object '{src.PathName(src)}' must be a 'BehaviorProviderDefinition'!")
        return

    outer, name = parse_clone_target(args.clone, src.Class.Name)
    if name is None:
        return

    cloned = clone_object(src, outer, name)
    if cloned is None:
        return
    fixup_bpd(cloned, {})


clone_bpd.add_argument("base", help="The bpd to create a copy of.")
clone_bpd.add_argument("clone", help="The name of the clone to create.")
clone_bpd.add_argument(
    "-x",
    "--suppress-exists",
    action="store_true",
    help="Deprecated, does nothing. See 'clone_dbg_suppress_exists' instead.",
)
