#############################################

from traceback import print_exc as pe
import io

#############################################

from utils.chess import getvariantboard, variantnameofvariantkey, variantkeyofvariantname
from utils.chess import treeofgamenode, sanext
import chess
import chess.pgn

#############################################

class Req:
    def __init__(self, reqobj = {}):
        self.kind = None
        self.id = None
        self.uid = "mockuser"
        self.newgame = False
        self.variantkey = "standard"
        self.fen = None
        self.pgn = None
        self.line = []
        try:
            for key, value in reqobj.items():
                self.__dict__[key] = value
        except:
            pe()

    def res(self, obj):        
        obj["id"] = self.id
        obj["uid"] = self.uid
        return obj

def serverlogic(reqobj):    
    req = Req(reqobj)
    #print(req)
    if req.kind:
        try:
            return eval("{}(req)".format(req.kind))
        except:
            pe()
            return({
                "kind": "servererror"
            })
    return({
        "kind": "unknownrequest"
    })

#############################################

def connected(req):
    return req.res({
        "kind": "connectedack"
    })

#############################################

class ClientGame:
    def fen(self):
        return self.currentnode.board().fen()

    def __init__(self, variantkey, pgn, fen):        
        self.variantkey = variantkey
        if pgn:                        
            pgnio = io.StringIO(pgn)
            game = chess.pgn.read_game(pgnio)                 
            self.variantkey = variantkeyofvariantname(game.headers.pop("Variant", self.variantkey))
            game.headers["Variant"] = variantnameofvariantkey(self.variantkey)
            self.rootnode = game
            self.currentnode = self.rootnode                    
            currentline = self.rootnode.headers.pop("CurrentLine", None)
            if currentline:
                rootfen = self.rootnode.board().fen()
                setuppgn = "[Variant \"{}\"]\n[FEN \"{}\"]\n[SetUp \"1\"]\n\n{}".format(variantkey, rootfen, currentline)                                                
                pgnio = io.StringIO(setuppgn)
                game = chess.pgn.read_game(pgnio)                
                for move in game.mainline_moves():                                        
                    self.currentnode = self.currentnode.variation(move)                                    
            return
        board = getvariantboard(variantkey)        
        if fen:
            board.set_fen(fen)        
        self.rootnode = chess.pgn.Game.from_board(board)
        self.currentnode = self.rootnode        

    def mergegame(self, dstgame, srcgame):        
        srccomment = srcgame.comment
        if not ( srccomment == "" ):
            dstgame.comment = srccomment
        for variation in srcgame.variations:
            move = variation.move
            srcgamenext = srcgame.variation(move)
            try:                
                dstgamenext = dstgame.variation(move)
            except:
                dstgamenext = dstgame.add_main_variation(move)    
            self.mergegame(dstgamenext, srcgamenext)                       

    def mergepgn(self, pgn):
        pgn = pgn.replace("\r", "")
        if not "\n\n" in pgn:
            pgn = "\n" + pgn
        if not "SetUp" in pgn:
            pgn = "[SetUp \"1\"]\n{}".format(pgn)
        if not "FEN" in pgn:
            pgn = "[FEN \"{}\"]\n{}".format(self.rootnode.board().fen(), pgn)
        if not "Variant" in pgn:
            pgn = "[Variant \"{}\"]\n{}".format(self.variantkey, pgn)        
        print("merge pgn")
        print(pgn)
        pgnio = io.StringIO(pgn)
        srcgame = chess.pgn.read_game(pgnio)                 
        self.mergegame(self.rootnode, srcgame)

    def pgn(self):
        self.rootnode.headers.pop("CurrentLine", None)
        exporter = chess.pgn.StringExporter(columns=None, headers=True, variations=True, comments=True)
        pgn = self.rootnode.accept(exporter)            
        reportpgn = "[CurrentLine \"{}\"]\n{}".format(self.currentlinepgn(), pgn)        
        return reportpgn
    
    def makealgebmove(self, algeb):
        move = chess.Move.from_uci(algeb)
        if self.currentnode.board().is_legal(move):
            try:                
                self.currentnode = self.currentnode.variation(move)                
            except:
                self.currentnode = self.currentnode.add_main_variation(move)                            
        else:
            print("illegal move")

    def makesanmove(self, san):
        move = self.currentnode.board().parse_san(san)
        self.makealgebmove(move.uci())

    def setline(self, line):
        self.currentnode = self.rootnode
        for san in line:
            self.makesanmove(san)

    def delmove(self):
        if not self.currentnode.move:            
            return        
        move = self.currentnode.move        
        self.currentnode = self.currentnode.parent
        self.currentnode.remove_variation(move)                        

    def tobegin(self):
        while self.backmove():
            pass

    def backmove(self):
        if not self.currentnode.parent:            
            return False
        self.currentnode = self.currentnode.parent                        
        return True

    def forwardmove(self):
        try:
            self.currentnode = self.currentnode.variation(0)                        
            return True
        except:            
            return False

    def toend(self):
        while self.forwardmove():
            pass

    def currentlinemoves(self):
        moves = []
        cursor = self.currentnode
        while cursor.parent:
            moves = [cursor.move] + moves
            cursor = cursor.parent
        return moves

    def getline(self):
        testboard = self.rootnode.board()
        line = []
        for move in self.currentlinemoves():            
            line.append(sanext(testboard, move))
            testboard.push(move)
        return line

    def currentlinepgn(self):
        testboard = self.rootnode.board()
        for move in self.currentlinemoves():
            testboard.push(move)
        testgame = chess.pgn.Game.from_board(testboard)
        exporter = chess.pgn.StringExporter(columns=None, headers=False, variations=False, comments=False)
        currentlinepgn = testgame.accept(exporter)    
        return currentlinepgn

