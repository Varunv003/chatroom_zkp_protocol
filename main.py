from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase
from paillier.keygen import generate_keys
from paillier.crypto import encrypt, decrypt

app = Flask(__name__)
app.config["SECRET_KEY"] = "hjhjsdahhds"
socketio = SocketIO(app)

rooms = {}

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    
    return code

public_key, private_key = generate_keys()
def generate_proof(username):
    """Generates a proof that the user owns the username."""
    encrypted_username = encrypt(public_key, username)
    proof = {
        "encrypted_username": encrypted_username
    }
    return proof

def verify_proof(proof, username):
    """Verifies a proof that the user owns the username."""
    encrypted_username = proof["encrypted_username"]
    public_key = proof["public_key"]
    is_valid = decrypt(private_key, encrypted_username) == username
    return is_valid

@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name)

        if join != False and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)
        
        room = code
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist.", code=code, name=name)
        
        proof = generate_proof(name)

        data = {
            "name": name,
            "proof": proof
        }
        socketio.emit("message", data)

        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))
    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    data = socketio.receive()
    proof = data["proof"]

    is_valid = verify_proof(proof, session["name"])

    if not is_valid:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return 
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    message = f"{name} has entered the room"
    send(message, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

# @socketio.on("disconnect")
# def disconnect():
#     room = session.get("room")
#     name = session.get("name")
#     leave_room(room)

#     if room in rooms:
#         rooms[room]["members"] -= 1
#         if rooms[room]["members"] <= 0:
#             del rooms[room]
    
#     send({"name": name, "message": "has left the room"}, to=room)
#     print(f"{name} has left the room {room}")
@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")
if __name__ == "__main__":
    socketio.run(app, debug=True)

# protocol
# 1. The user creates a pair of public and private keys. The public key is shared with the chatroom app, while the private key is kept secret by the user.
# 2. When the user wants to join a chatroom, they generate a random challenge and encrypt it with their private key.
# 3. They then send the encrypted challenge to the chatroom app.
# 4. The chatroom app decrypts the challenge using the user's public key.
# 5. The chatroom app then generates a proof that the user knows the decryption key.
# 6. The user verifies the proof.
# 7. If the proof is valid, the chatroom app allows the user to join the chatroom.


# from flask import Flask, render_template, request, session, redirect, url_for
# from flask_socketio import join_room, leave_room, send, SocketIO
# import random
# from string import ascii_uppercase

# app = Flask(__name__)
# app.config["SECRET_KEY"] = "hjhjsdahhds"
# socketio = SocketIO(app)

# rooms = {}

# def generate_unique_code(length):
#     while True:
#         code = ""
#         for _ in range(length):
#             code += random.choice(ascii_uppercase)
        
#         if code not in rooms:
#             break
    
#     return code

# @app.route("/", methods=["POST", "GET"])
# def home():
#     session.clear()
#     if request.method == "POST":
#         name = request.form.get("name")
#         code = request.form.get("code")
#         join = request.form.get("join", False)
#         create = request.form.get("create", False)

#         if not name:
#             return render_template("home.html", error="Please enter a name.", code=code, name=name)

#         if join != False and not code:
#             return render_template("home.html", error="Please enter a room code.", code=code, name=name)
        
#         room = code
#         if create != False:
#             room = generate_unique_code(4)
#             rooms[room] = {"members": 0, "messages": []}
#         elif code not in rooms:
#             return render_template("home.html", error="Room does not exist.", code=code, name=name)
        
#         session["room"] = room
#         session["name"] = name
#         return redirect(url_for("room"))

#     return render_template("home.html")

# @app.route("/room")
# def room():
#     room = session.get("room")
#     if room is None or session.get("name") is None or room not in rooms:
#         return redirect(url_for("home"))

#     return render_template("room.html", code=room, messages=rooms[room]["messages"])

# @socketio.on("message")
# def message(data):
#     room = session.get("room")
#     if room not in rooms:
#         return 
    
#     content = {
#         "name": session.get("name"),
#         "message": data["data"]
#     }
#     send(content, to=room)
#     rooms[room]["messages"].append(content)
#     print(f"{session.get('name')} said: {data['data']}")

# @socketio.on("connect")
# def connect(auth):
#     room = session.get("room")
#     name = session.get("name")
#     if not room or not name:
#         return
#     if room not in rooms:
#         leave_room(room)
#         return
    
#     join_room(room)
#     send({"name": name, "message": "has entered the room"}, to=room)
#     rooms[room]["members"] += 1
#     print(f"{name} joined room {room}")

# @socketio.on("disconnect")
# def disconnect():
#     room = session.get("room")
#     name = session.get("name")
#     leave_room(room)

#     if room in rooms:
#         rooms[room]["members"] -= 1
#         if rooms[room]["members"] <= 0:
#             del rooms[room]
    
#     send({"name": name, "message": "has left the room"}, to=room)
#     print(f"{name} has left the room {room}")

# if __name__ == "__main__":
#     socketio.run(app, debug=True)

