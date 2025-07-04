from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from enum import auto

    from mods_base import Game
    from unrealsdk.unreal._uenum import UnrealEnum  # pyright: ignore[reportMissingModuleSource]

    class EChangeStatus(UnrealEnum):
        CHANGE_Toggle = auto()
        CHANGE_Enable = auto()
        CHANGE_Disable = auto()

    class ECurrencyType(UnrealEnum):
        # Skipping the reserved values
        CURRENCY_Credits = auto()
        CURRENCY_Eridium = auto()
        CURRENCY_SeraphCrystals = auto()

    class EInteractionIcons(UnrealEnum):
        # Skipping a lot of values we don't care about
        INTERACTION_ICON_Heal = auto()
        INTERACTION_ICON_Gunner = auto()
        INTERACTION_ICON_Open = auto()

    class ENetRole(UnrealEnum):
        ROLE_None = auto()
        ROLE_SimulatedProxy = auto()
        ROLE_AutonomousProxy = auto()
        ROLE_Authority = auto()

    class EShopType(UnrealEnum):
        SType_Weapons = auto()
        SType_Items = auto()
        SType_Health = auto()
        SType_BlackMarket = auto()

    class ESkillEventType(UnrealEnum):
        # Skipping a lot of values we don't care about
        if Game.get_current() is Game.TPS:
            SEVT_OnPaidCashForUse = auto()

    class ETransactionStatus(UnrealEnum):
        TS_TransactionInProgress = auto()
        TS_TransactionComplete = auto()
        TS_TransactionFailed = auto()

    class EUsabilityType(UnrealEnum):
        UT_Primary = auto()
        UT_Secondary = auto()

    class PlayerMark(UnrealEnum):
        PM_Trash = auto()
        PM_Standard = auto()
        PM_Favorite = auto()
else:
    import unrealsdk

    EChangeStatus = unrealsdk.find_enum("EChangeStatus")
    ECurrencyType = unrealsdk.find_enum("ECurrencyType")
    EInteractionIcons = unrealsdk.find_enum("EInteractionIcons")
    ENetRole = unrealsdk.find_enum("ENetRole")
    EShopType = unrealsdk.find_enum("EShopType")
    ESkillEventType = unrealsdk.find_enum("ESkillEventType")
    ETransactionStatus = unrealsdk.find_enum("ETransactionStatus")
    EUsabilityType = unrealsdk.find_enum("EUsabilityType")
    PlayerMark = unrealsdk.find_enum("PlayerMark")