clientgames = {}

def setgame(clientgame):    
    fen = clientgame.fen()
    pgn = clientgame.pgn()
    variantkey = clientgame.variantkey
    tree = treeofgamenode(clientgame.rootnode)
    line = clientgame.getline()
    return {
        "kind": "setboard",
        "variantkey": variantkey,
        "fen": fen,
        "pgn": pgn,
        "tree": tree,
        "line": line
    }

def getboard(req):
    global clientgames
    if ( req.uid in clientgames ) and ( not req.newgame ):
        clientgame = clientgames[req.uid]
    else:
        clientgame = ClientGame(req.variantkey, req.pgn, req.fen)
        clientgames[req.uid] = clientgame
    return req.res(setgame(clientgame))

def makealgebmove(req):
    global clientgames
    clientgame = clientgames[req.uid]    
    clientgame.makealgebmove(req.algeb)
    return req.res(setgame(clientgame))

def setline(req):
    global clientgames
    clientgame = clientgames[req.uid]    
    clientgame.setline(req.line)
    return req.res(setgame(clientgame))

def delmove(req):
    global clientgames
    clientgame = clientgames[req.uid]        
    clientgame.delmove()
    return req.res(setgame(clientgame))

def tobegin(req):
    global clientgames
    clientgame = clientgames[req.uid]        
    clientgame.tobegin()
    return req.res(setgame(clientgame))

def backmove(req):
    global clientgames
    clientgame = clientgames[req.uid]        
    clientgame.backmove()
    return req.res(setgame(clientgame))

def forwardmove(req):
    global clientgames
    clientgame = clientgames[req.uid]        
    clientgame.forwardmove()
    return req.res(setgame(clientgame))

def toend(req):
    global clientgames
    clientgame = clientgames[req.uid]        
    clientgame.toend()
    return req.res(setgame(clientgame))

def mergepgn(req):
    global clientgames
    clientgame = clientgames[req.uid]        
    clientgame.mergepgn(req.pgn)
    return req.res(setgame(clientgame))

#############################################
