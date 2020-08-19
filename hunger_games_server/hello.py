from flask import Flask,jsonify,render_template, request
import os.path
import wexpect
import socket
import json
from waitress import serve
app = Flask(__name__, static_url_path='')


# import wexpect
# mc_server=wexpect.spawn('java -Xms4G -Xmx4G -jar "server (6).jar" nogui java',cwd=os.path.abspath("D:\\Google Drive Current\\minecraft_1.15.2"))

# @app.route('/')
# def hello_world():
#     return 'Hello, WorlAAd!'


# @app.route('/')
# def hello_world():
#     return app.send_static_file("hobbies_flask.html")
@app.before_first_request
def declareStuff():
    global HOST
    global PORT
    HOST = 'localhost'    # The remote host
    PORT = 50008           # The same port as used by the server

@app.route('/')
def hello_world():
    return render_template("index_v2.html")

@app.route('/_stuff',methods=['GET'])
def stuff():
    send_data=["update_teams"]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(bytes(json.dumps(send_data),encoding="utf-8"))
        data = s.recv(1024)
        return data.decode("utf-8")
    # return jsonify(word=data.decode("utf-8"))

@app.route('/handle_data', methods=['POST'])
def handle_data():
    player_list = request.form['myData']
    team = request.form['Team']
    send_data=["ch_team"]+[team]+[player_list]
    print("hi")
    print("hi")
    print("hi")
    print(player_list)
    print(team)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(bytes(json.dumps(send_data),encoding="utf-8"))
        data = s.recv(1024)

    return("done")

@app.route('/handle_start_size', methods=['POST'])
def get_start_size_data():
    size = request.form['data']
    print(size)
    send_data=["worldborder_start"]+[size]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(bytes(json.dumps(send_data),encoding="utf-8"))
        return("ok")

@app.route('/handle_end_size', methods=['POST'])
def get_end_size_data():
    size = request.form['data']
    send_data=["worldborder_end"]+[size]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(bytes(json.dumps(send_data),encoding="utf-8"))
        return("ok")

@app.route('/handle_time', methods=['POST'])
def get_time_data():
    size = request.form['data']
    send_data=["worldborder_time_move"]+[size]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(bytes(json.dumps(send_data),encoding="utf-8"))
        return("ok")

@app.route('/handle_start', methods=['POST'])
def start_game():
    size = request.form['data']
    send_data=["start_game"]+[size]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(bytes(json.dumps(send_data),encoding="utf-8"))
        return("ok")

# if __name__ == '__main__':
#     app.run()

if __name__ == "__main__":
   #app.run() ##Replaced with below code to run it using waitress 
   serve(app, host='0.0.0.0', port=8000)