curl --url https://launcher.mojang.com/v1/objects/bb2b6b1aefcd70dfd1892149ac3a215f6c636b07/server.jar --output ./minecraft_server_1_15_2/server.jar
python -m venv env
CALL .\env\Scripts\activate
python -m pip install --upgrade pip
pip install -r ./env/requirements.txt
cd ./minecraft_server_1_15_2
server.jar
echo "Setup Complete."
pause