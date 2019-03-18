###################################################

from os import environ
import heroku3

###################################################

from utils.ansi import pretty

###################################################

TOKEN = environ["FBSERV_TOKEN"]

###################################################

conn = heroku3.from_key(TOKEN)

try:
    conn.apps()["cserv"].delete()
    print("app destroyed")
except:
    print("could not destroy cserv")

try:
    conn.create_app(name = "cserv", stack_id_or_name = "heroku-18", region_id_or_name = "eu")
    print("app created")
except:
    print("could not create cserv")

for app in conn.apps():
    print(app, pretty(app.__dict__))

###################################################
