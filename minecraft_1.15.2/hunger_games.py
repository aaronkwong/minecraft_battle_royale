
import socket
import os
import time
import pickle
import numpy as np
import copy
import wexpect
import json
import random
# import subprocess
# import time

# mc_server=subprocess.Popen('"C:/Program Files/Java/jre1.8.0_191/bin/java.exe" -Xms4G -Xmx4G -jar "D:/gd/minecraft_1.15.2/server (6).jar" nogui java',shell=False,stdout=subprocess.PIPE,stdin=subprocess.PIPE)
# mc_server.stdin.write(b'/time set midnight \n')
# #mc_server.stdin.close()
# mc_server.stdin.flush()

#this function takes a wexpect connection and returns the player list
#need to adda try catch to this
def capture_player_list(mc_server):
    #print(player_list)
    #the start and end of the substring we will be taking
    while(True):
        #print(mc_server)
        #this first line basically just flushed the buffer becaause we want only the output of "/list". It will be overwritten
        throwRA=mc_server.read_nonblocking()
        mc_server.sendline('/list')
        time.sleep(0.2)
        player_list=mc_server.read_nonblocking()
        if ('20 players online:' in player_list) and (not('lost connection: Disconnected' in player_list)) and (not('the game' in player_list)) and player_list.count("[Server thread/INFO]")==1:
            print(player_list)
            start=player_list.find('20 players online:')+len('20 players online:')+1
            end=player_list.rfind('\r\n')
            players=player_list[start:end].replace(",","").split(" ")
            break
    return(players)

#stock server 
def stop_server(mc_server):
    mc_server.sendline('/stop')

#create team block
def create_teams():
    landing=[""]*10
    team1=[""]*10
    team2=[""]*10
    team3=[""]*10
    team4=[""]*10
    return([landing,team1,team2,team3,team4])

#for soem reason    this function is working on global varibales.
def update_position(team_data,x,y,new_value):
    data=copy.deepcopy(team_data)
    data[x][y]=new_value
    return(data)
    # data=team_data
    # data[x][y]=new_value
    #return(data)


#team_to_add_to is an integer with the group number landing(0), team1(1), team2(2), team3(3), team4(4)
def add_to_team(team_data,team_to_add_to,name):
    #for the team which will have a member added we should find where the next empty slot is
    # team_data[team_to_add_to]
    filled_already=[]
    for poss in team_data[team_to_add_to]:
        filled_already.append(not(poss==""))
    if sum(filled_already)>9:
        #to prevent an error out if over 10 players in one team just return unchanged
        return(team_data)
    else:
        new_free_position=sum(filled_already)
        #print(new_free_position)
        return(update_position(team_data,x=team_to_add_to,y=new_free_position,new_value=name))

def clean_slots(the_list):
    if the_list[the_list.index("")+1]=="":
        return(the_list)
    else:
        new_list=the_list[0:the_list.index("")] + the_list[the_list.index("")+1:10] + [""]
        # new_list.append(the_list[0:the_list.index("")])
        # new_list.append(the_list[the_list.index("")+1:9])
        # new_list.append("")
        return(new_list)

#remove player from a team
def remove_from_team(team_data,team_to_remove_from,name):
    team_data_copy=copy.deepcopy(team_data)
    temp_team=team_data_copy[team_to_remove_from]
    removed_team=[]
    for i in temp_team:
        if name==i:
            removed_team.append("")
        else:
            removed_team.append(i)
    #the slot is now empty. players below should be bumped up
    team_data_copy[team_to_remove_from]=clean_slots(removed_team)
    return(team_data_copy)

#find the position of a player in the teams
def find_member_on_team(mylist,char):
    for sub_list in mylist:
        if char in sub_list:
            return (mylist.index(sub_list), sub_list.index(char))
    raise ValueError("'{char}' is not in list".format(char = char))

#update the team data and account for any logins or disconnects
def check_current_login(mc_server,accounted,team_data):
    active_players=capture_player_list(mc_server)
    #find any players that are new logins
    player_unaccounted=[]
    for i in active_players:
        player_unaccounted.append(not(i in accounted))
        print(i)
    player_unaccounted=np.array(active_players)[np.array(player_unaccounted)]
    #if there are new players, we should add them to the landing page
    if not(len(player_unaccounted)==0):
        for player in player_unaccounted:
            team_data=add_to_team(team_data,team_to_add_to=0,name=player)
            accounted.append(player)
    #now check for player which have logged out
    player_left=[]
    for i in accounted:
        player_left.append(not(i in active_players))
    #get names of players that logged out
    player_logged=np.array(accounted)[np.array(player_left)]
    print(len(player_logged))
    if not(len(player_logged)==0):
        print("player left!")
        for player in player_logged:
            #need add a function to find where the person is if they moved a team already
            a,b=find_member_on_team(team_data,player)
            team_data=remove_from_team(team_data,a,name=player)
            print(team_data)
            print(player)
        #remove these players from accounted
        accounted=np.array(accounted)[np.array([not i for i in player_left])]
        accounted=accounted.tolist()
    #return all varibales that change
    return(team_data,accounted)

