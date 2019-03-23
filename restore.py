###################################################

from utils.file import read_json_from_file

###################################################

import firebase_admin
from firebase_admin import credentials, firestore

###################################################

THEGAMEDATA_PATH = "thegamedata"

###################################################

cred = credentials.Certificate('firebase/sacckey.json')
default_app = firebase_admin.initialize_app(cred)    
db = firestore.client()
print("firebase initialized", db)

###################################################

obj = read_json_from_file("backup/pgn.json", {})

gamedatacoll = db.collection(THEGAMEDATA_PATH)
thegamepgn_docref = gamedatacoll.document("pgn")

thegamepgn_docref.set(obj)

print("restored to", obj)

###################################################
