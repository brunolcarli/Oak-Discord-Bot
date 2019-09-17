"""
Módulo para fncionalidades dedicadas a dados do showdown.
"""

import datetime
import requests


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

    def validate(self, winner, loser, date):
        winner_is_ok = winner.strip().lower() == self.winner.lower()
        loser_is_ok = loser.strip().lower() == self.loser.lower()
        date_is_ok = abs(date - self.date).days <= 2

        error = "Winner is not valid; " if not winner_is_ok else ""
        error += "Loser is not valid; " if not loser_is_ok else ""
        error += "Date is not valid; " if not date_is_ok else ""

        return OperationResult(error=error)


class OperationResult:
    success = False
    error = "Not evaluated!"
    battle = None

    def __init__(self, battle=None, error=""):
        self.battle = battle
        self.success = len(error) == 0
        self.error = error


def load_battle_replay(battle_url):
    is_showdown_replay = battle_url.strip()\
                            .find('://replay.pokemonshowdown.com/') > -1

    if not is_showdown_replay:
        return OperationResult(
            error="Battle URL is not a valid Showdown battle replay"
        )

    battle_metadata_url = battle_url.strip() + ".json"
    response = requests.get(url=battle_metadata_url)

    if response.status_code != 200:
        return OperationResult(error="Error getting replay metadata")

    battle_data = response.json()

    # loading result
    start_index = battle_data["log"].index("|win|") + 5
    end_index = battle_data["log"].find("\n", start_index)
    winner = battle_data["log"][start_index:end_index]

    if battle_data["p2"].lower() == winner.lower():
        loser = battle_data["p1"]
    else:
        loser = battle_data["p2"]

    date = datetime.datetime.fromtimestamp(battle_data["uploadtime"]) + \
                datetime.timedelta(hours=-3)  # Brazil timezone offset from UTC
    battle = Battle(winner, loser, date, battle_data["format"])

    return OperationResult(battle=battle)
