#########################################################
# global imports

#########################################################

#########################################################
# local imports
from utils.file import read_json_from_file
from utils.http import posturl
#########################################################

#########################################################
# flask imports
from flask import Flask, render_template, request, Response, send_from_directory, redirect
#########################################################

#########################################################
# flask socketio imports
from flask_socketio import SocketIO, emit
#########################################################

#########################################################
# create app
app = Flask(__name__, static_url_path = '/static')
app.config['SECRET_KEY'] = 'secret!'
#########################################################

#########################################################
# mount socket
socketio = SocketIO(app)
#########################################################

#########################################################
# app routes
@app.route("/")
def index():    
    fbconfig = read_json_from_file("firebase/config.json", {})    
    return render_template("index.html", fbconfig = fbconfig)
#########################################################

#########################################################
# socketio event handler
@socketio.on("sioreq")
def handle_sioreq(reqobj):
    sid = request.sid
    #print("sioreq", sid, reqobj)
    resobj = posturl("http://localhost:4000/", jsonobj = reqobj, asjson = True, verbose = False)
    socketio.emit("siores", resobj, room = sid, namespace = "/")
#########################################################

#########################################################
# startup
def startup(port = 5000):
    socketio.run(app, port = port)
#########################################################

#########################################################
# main
if __name__ == '__main__':    
    startup()
#########################################################