def move_player_to_team(team_data,player_to_move,new_team):
    for sub_list in team_data:
        if player_to_move in sub_list:
            x,y=team_data.index(sub_list), sub_list.index(player_to_move)
            team_data=remove_from_team(team_data=team_data,team_to_remove_from=x,name=player_to_move)
            team_data=add_to_team(team_data=team_data,team_to_add_to=new_team,name=player_to_move)
            return(team_data)
    print("Could not find the selected player. Maybe they logged out")
    print(player_to_move)
    return(team_data)

def change_player_gamemode(mc_server,player_name,mode):
    mc_server.sendline('/gamemode '+mode+" "+player_name)

def teleport_player(mc_server,player_name,x,y,z):
    mc_server.sendline('/teleport '+str(player_name)+" "+str(x)+" "+str(y)+" "+str(z))

def create_team(mc_server,team_name):
    mc_server.sendline('/team add '+team_name)

def add_member_to_team(mc_server,team_name,member_to_add):
    mc_server.sendline('/team join '+team_name+" "+member_to_add)

def kill_all_players(mc_server):
    mc_server.sendline('/kill @a')

def set_world_border(mc_server,worldborder_size,time=""):
    if time=="":
        mc_server.sendline('/worldborder set '+str(worldborder_size))
    else:
        mc_server.sendline('/worldborder set '+str(worldborder_size)+" "+str(time))

def calculate_teams_and_spawns(team_data,worldborder_center,worldborder_start_size,worldborder_end_size,worldborder_collpase_time):
    #first lets find the number of teams which contain at least one player
    #we will fill active_team with the indexes of [team_data] which are the teams which will play
    active_team_indexes=[]
    for sublist in team_data:
        for underlist in sublist:
            if underlist!="":
                active_team_indexes.append(team_data.index(sublist))
                break
    print(active_team_indexes)
    if len(active_team_indexes)==0:
        print("Error. no active teams found.")
    else:
        print("teams found.")
        #now lets calculate the possible spawn locations. 
        xhigh=worldborder_center[0]+(worldborder_start_size/2)
        xlow=worldborder_center[0]-(worldborder_start_size/2)
        yhigh=worldborder_center[1]+(worldborder_start_size/2)
        ylow=worldborder_center[1]-(worldborder_start_size/2)
        loc_1=[xhigh,ylow]
        loc_2=[xlow,yhigh]
        loc_3=[xlow,ylow]
        loc_4=[xhigh,yhigh]
        possible_spawns=[loc_1,loc_2,loc_3,loc_4]
        random.shuffle(possible_spawns)
        return(active_team_indexes,possible_spawns[0:len(active_team_indexes)])

# calculate_teams_and_spawns(test.teams,test.worldborder_center_location,test.worldborder_start_size,test.worldborder_end_size,3600)







