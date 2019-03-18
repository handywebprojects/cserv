#############################################

from traceback import print_exc as pe
import io
import uuid
import firebase_admin
from firebase_admin import credentials, firestore

#############################################

from utils.chess import getvariantboard, variantnameofvariantkey, variantkeyofvariantname
from utils.chess import treeofgamenode, sanext
import chess
import chess.pgn
from utils.http import geturl

#############################################

USERS_PATH = "users"

try:
    cred = credentials.Certificate('firebase/sacckey.json')
    default_app = firebase_admin.initialize_app(cred)    
    db = firestore.client()
    print("firebase initialized", db)

    userscoll = db.collection(USERS_PATH)
except:
    #pe()
    print("firebase could not be initialized")

#############################################

class Req:
    def __init__(self, reqobj = {}):
        global users
        self.kind = None
        self.id = None
        self.uid = "mockuser"
        self.username = "Anonymous"
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
        self.user = User(self.uid)
        if not ( self.uid == "mockuser" ):
            if not ( self.uid in users ):
                self.user.getdb()
            else:
                self.user = users[self.uid]
        
        print("request", self.kind, self.user)

    def res(self, obj, alert = None):        
        obj["id"] = self.id
        obj["uid"] = self.uid        
        obj["username"] = self.username
        if alert:
            obj["alertmessage"] = alert
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
        #print("merge pgn")
        #print(pgn)
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
    if req.user.verified:        
        clientgame.makealgebmove(req.algeb)
        return req.res(setgame(clientgame))
    else:
        return req.res(setgame(clientgame), "You have to be logged in to make a move!")

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

def auth(req):
    global users
    user = User(req.uid).getdb()

    return req.res({
        "kind": "auth",
        "user": user.__dict__
    })

users = {}

class User:
    def __init__(self, uid):
        global users
        self.uid = uid                
        self.username = "Anonymous"
        self.code = None
        self.verified = False
        self.side = None

    def setusername(self, username):
        self.username = username
        return self

    def setcode(self, code):
        self.code = code
        return self

    def setverified(self, verified):
        self.verified = verified
        return self

    def setside(self, side):
        self.side = side
        return self

    def setdb(self):
        global userscoll, users
        doc = userscoll.document(self.uid)
        userdata = self.__dict__
        #print("setting user in db", userdata)
        doc.set(userdata)
        self.storelocal()

    def storelocal(self):
        users[self.uid] = self
        return self

    def fromdata(self, data):
        self.username = data.get("username", "Anonymous")
        self.code = data.get("code", None)
        self.verified = data.get("verified", False)
        self.side = data.get("side", None)
        return self

    def getdb(self):
        global userscoll, users        
        doc = userscoll.document(self.uid).get()
        #print("getting data for", self)
        try:
            data = doc.to_dict()
            #print("received data", data)
            self.fromdata(data)
            #print("set user to", self)
        except:
            #print("no data")
            pass
        return self.storelocal()

    def __repr__(self):
        return "[ User {} {} {} {}]".format(self.uid, self.username, self.code, self.verified)

def getuser(uid):
    global users
    if uid in users:
        return users[uid]
    return User(uid)

def signin(req):    
    #print("signing in with username [ {} ]".format(req.username))

    genuuid = uuid.uuid1().hex
    code = uuid.uuid1().hex

    user = User(genuuid).setusername(req.username).setcode(code).storelocal()

    return req.res({
        "kind": "signin",
        "status": "ok",
        "setuid": genuuid,
        "setcode": code
    })

def vercode(req):    
    global userscoll
    #print("verifying code for uid [ {} ]".format(req.tempuid))

    user = getuser(req.tempuid)

    #print(user)

    profile = geturl("https://lichess.org/@/{}".format(req.username), verbose = True)

    verified = user.code in profile

    if verified:            
        sameusers = userscoll.where("username", "==", user.username).get()    

        for doc in sameusers:
            data = doc.to_dict()
            #print("user doc already exists", data)
            user = User(data["uid"]).fromdata(data)
            break

        user.setverified(verified)

        user.setdb()

    req.uid = user.uid

    return req.res({
        "kind": "codeverified",
        "verified": verified,
        "user": user.__dict__
    })

def setside(req):
    if req.user.verified:
        #print("set side", req.side, req.user)
        req.user.setside(req.side).setdb()
        return req.res({
            "kind": "auth",
            "user": req.user.__dict__
        })
    else:
        return req.res({
            "kind": "setsidefailed"
        }, "Log in to set side.")

#############################################
