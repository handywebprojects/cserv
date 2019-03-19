#############################################

import chess
from chess.variant import find_variant
from chess.pgn import read_game

#############################################

VARIANT_KEYS = [    
    [ "standard", "Standard" ],
    [ "chess960", "Chess960" ],
    [ "crazyhouse", "Crazyhouse" ],
    [ "antichess", "Giveaway" ],
    [ "atomic", "Atomic" ],
    [ "horde", "Horde" ],
    [ "kingOfTheHill", "King of the Hill" ],
    [ "racingKings", "Racing Kings" ],
    [ "threeCheck", "Three-check" ]
]

#############################################

def variantnameofvariantkey(variantkey):
    for item in VARIANT_KEYS:
        if item[0] == variantkey:
            return item[1]
    return "Standard"

def variantkeyofvariantname(variantname):
    for item in VARIANT_KEYS:
        if item[1] == variantname:
            return item[0]
    return "standard"

def getvariantboard(variantkey = "standard"):
    if variantkey == "standard":
        return chess.Board()
    elif variantkey == "chess960":
        return chess.Board(chess960 = True)
    elif variantkey == "fromPosition":
        return chess.Board()
    else:
        VariantBoard = find_variant(variantkey)
        return VariantBoard()

def sanext(board, move):
    san = board.san(move)
    fmn = board.fullmove_number
    turnblack = ( board.turn == chess.BLACK )
    sanext = "{}.".format(fmn)
    if turnblack:
        sanext += "."
    sanext += san
    return sanext

def stripsan(san):
    if ".." in san:
        parts = san.split("..")
        return parts[1]
    if "." in san:
        parts = san.split(".")
        return parts[1]
    return san

def treeofgamenode(gamenode):
        obj = {}
        for childnode in gamenode.variations:
            move = childnode.move
            board = gamenode.board()            
            obj[sanext(board, move)] = treeofgamenode(childnode)
        return obj

#############################################
