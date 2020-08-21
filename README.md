# Minecraft Battle Royale Server
A python script which uses minecraft server commands to set up battle royale style match for you and your friends. Controlled with an easy to use web interface. 

### Installing
Assuming you know how to set up your own minecraft server already. Working on python 3.7.5 with minecraft 1.15.2

1. Download repository
2. Download the minecraft server: https://launcher.mojang.com/v1/objects/bb2b6b1aefcd70dfd1892149ac3a215f6c636b07/server.jar and add it to the "./smallsonsbattleroyale/minecraft_server_1_15_2" directory
3. Start the server and accept the EULA
4. Navigate to the repository root directory "./smallsonsbattleroyale/"
4. Build a python virtual enviornment, activate and install modules from requirements.txt
```
#set up a virtual enviornment
python -m venv env
#activate enviornment
.\br_env\Scripts\activate
#update pip
pip install --upgrade pip
#install packages
pip install -r ./smallsonsbattleroyale/env/requirements.txt
```
4. Navigate to ./minecraft_server_1_15_2 and start the hunger games script.
```
python hunger_games.py
```

## Getting Started
You can navigate to localhost:8000 to view the web interface. Use controls to modify team composition and arena settings.
![](img/webpage_interface.JPG)

Gameplay:
![](img/in_game.png)

## How it Works
![](img/flow.JPG)