class player:
    def __init__(self):
        self.teams=create_teams()
        self.mc_server=wexpect.spawn('java -Xms4G -Xmx4G -jar "server (6).jar" nogui java',cwd=os.path.abspath("D:\\gd\\minecraft_1.15.2"))
        self.accounted=[]
        self.worldborder_center_location=[0,0]
        self.worldborder_start_size=1000
        self.worldborder_end_size=100
        self.worldborder_collapse_time=3600
        self.initiate_match_teams_indexes=[]
        self.initiate_match_teams_spawn_locations=[]
        self.total_players=[]
        self.check_players_time=0
    def check_players(self):
        if (time.time()-self.check_players_time)>1:
            try:
                self.teams,self.accounted=check_current_login(mc_server=self.mc_server,accounted=self.accounted,team_data=self.teams)
                self.check_players_time=time.time()
            except:
                print("check_players_error_rebound")
    def stop_pserver(self):
        stop_server(self.mc_server)
    def move_player(self,player_to_move,new_team):
        self.teams=move_player_to_team(team_data=self.teams,player_to_move=player_to_move,new_team=new_team)
    def pre_match_calc(self):
        self.initiate_match_teams_indexes,self.initiate_match_teams_spawn_locations=calculate_teams_and_spawns(team_data=self.teams,worldborder_center=self.worldborder_center_location,worldborder_start_size=self.worldborder_start_size,worldborder_end_size=self.worldborder_end_size,worldborder_collpase_time=self.worldborder_collapse_time)
    def make_teams(self):
        #for each team that will play create a team
        for i in self.initiate_match_teams_indexes:
            #make a clean list of all players. make empty to fill
            #create the team name
            team_name_assign=str("team_"+str(i))
            print(team_name_assign)
            create_team(mc_server=self.mc_server,team_name=team_name_assign)
            print("good")
            #for each team add the members
            players_in_team=[]
            print("good1")
            for player_in_list in self.teams[i]:
                if player_in_list!="":
                    players_in_team.append(player_in_list)
            print(players_in_team)
            self.total_players.append(players_in_team)
            print(self.total_players)
            #now we have the list of players, per team add them to the team
            print("good2")
            for member in players_in_team:
                add_member_to_team(mc_server=self.mc_server,team_name=team_name_assign,member_to_add=member)
            players_in_team=[]
        #delete first element which is the empty list
        print(self.total_players)
        # del self.total_players[0]
    def start_match(self):
        self.mc_server.sendline('/say Command to Initiate Match Received.')
        self.mc_server.sendline('/say Calculating teams and spawn locations...')
        self.mc_server.sendline('/say Assigning players to their teams...')
        self.pre_match_calc()
        self.make_teams()
        self.mc_server.sendline('/say Killing All Players in 10 seconds... Please Respawn to be Full Health')
        time.sleep(10)
        kill_all_players(mc_server=self.mc_server)
        self.mc_server.sendline('/say Teleporting teams to their respective start locations in 5 seconds...')
        time.sleep(5)
        set_world_border(mc_server=self.mc_server,worldborder_size=self.worldborder_start_size,time="")
        #
        #make all players creative before the jump
        for sublist in self.total_players:
            for indiv_player in sublist:
                change_player_gamemode(mc_server=self.mc_server,player_name=indiv_player,mode="creative")
        print("creative")
        #
        #teleport teams to staarting
        x=0
        for sublist in self.total_players:
            for indiv_player in sublist:
                teleport_player(mc_server=self.mc_server,player_name=indiv_player,x=self.initiate_match_teams_spawn_locations[int(x)][0],y=200,z=self.initiate_match_teams_spawn_locations[int(x)][1])
                print(indiv_player)
                print(self.initiate_match_teams_spawn_locations[int(x)][0],self.initiate_match_teams_spawn_locations[int(x)][0])
            x=x+1
        time.sleep(10)
        print("teleport")
        #
        #after players survive the fall turn them back to survival
        #make all players creative before the jump
        x=0
        for sublist in self.total_players:
            for indiv_player in sublist:
                change_player_gamemode(mc_server=self.mc_server,player_name=indiv_player,mode="survival")
                print(indiv_player)
        x=x+1
        set_world_border(mc_server=self.mc_server,worldborder_size=self.worldborder_end_size,time=self.worldborder_collapse_time)
        self.initiate_match_teams_indexes=[]
        self.initiate_match_teams_spawn_locations=[]
        self.total_players=[]



# test.stop_pserver()
# test=player()
# test.teams
# test.teams[1][0]="aaron"
# test.teams[2][0]="aaronddd"
# test.pre_match_calc()
# test.make_teams()
# test.total_players



# test=player()
# time.sleep(5)
# test.check_players()
# player.teams
# player.accounted

#aaro=capture_player_list(mc_server)


#mc_server=wexpect.spawn('java -Xms4G -Xmx4G -jar "server (6).jar" nogui java')
# mc_server=wexpect.spawn('java -Xms4G -Xmx4G -jar "server (6).jar" nogui java',cwd=os.path.abspath("D:\\gd\\minecraft_1.15.2"))
# mc_server.sendline('/time set midnight')
#printout the buffer holding the console output




# print(mc_server.read_nonblocking())

#players=capture_player_list(mc_server)

#list for players already accounted for



HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 50008              # Arbitrary non-privileged port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
test=player()
time.sleep(5)
while True:
    clientsocket, addr = s.accept()
    print("computer",{addr},"coonected.")
    msg=clientsocket.recv(1024)
    msg=json.loads(msg.decode("utf-8"))
    if msg[0]=="ch_team":
        #xtract list of player to be moved
        player_move=msg[2][:-1]
        player_move=player_move.split(" ")
        for player in player_move:
            test.move_player(player_to_move=player,new_team=int(msg[1]))
    elif msg[0]=="update_teams": 
        test.check_players()
    elif msg[0]=="worldborder_start":
    	if isinstance(msg[1],int):
        	test.worldborder_start_size=int(msg[1])
    elif msg[0]=="worldborder_end":
    	if isinstance(msg[1],int):
        	test.worldborder_end_size=int(msg[1])
    elif msg[0]=="worldborder_time_move":
    	if isinstance(msg[1],int):
        	test.worldborder_collapse_time=int(msg[1])
    elif msg[0]=="start_game":
        test.start_match()
    temp_teams=copy.deepcopy(test.teams)
    temp_teams.append([test.worldborder_start_size,test.worldborder_end_size,test.worldborder_collapse_time])
    to_send=temp_teams
    # to_send=test.teams
    clientsocket.sendall(bytes(json.dumps(to_send),encoding="utf-8"))
    
