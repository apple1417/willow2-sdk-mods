import unrealsdk
from typing import Dict

from Mods.ModMenu import Game, Options

from . import ABCCheat, ABCToggleableCheat, SDKHook


class OneShot(ABCToggleableCheat):
    Name = "One Shot Mode"
    KeybindName = "Toggle One Shot Mode"

    def __init__(self) -> None:
        super().__init__()
        self.CheatOptions = [Options.Hidden("Disable One Shot Mode in TPS", StartingValue=False)]

    def GetHooks(self) -> Dict[str, SDKHook]:
        if Game.GetCurrent() == Game.TPS and self.CheatOptions[0].CurrentValue:  # type: ignore
            return {}

        def TakeDamage(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            pc = unrealsdk.GetEngine().GamePlayers[0].Actor

            if params.InstigatedBy != pc:
                return True

            if not self.IsOn:
                return True

            game = unrealsdk.FindAll("WillowCoopGameInfo")[-1]
            if game.IsFriendlyFire(caller, params.InstigatedBy.Pawn):
                return True

            caller.SetShieldStrength(0)
            # Try set the health to 1 so that your shot kills them, giving xp
            # Only do it if they have more than 1 health though, so that you don't get stuck in a
            #  loop if you somehow deal less than 1 damage
            if caller.GetHealth() > 1:
                caller.SetHealth(1)
            else:
                caller.SetHealth(0)

            return True

        return {
            "WillowGame.WillowAIPawn.TakeDamage": TakeDamage,
            "WillowGame.WillowVehicle.TakeDamage": TakeDamage
        }


class KillAll(ABCCheat):
    Name = "Kill All"
    KeybindName = "Kill All"

    def OnPress(self) -> None:
        player_pawn = unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn
        # The current WorldInfo object keeps a linked list of all extant pawns:
        pawn = unrealsdk.GetEngine().GetCurrentWorldInfo().PawnList
        while pawn is not None:
            # A WillowPawn's "enemy status" is determined by the GetOpinion method:
            if pawn.GetOpinion and pawn.GetOpinion(player_pawn) != 2: #OPINION_Friendly
                # Necessary to prevente infinite loops with parent/children:
                if pawn.MyWillowMind:
                    pawn.MyWillowMind.SpawnParent = None
                    pawn.MyWillowMind.SpawnChildren = ()
                pawn.SpawnParent = None
                pawn.Died(None, None, ())
            pawn = pawn.NextPawn    
