from typing import Any

import unrealsdk
from mods_base import BoolOption, build_mod, hook
from unrealsdk import logging
from unrealsdk.hooks import Block
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

force_option = BoolOption(
    identifier="Force Offline Mode",
    value=False,
    description=(
        "Forces your game to never connect to SHiFT.\n"
        "This will apply next time you restart the game."
    ),
)
warning_option = BoolOption(
    identifier="Hide Offline Warning",
    value=True,
    description="Automatically hides the offline mode warning.",
)


@hook("WillowGame.WillowGFxDialogBox:DisplayOkBoxTextFromSpark")
def display_offline_warning(  # noqa: D103
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> type[Block] | None:
    if warning_option.value and args.Section == "dlgCouldNotConnectSHiFT":
        obj.Close()
        return Block
    return None


@hook("WillowGame.WillowGFxMoviePressStart:DoSparkAuthentication")
def do_spark_authentication(  # noqa: D103
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> type[Block] | None:
    if not force_option.value:
        return
    obj.ShouldStartSparkInitialization = False

    # Normally, offline mode hotfixes run the line:
    #   set Transient.GearboxAccountData_1 Services (Transient.SparkServiceConfiguration_0)

    # When we set the above bool, account data *_1* never gets created, we only have _0

    try:
        ss_0 = unrealsdk.find_object(
            "SparkServiceConfiguration",
            "Transient.SparkServiceConfiguration_0",
        )
        gad_0 = unrealsdk.find_object("GearboxAccountData", "Transient.GearboxAccountData_0")

        # Pre-set the array on _0 instead
        gad_0.Services = (ss_0,)

        # And try create a dummy _1 so that commands don't print an error message
        try:
            unrealsdk.find_object("GearboxAccountData", "Transient.GearboxAccountData_1")
        except ValueError:
            unrealsdk.construct_object(
                gad_0.Class,
                gad_0.Outer,
                "GearboxAccountData_1",
                flags=0x4000,
            )

    except ValueError:
        logging.error(
            "[Offline Helpers] Failed to set up alternate GearboxAccountData, you may get an error"
            " when executing text mods.",
        )


build_mod()
