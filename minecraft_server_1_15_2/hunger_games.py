
import socket
import os
import time
import pickle
import numpy as np
import copy
import wexpect
import json
import random
import subprocess
import time
from threading import Thread
import argparse
import time

#select whether this is a vanilla or modded server
parser=argparse.ArgumentParser()
parser.add_argument("mod_status",
    default="v",
    nargs='?',
    help="Please indicate whether the server is modded (m) or vanilla (v).")

args = parser.parse_args()

if args.mod_status=="m":
    print("MODDED DETECTED.")
    modded=True
elif args.mod_status=="v":
    modded=False
else:
    print("You did not select whether the server is vanilla or modded.")
    quit()

print("Starting up web interface...\n")
subprocess.Popen(['python',os.path.dirname(os.getcwd())+"\\hunger_games_server\\battle_royale_server.py"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

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
        if ('20 players online:' in player_list) and (not('lost connection: Disconnected' in player_list)) and (not('the game' in player_list)) and player_list.count("[Server thread/INFO]")==1 and (not("Can't keep up!" in player_list)) and (not("Mismatch in destroy" in player_list)) and (not("Fetching packet for" in player_list)) and (not('moved too quickly!' in player_list)) and (not('moved wrongly!' in player_list)) and (not("Can't keep up!" in player_list)):
            # print(player_list)
            start=player_list.find('20 players online:')+len('20 players online:')+1
            end=player_list.rfind('\r\n')
            players=player_list[start:end].replace(",","").split(" ")
            break
    return(players)

def remove_spaces(string_t):
    if string_t.endswith(' '):
        print(string_t)
        return(remove_spaces(string_t[0:-1]))
    else:
        return(string_t)

def capture_player_list_modded_server(mc_server):
    #print(player_list)
    #the start and end of the substring we will be taking
    while(True):
        #print(mc_server)
        #this first line basically just flushed the buffer becaause we want only the output of "/list". It will be overwritten
        a=test.mc_server.read_nonblocking()
        test.mc_server.sendline('/list')
        time.sleep(0.1)
        player_list=test.mc_server.read_nonblocking()
        # print(player_list)
        if ('players online:' in player_list) and (not('lost connection: Disconnected' in player_list)) and (not('the game' in player_list)) and player_list.count("[Server thread/INFO]")==2 and (not("Can't keep up!" in player_list)) and (not("Mismatch in destroy" in player_list)) and (not("Fetching packet for" in player_list)) and (not('moved too quickly!' in player_list)) and (not('moved wrongly!' in player_list)) and (not("Can't keep up!" in player_list)):
            try:
                # the modded server prints out two lines in response so take the second line which contaions the player names
                b=player_list.split('[minecraft/DedicatedServer]: ')[2]
            except:
                print("none")
                return([])
            # remove the arrow from the start of the second line 
            c=b.split('>')[0]
            #remove the next line spacing
            c=c.replace('\r\n','')
            player_list=remove_spaces(c)
            players=player_list.replace(",","").split(" ")
            break
    if players==[' ']:
        return([])
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
    if modded:
        active_players=capture_player_list_modded_server(mc_server)
    else:
        active_players=capture_player_list(mc_server)
    # print(active_players)
    #find any players that are new logins
    player_unaccounted=[]
    for i in active_players:
        player_unaccounted.append(not(i in accounted))
        #print(i)
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
    #print(len(player_logged))
    if not(len(player_logged)==0):
        print("Player change detected!")
        for player in player_logged:
            #need add a function to find where the person is if they moved a team already
            a,b=find_member_on_team(team_data,player)
            team_data=remove_from_team(team_data,a,name=player)
            #print(team_data)
            #print(player)
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

def give_player(mc_server,player,item,quantity):
    mc_server.sendline('/give '+player+' '+item+' '+quantity)

def command_server(mc_server,command):
    mc_server.sendline('/'+command)

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
        #lets make these a little closer in from the corner
        xhigh=xhigh-10
        xlow=xlow+10
        yhigh=yhigh-10
        ylow=ylow+10
        loc_1=[xhigh,ylow]
        loc_2=[xlow,yhigh]
        loc_3=[xlow,ylow]
        loc_4=[xhigh,yhigh]
        possible_spawns=[loc_1,loc_2,loc_3,loc_4]
        random.shuffle(possible_spawns)
        return(active_team_indexes,possible_spawns[0:len(active_team_indexes)])

# calculate_teams_and_spawns(test.teams,test.worldborder_center_location,test.worldborder_start_size,test.worldborder_end_size,3600)

def preload_chunks(mc_server,x1,z1,x2,z2):
    print("forceload add "+str(int(x1))+' '+str(int(z1))+' '+str(int(x2))+' '+str(int(z2)))
    command_server(mc_server=mc_server,command="forceload add "+str(int(x1))+' '+str(int(z1))+' '+str(int(x2))+' '+str(int(z2)))

def spawn_zombies_blazes_wither(mc_server,intervention_count):
    number_zombies=3+intervention_count
    number_blazes=intervention_count-1
    number_withers=intervention_count-3
    #always spawn a creeper each round
    #command_server(mc_server=mc_server,command='execute at @e[gamemode=survival] run summon minecraft:creeper')
    time.sleep(1)
    #spawn an increasing number of zombies
    if number_zombies>0:
        for i in range(0,number_zombies):
            command_server(mc_server=mc_server,command='execute at @e[gamemode=survival] run summon minecraft:zombie')
    #spawn an increasing number of blazes each round
    if number_blazes>0:
        for i in range(0,number_blazes):
            command_server(mc_server=mc_server,command='execute at @e[gamemode=survival] run summon minecraft:blaze')
    #spawn a wither on round 4
    if number_withers>0:
        mc_server.sendline('/say HOW THE FUCK ARE YOU STILL ALIVE?? TIME TO DIE :D :D :D')
        time.sleep(3)
        mc_server.sendline('/say now where did I put those wither skulls??')
        time.sleep(2)
        for i in range(0,number_withers):
            command_server(mc_server=mc_server,command='execute at @e[gamemode=survival] run summon minecraft:wither')
    return(intervention_count+1)

v_1_15_2=['minecraft:oak_log','minecraft:oak_boat','minecraft:arrow','minecraft:bookshelf','minecraft:iron_ingot']
m_1_12_2=['minecraft:oak_log','minecraft:boat','minecraft:arrow','minecraft:bookshelf','minecraft:iron_ingot']
item_quantity=['10','1','5','15','3']

class player:
    def __init__(self):
        self.teams=create_teams()
        self.mc_server=wexpect.spawn('java -Xms4G -Xmx4G -jar "server.jar" nogui java',cwd=os.getcwd())
        self.accounted=[]
        self.worldborder_center_location=[0,0]
        self.worldborder_start_size=1000
        self.worldborder_end_size=16
        self.worldborder_collapse_time=2400
        self.initiate_match_teams_indexes=[]
        self.initiate_match_teams_spawn_locations=[]
        self.total_players=[]
        self.check_players_time=0
        self.last_initiated=0
        #when is the border expected to finish closing?
        self.end_time=0
        #a counter to keep track of the stages or waves that are sent to players
        self.end_time_intervention=0
        #timer to time how long should be waited beteween waves
        self.end_time_time_between_waves=0
        #error rebound counter
        self.error_rebound=0
        if modded:
            self.item_pack=m_1_12_2
        else:
            self.item_pack=v_1_15_2
        self.item_pack_number=item_quantity
        #if vanilla chunks are forceloaded so teleports can go fast
        if modded:
            self.teambuffertime=0.1
        else:
            self.teambuffertime=5
    def check_players(self):
        if (time.time()-self.check_players_time)>2:
            try:
                self.teams,self.accounted=check_current_login(mc_server=self.mc_server,accounted=self.accounted,team_data=self.teams)
                self.check_players_time=time.time()
            except:
                print("check_players_error_rebound")
                test.teams=create_teams()
                test.accounted=[]
    def stop_pserver(self):
        stop_server(self.mc_server)
    def move_player(self,player_to_move,new_team):
        self.teams=move_player_to_team(team_data=self.teams,player_to_move=player_to_move,new_team=new_team)
    def pre_match_calc(self):
        self.initiate_match_teams_indexes,self.initiate_match_teams_spawn_locations=calculate_teams_and_spawns(team_data=self.teams,worldborder_center=self.worldborder_center_location,worldborder_start_size=self.worldborder_start_size,worldborder_end_size=self.worldborder_end_size,worldborder_collpase_time=self.worldborder_collapse_time)
    def make_teams(self):
        #for each team that will play create a team
        team_counter=0
        possible_team_colors=["blue","dark_red","aqua","dark_purple"]
        for i in self.initiate_match_teams_indexes:
            #make a clean list of all players. make empty to fill
            #create the team name
            team_name_assign=str("team_"+str(i))
            print(team_name_assign)
            create_team(mc_server=self.mc_server,team_name=team_name_assign)
            self.mc_server.sendline('/say Assigning team colors...')
            team_command=str('team modify '+team_name_assign+' color '+possible_team_colors[team_counter])
            print(team_command)
            command_server(mc_server=self.mc_server,command=team_command)
            #self.mc_server.sendline('/say Team friendlyfire DISABLED...')
            command_server(mc_server=self.mc_server,command='team modify '+team_name_assign+' friendlyFire false')
            team_counter=team_counter+1
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
        if time.time()-self.last_initiated>15:
            self.mc_server.sendline('/say Command to Initiate Match Received.')
            self.mc_server.sendline('/say Calculating teams and spawn locations...')
            self.mc_server.sendline('/say Assigning players to their teams...')
            self.mc_server.sendline('/say Preloading spawn chunks. This will take some time...')
            self.pre_match_calc()
            self.make_teams()
            #use this time to preload chunks in preparation of the teleport. If you don't do this the server gets overloaded with everyone teleporting
            preload_buffer=50
            for loc in self.initiate_match_teams_spawn_locations:
                preload_chunks(self.mc_server,x1=loc[0]-preload_buffer,z1=loc[1]+preload_buffer,x2=loc[0]+preload_buffer,z2=loc[1]-preload_buffer)
                time.sleep(5)
            self.mc_server.sendline('/say Killing All Players in 5 seconds... Please Respawn to be Full Health')
            time.sleep(5)
            #set player spawn points at the start locations
            # x=0
            # for sublist in self.total_players:
            #     for indiv_player in sublist:
            #         #teleport_player(mc_server=self.mc_server,player_name=indiv_player,x=self.initiate_match_teams_spawn_locations[int(x)][0],y=200,z=self.initiate_match_teams_spawn_locations[int(x)][1])
            #         command_server(mc_server=self.mc_server,command='spawnpoint '+indiv_player+' '+str(self.initiate_match_teams_spawn_locations[int(x)][0])+' '+'700'+' '+str(self.initiate_match_teams_spawn_locations[int(x)][0]))
            #     x=x+1
            #set the new borders, this can sometimes kill players
            command_server(mc_server=self.mc_server,command='worldborder center '+str(self.worldborder_center_location[0])+' '+str(self.worldborder_center_location[1]))
            set_world_border(mc_server=self.mc_server,worldborder_size=self.worldborder_start_size,time="")
            #set new spawn points
            # for sublist in self.total_players:
            #     for indiv_player in sublist:
                    
            #kill players instantly if the border shift didnt already kill them
            kill_all_players(mc_server=self.mc_server)
            self.mc_server.sendline('/say Teleporting teams to their respective start locations in 5 seconds...')
            #set minecraft time to day at match start
            command_server(mc_server=self.mc_server,command='time set noon')
            time.sleep(5)
            #set player gamemodes to survival in case they are creative and currently flying
            for sublist in self.total_players:
                for indiv_player in sublist:
                    change_player_gamemode(mc_server=self.mc_server,player_name=indiv_player,mode="survival")
            print("creative")
            time.sleep(2)
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
                    time.sleep(0.2)
                time.sleep(self.teambuffertime)
                x=x+1
            #give items
            for sublist in self.total_players:
                for indiv_player in sublist:
                    give_player(mc_server=self.mc_server,player=indiv_player,item=self.item_pack[0],quantity=self.item_pack_number[0])
                    give_player(mc_server=self.mc_server,player=indiv_player,item=self.item_pack[1],quantity=self.item_pack_number[1])
                    give_player(mc_server=self.mc_server,player=indiv_player,item=self.item_pack[2],quantity=self.item_pack_number[2])
                    give_player(mc_server=self.mc_server,player=indiv_player,item=self.item_pack[3],quantity=self.item_pack_number[3])
                    give_player(mc_server=self.mc_server,player=indiv_player,item=self.item_pack[4],quantity=self.item_pack_number[4])
                    #give_player(mc_server=self.mc_server,player=indiv_player,item='minecraft:obsidian',quantity='4')
                    command_server(mc_server=self.mc_server,command='xp set '+indiv_player+' 30 levels')
            time.sleep(6)
            print("teleport")
            # command_server(mc_server=self.mc_server,command="forceload remove all")
            # command_server(mc_server=self.mc_server,command="forceload remove all")
            #
            #after players survive the fall turn them back to survival
            #make all players creative before the jump
            x=0
            for sublist in self.total_players:
                for indiv_player in sublist:
                    change_player_gamemode(mc_server=self.mc_server,player_name=indiv_player,mode="survival")
                    print(indiv_player)
            x=x+1
            command_server(mc_server=self.mc_server,command="forceload remove all")
            time.sleep(10)
            self.mc_server.sendline('/say Worldborders will begin to shrink in 1 minutes...')
            time.sleep(50)
            set_world_border(mc_server=self.mc_server,worldborder_size=self.worldborder_end_size,time=self.worldborder_collapse_time)
            #delete all forceloads so that only chunks where players are in are needed.
            
            self.initiate_match_teams_indexes=[]
            self.initiate_match_teams_spawn_locations=[]
            self.total_players=[]
            self.last_initiated=time.time()
            self.worldborder_center_location=[self.worldborder_center_location[0]+5000,self.worldborder_center_location[1]+5000]
            self.end_time=time.time()+self.worldborder_collapse_time
    def check_intervention(self):
        #check if match in progress and intervention time is hit
        if self.end_time!=0 and time.time()-self.end_time>1:
            if self.end_time_intervention==0:
                print("end time hit")
                self.mc_server.sendline('/say Time is up! Spawning 5 zombies to your location in 10 minutes')
                self.end_time_time_between_waves=time.time()+600
                self.end_time_intervention=1
            elif self.end_time_intervention!=0 and time.time()-self.end_time_time_between_waves>1:
                print("wave sent.")
                self.end_time_intervention=spawn_zombies_blazes_wither(mc_server=self.mc_server,intervention_count=self.end_time_intervention)
                self.end_time_time_between_waves=time.time()+60
                self.mc_server.sendline('/say Next wave spawns in 60 seconds.')

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 50008              # Arbitrary non-privileged port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
print("starting minecraft server...\n")
test=player()
time.sleep(5)

def main_function(test=test):
    while True:
        # print(myvar)
        if myvar=="0":
            # print("good")
            try:
                test.check_intervention()
                clientsocket, addr = s.accept()
                #print("computer",{addr},"coonected.")
                msg=clientsocket.recv(1024)
                msg=json.loads(msg.decode("utf-8"))
                if msg[0]=="ch_team":
                    try:
                        #xtract list of player to be moved
                        player_move=msg[2][:-1]
                        player_move=player_move.split(" ")
                        for player in player_move:
                            test.move_player(player_to_move=player,new_team=int(msg[1]))
                    except:
                        print("Error in moving player.")
                elif msg[0]=="update_teams": 
                    test.check_players()
                elif msg[0]=="worldborder_start":
                    try:
                        test.worldborder_start_size=int(msg[1])
                    except:
                        print("worldborder start size is not a number.")
                elif msg[0]=="worldborder_end":
                    try:
                        test.worldborder_end_size=int(msg[1])
                    except:
                        print("worldborder end size is not a number.")
                elif msg[0]=="worldborder_time_move":
                    try:
                        test.worldborder_collapse_time=int(msg[1])
                    except:
                        print("worldborder collapse time is not a number.")
                elif msg[0]=="start_game":
                    try:
                        test.start_match()
                    except:
                        print("error starting match")
                # elif msg[0]=="close_everything":
                #     try:
                #         test.stop_pserver()
                #         quit()
                #     except:
                #         print("error closing.")
                temp_teams=copy.deepcopy(test.teams)
                temp_teams.append([test.worldborder_start_size,test.worldborder_end_size,test.worldborder_collapse_time])
                to_send=temp_teams
                # to_send=test.teams
                clientsocket.sendall(bytes(json.dumps(to_send),encoding="utf-8"))
                # print("good2")
            except:
                if test.error_rebound!=3:
                    test.teams=create_teams()
                    test.accounted=[]
                    test.error_rebound=test.error_rebound+1
                else:
                    test.stop_pserver()
        elif myvar=="stop":
            print("Exit code received.")
            test.stop_pserver()
        else:
            print("esleeeeeeeee")
            time.sleep(0.1)

print("Game monitoring...ACTIVE")
myvar="0"
t=Thread(target=main_function)
t.start()


