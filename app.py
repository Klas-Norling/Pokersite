from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, emit, send, SocketIO
import random
from string import ascii_uppercase
from create_database import User
user=User()
app = Flask(__name__)
app.config["SECRET_KEY"] = "hjhjsdahhds"
socketio = SocketIO(app)

@app.route("/", methods=["POST", "GET"])
def home():

    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        betting = request.form.get("betting")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name, betting=betting)
        
        if not betting:
            return render_template("home.html", error="Please enter a betting amount.", code=code, name=name)
        
        if join != False and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name, betting=betting)
        
        room = code
        if create != False:
            room = user.generate_unique_code()
            print(room, "room numbe is here")

        elif user.room_exists(code)==False:
            return render_template("home.html", error="Room does not exist.", code=code, name=name, betting=betting)
        
        session["room"] = room
        session["name"] = name
        session["betting"] = betting
        return redirect(url_for("room"))

    return render_template("home.html")

@app.route("/room")
def room():
    
    room=session.get("room")
    name=session.get("name")
    NonExistent=user.room_exists(room)
    if room is None or name is None or NonExistent==False:
        return redirect(url_for("home"))
    
    return render_template("room.html",code=room,name=name) #also add in messages.

@socketio.on("message")
def message(data):
    room=session.get("room")
    name=session.get("name")
    message=name+": "+data["data"]
    print("HELLLLLLLOOOOOOOOO")
    print(message)
    if user.room_exists(room) ==False:
        return
    
    content = {
        "name":session.get("name"), 
        "message": data["data"]
    }

    send(content, to=room)
    user.insert_comment(name,room,message)
    print(f"{session.get('name')} said: {data['data']}")


@socketio.on("connect")
def connect(auth):
    room=session.get("room")
    name=session.get("name")
    betting=session.get("betting")
    print("CONNECT ERROR??====================================BEGIN")
    if not room or not name:
        print("here")
        return redirect('/')
    if user.room_exists(room)==False:
        print("also here IM IN HERE")
        leave_room(room)
        return redirect('/')
    print("am i also here")
    join_room(room)
    send({"name": name, "message":"has joined the room"}, to=room)
    maxplayers=user.member_exists(room)
    print(maxplayers," Amount Maxplayers")
    if maxplayers == False:
        print("im in here")
        maxplayers=1
    else:
        maxplayers=maxplayers+1
    emit('update_values',{'data':maxplayers},to=room)
    emit('update_bettingamount',{'data':betting},broadcast=False)
    user.add_member(room)
    print(f"{name} has joined room {room}")
    print("CONNECT ERROR??====================================END")

@socketio.on("disconnect")
def disconnect():
    room=session.get("room")
    name=session.get("name")
    print("DISCONNECT ERROR??====================================BEGIN")
    maxplayers=user.member_exists(room)-1
    leave_room(room)
    print("Before: ",user.show_rooms)
    if user.room_exists(room)==True:
        user.sub_member(room)
        print("user deleted")
        if user.member_exists(room)==False:
            print("room deleted")
            print(room)
            user.del_room(room)
            return redirect('/')
    
    print("After: ",user.show_rooms)

    send({"name": name, "message":"has left the room"}, to=room)
    emit('update_values',{'data':maxplayers},to=room)
    print(f"{name} has left the room {room}")
    print("DISCONNECT ERROR??====================================END")

@socketio.on("button")
def button(data):
    value=data["data"]
    betting=session.get("betting")
    if value == "check":                #check function
        print("check is here")
        emit('button_response',{'response':"check is here"},broadcast=False)

    elif value == "fold":                #fold function
        print("fold is here")
        emit('button_response',{'response':"fold is here"},broadcast=False)

    else:                               #Bet function
        print(value, "bet is here")
        print(betting)

        if(int(betting)<=0):
            emit('update_bettingamount',{'data':"YOU HAVE NO MONEY, YOU LOSE"},broadcast=False)
            session["betting"]=0
            print("FIRST")
        elif((int(betting)-int(value))<0):
            newvalue=int(betting)-int(value)
            value=int(value)+newvalue
            session["betting"]=value
            print(value)
            emit('button_response',{'response':"bet is here"},broadcast=False)
            emit('update_bettingamount',{'data':value},broadcast=False)
            print("SEC")
        else:
            value=int(betting)-int(value)
            session["betting"]=value
            print(value)
            emit('button_response',{'response':"bet is here"},broadcast=False)
            emit('update_bettingamount',{'data':value},broadcast=False)
            print("Third")

if __name__ == "__main__":
    socketio.run(app, debug=True)