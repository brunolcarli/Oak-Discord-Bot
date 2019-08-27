import requests
import datetime

class Battle:
    winner = ""
    loser = ""
    date = ""
    meta_format = ""

    def __init__(self, winner, loser, date, meta_format):
        self.winner = winner
        self.loser = loser
        self.date = date
        self.meta_format = meta_format

    def validate(self, winner, loser):
        winnerOK = winner.strip().lower() == self.winner.lower()
        loserOK  = loser.strip().lower()  == self.loser.lower()

        error  = "Winner is not valid; " if not winnerOK else ""
        error += "Loser is not valid; "  if not loserOK  else ""
        
        return OperationResult(error=error)

class OperationResult:
    success = False
    error = "Not evaluated!"
    battle = None

    def __init__(self, battle = None, error = ""):
        self.battle = battle
        self.success = len(error) == 0
        self.error = error

def load_battle_replay(battle_url): 
    isShowdownReplay = battle_url.strip().find('://replay.pokemonshowdown.com/') > -1
    if not isShowdownReplay:        
        return OperationResult(error="Battle URL is not a valid Showdown battle replay")
    
    battle_metadata_url = battle_url.strip() + ".json"
    response = requests.get(url = battle_metadata_url)

    if response.status_code != 200:
        return OperationResult(error="Error getting replay metadata")

    battle_data = response.json()
    
    # loading result
    startIndex = battle_data["log"].index("|win|") + 5
    endIndex = battle_data["log"].find("\n", startIndex)
    winner = battle_data["log"][startIndex:endIndex]
    loser = battle_data["p1"] if battle_data["p2"].lower() == winner.lower() else battle_data["p2"]
    date = datetime.datetime.fromtimestamp(battle_data["uploadtime"]) + datetime.timedelta(hours=-3) # Brazil timezone offset from UTC

    battle = Battle(winner, loser, date, battle_data["format"])
    return OperationResult(battle=battle)





