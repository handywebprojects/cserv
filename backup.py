###################################################

from utils.file import create_dir, write_json_to_file

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

create_dir("backup", verbose = True)

print("retrieving doc")
gamedatacoll = db.collection(THEGAMEDATA_PATH)
thegamepgn_docref = gamedatacoll.document("pgn")
thegamepgn_dict = thegamepgn_docref.get().to_dict()

print("writing json")
write_json_to_file("backup/pgn.json", thegamepgn_dict)

print("setting backup in db")
thegamepgn_backup_docref = gamedatacoll.document("backuppgn")
thegamepgn_backup_docref.set(thegamepgn_dict)

print("backup done")

###################################################
