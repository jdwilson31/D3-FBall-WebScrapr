from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import csv
import re

NAME_DICT = {}

def parseHTML(link):
    url = link
    sourceCode = requests.get(url).text
    html = BeautifulSoup(sourceCode, "html.parser")
    
    return html

def get_game_links(html, base, links):
    schedule = html.find("div", class_="schedule-body-container")

    boxscores = schedule.find_all("div", class_="sidearm-schedule-game-links show-on-medium-only")

    for game in boxscores:
        link = (game.find("li"))
        links.append(base + link.find("a").get("href"))


def get_game_info(html):
    names = html.find("table", class_="sidearm-table").find("tbody").find_all("span", class_="hide-on-medium")
    team_names = []
    for name in names:
        team_names.append(name.text)

    info = html.find("dl", class_="text-center inline").find_all("dd")
    date = info[0].text
    year = date[-4:]

    week = html.find("h4", class_ ="main-heading text-center text-uppercase").find("span").text
    week_num = int(week[1]) + int(week[3])

    game_id = str(team_names[0][:3]).upper() + "_" + str(team_names[1][:3]).upper() + str(year) 
    if game_id == "AMH_COL2022": week_num = 5
    return str(week_num), game_id


def clean_pbp(raw_plays):
    plays = []
    clean_plays = []
    for play in (raw_plays):
        if len(play) > 0:
            plays.append(play.text)

    for play in plays:
        index = 0
        while ord(play[index]) in [32, 10, 13]:
            index += 1

        clean_plays.append(play[index:])
        if "\n" in play[index:]:
            clean_plays.append("----------------------------------")

    count = 0
    for play in clean_plays:
        index = len(play) - 1
        while ord(play[index]) in [32, 10, 13]:
            index -= 1

        clean_plays[count] = play[:index + 1]
        count += 1
    
    return clean_plays
    

def format_pbp(clean_plays, game_id, official_pbp, play_id):
    index = 0

    while index < len(clean_plays):
        off_play = game_id + ": " + str(play_id) + "\n"
        while (index < len(clean_plays)) and (clean_plays[index] != "----------------------------------"):
            off_play += clean_plays[index] + "\n"
            index += 1
        off_play = re.sub("EPHS", "WIL", off_play)
        official_pbp.append(off_play[:-1])
        play_id += 1
        index += 1

    return play_id


def parse_line(play_dict, play, info_to_pass):
    time = ""
    if re.findall("\d{2}:\d{2}", play) != []:
        time = re.findall("\d{2}:\d{2}", play)[-1]
    if time != "":
        info_to_pass["time"] = time
    play_info = play.split("\n")
    play_dict["play_id"] = play[13:play.index('\n')]
    play_dict["game_id"] = play[:11]
    play_dict["home_team"] = play[4:7]
    play_dict["away_team"] = play[:3]
    play_dict["week"] = info_to_pass[play[:11]]
    pos_def_team(play_info, info_to_pass)
    if info_to_pass["posteam"] == "TRI" and play_dict["game_id"] == "BOW_BAN2022": info_to_pass["posteam"] = "BAN"
    play_dict["posteam"] = info_to_pass["posteam"]
    play_dict["posteam_type"] = info_to_pass["posteam_type"]
    play_dict["defteam"] = info_to_pass["defteam"]
    play_dict["game_half"] = info_to_pass["game_half"]
    play_dict["drive"] = info_to_pass["drive"]
    play_dict["drive_plays"] = info_to_pass["drive_plays"] + 1
    play_dict["quarter"] = info_to_pass["quarter"]
    play_dict["home_team_score"] = info_to_pass["home_team_score"]
    play_dict["away_team_score"] = info_to_pass["away_team_score"]
    play_dict["posteam_score"] = info_to_pass["posteam_score"]
    play_dict["defteam_score"] = info_to_pass["defteam_score"]
    play_dict["score_differential"] = play_dict["posteam_score"] - play_dict["defteam_score"]

    if play_info[1][0] not in ["1", "2", "3", "4"]:
        temp_info = [play_info[0]]
        if "drive start" not in play_info[-1] and (":" not in play_info[-1] or "TOUCHDOWN" in play_info[-1]):
            if play_info[len(play_info) - 2][0] in ["1", "2", "3", "4"]:
                temp_info.append(play_info[len(play_info) - 2])
            else:
                temp_info.append("1st and 10 at " + play_dict["posteam"] + "40")
            temp_info.append(play_info[len(play_info) - 1])
            play_info = temp_info

        if play_dict["game_id"] == "BAT_WES2022":
            temp_info.append("0 and 99 and " + play_dict["posteam"] + "0")
            temp_info.append(play_info[len(play_info) - 1])
            play_info = temp_info

    if play_info[1][0] in ["1", "2", "3", "4", "0"] and len(play_info) > 2:
        general_info(play_dict, play_info)
        touchdown(play_dict, play_info[2])
        penalties(play_dict, play_info[2])
        turnovers(play_dict, play_info[2])
        tackling_info(play_dict, play_info[2])
        first_down(play_dict, play_info[2])
        names_and_more(play_dict, play_info[2], info_to_pass)

    else:
        play_dict["side_of_field"] = play_dict["yardline100"] = play_dict["down"] = play_dict["yds_to_go"] = ""
        play_dict["goal_to_go"] = play_dict["sp"] = play_dict["yardline"] = play_dict["play_type"] = play_dict["desc"] = ""
        play_dict["yards_gained"] = play_dict["first_down"] = play_dict["first_down_pass"] = play_dict["first_down_rush"] = play_dict["first_down_penalty"] = ""
        play_dict["third_down_failed"] = play_dict["third_down_converted"] = ""
        play_dict["fourth_down_attempted"] = play_dict["fourth_down_failed"] = play_dict["fourth_down_converted"] = ""
        play_dict["rush_attempt"] = play_dict["pass_attempt"] = ""
        play_dict["rusher"] = play_dict["passer"] = play_dict["receiver"] = play_dict["targeted_receiver"] = ""
        play_dict["rushing_yards"] = play_dict["passing_yards"] = play_dict["receiving_yards"] = play_dict["yards_net"] = play_dict["drive_first_downs"] = ""
        play_dict["touchdown"] = play_dict["pass_touchdown"] = play_dict["rush_touchdown"] = play_dict["return_touchdown"] = ""
        play_dict["touchdown_team"] = play_dict["touchdown_player"] = ""
        play_dict["complete_pass"] = play_dict["incomplete_pass"] = ""
        play_dict["solo_tackle"] = play_dict["assisted_tackle"] = ""
        play_dict["tackled_for_loss"] = play_dict["tackled_for_loss_yards"] = play_dict["sack"] = play_dict["sack_yards"] = ""
        play_dict["half_tfl"] = play_dict["full_tfl"] = play_dict["full_sack"] = play_dict["half_sack"] = ""
        play_dict["penalty"] = play_dict["first_down_penalty"] = ""
        play_dict["penalty_team"] = play_dict["penalty_type"] = play_dict["penalty_accepted"] = play_dict["penalty_yards"] = play_dict["penalty_player"] = ""
        play_dict["fumble"] = play_dict["interception"] = play_dict["interception_player"] = play_dict["pass_deflection_player"] = ""
        play_dict["fumble_lost"] = play_dict["fumble_forced"] = ""
        play_dict["fumble_team"] = play_dict["fumble_recovery_team"] = play_dict["forced_fumble_player"] = play_dict["fumble_recovery_player"] = ""
        play_dict["return_yards"] = play_dict["return_team"] = play_dict["touchback"] = play_dict["return_player"] = ""
        play_dict["assisted_tackle_player_1"] = play_dict["assisted_tackle_player_2"] = play_dict["solo_tackle_player"] = ""
        play_dict["tackle_for_loss_player_1"] = play_dict["tackle_for_loss_player_2"] = ""
        play_dict["sack_player_1"] = play_dict["sack_player_2"] = play_dict["solo_tackle_player_2"] = ""
        play_dict["timeout"] = play_dict["timeout_team"] = ""
        play_dict["safety"] = ""

    play_dict["posteam_score_post"] = play_dict["defteam_score_post"] = play_dict["score_differential_post"] = ""
    play_dict["home_team_score_post"] = play_dict["away_team_score_post"] = ""
    
    play_dict["recent_time"] = info_to_pass["time"]
    if int(info_to_pass["time"][:2]) >= 10:
        play_dict["quarter_time"] = "early"
    elif int(info_to_pass["time"][:2]) >= 5:
        play_dict["quarter_time"] = "mid"
    else: play_dict["quarter_time"] = "late"
    if play_dict["quarter"] in ["2", "4"] and play_dict["quarter_time"] == "late": play_dict["late_half"] = 1
    else: play_dict["late_half"] = 0 
    play_dict["change_of_possession"] = 0

    timeout_info(play_dict, play_dict["desc"], info_to_pass)
    special_teams_info(play_dict)
    change_score(play_dict, info_to_pass)
    if play_dict["play_type"] in ["kickoff", "punt"] or play_dict["fg_result"] in ["blocked", "missed"] \
       or play_dict["fumble"] == 1 or play_dict["interception"] == 1 or play_dict["fourth_down_failed"] == 1:
        if play_dict["penalty"] == 1 and play_dict["play_type"] != "kickoff":
            if play_dict["penalty_team"] != play_dict["posteam"] and play_dict["first_down"] == 1:
                info_to_pass["change_of_possession"] = 0
            else:
                play_dict["change_of_possession"] = 1
                info_to_pass["change_of_possession"] = 1
        else:
            if (play_dict["fumble"] == 1 and play_dict["fumble_lost"] == 1) or play_dict["fumble"] == 0:
                play_dict["change_of_possession"] = 1
                info_to_pass["change_of_possession"] = 1
            

    if play_dict["play_type"] != "No Play" and play_dict["play_type"] != "": info_to_pass["drive_plays"] += 1

    
def pos_def_team(play_info, info_to_pass):
    if info_to_pass["posteam"] not in play_info[0][:11] or info_to_pass["defteam"] not in play_info[0][:11]:
        info_to_pass["posteam"] = ""
        info_to_pass["defteam"] = ""
        info_to_pass["posteam_type"] = ""
        info_to_pass["drive"] = 0
        info_to_pass["game_half"] = "Half1"
        info_to_pass["quarter"] = 1
        info_to_pass["posteam_timeouts_remaining"] = info_to_pass["defteam_timeouts_remaining"] = 3
        info_to_pass["home_team_timeouts_remaining"] = info_to_pass["away_team_timeouts_remaining"] = 3
        info_to_pass["yards_net"] = info_to_pass["drive_first_downs"] = info_to_pass["drive_plays"] = 0
        info_to_pass["home_team_score"] = info_to_pass["away_team_score"] = info_to_pass["posteam_score"] = info_to_pass["defteam_score"] = 0
        if "ball" in play_info[1] or "defe" in play_info[1]: 
            if re.findall("[A-Z]+ *(?:ball|will def)", play_info[1]) != []:
                info_to_pass["posteam"] = re.findall("[A-Z]+ *(?:ball|will def)", play_info[1])[0][:3].upper()
            else: 
                info_to_pass["posteam"] = re.findall("[A-Z][a-z ]+,* *defers", play_info[1])[0][:3].upper()
            if info_to_pass == play_info[0][:3]: info_to_pass["defteam"] = play_info[0][4:7]
            else: info_to_pass["defteam"] = play_info[0][:3]
    elif "drive" in play_info[len(play_info) - 1] or "TOTAL" in play_info[1] or info_to_pass["change_of_possession"] == 1:
        info_to_pass["drive"] = info_to_pass["drive"] + 1
        if "drive" in play_info[len(play_info) - 1]:
            info_to_pass["posteam"] = play_info[len(play_info) - 1][:3].upper()
        else: info_to_pass["posteam"] = info_to_pass["defteam"]
        info_to_pass["yards_net"] = info_to_pass["drive_first_downs"] = info_to_pass["drive_plays"] = 0
        if info_to_pass["posteam"] == play_info[0][:3]:
            info_to_pass["defteam"] = play_info[0][4:7]
            info_to_pass["posteam_type"] = "Away"
            info_to_pass["defteam_timeouts_remaining"] = info_to_pass["home_team_timeouts_remaining"]
            info_to_pass["posteam_timeouts_remaining"] = info_to_pass["away_team_timeouts_remaining"]
            info_to_pass["defteam_score"] = info_to_pass["home_team_score"]
            info_to_pass["posteam_score"] = info_to_pass["away_team_score"]
        else:
            info_to_pass["defteam"] = play_info[0][:3]
            info_to_pass["posteam_type"] = "Home"
            info_to_pass["posteam_timeouts_remaining"] = info_to_pass["home_team_timeouts_remaining"]
            info_to_pass["defteam_timeouts_remaining"] = info_to_pass["away_team_timeouts_remaining"]
            info_to_pass["defteam_score"] = info_to_pass["away_team_score"]
            info_to_pass["posteam_score"] = info_to_pass["home_team_score"]
        if info_to_pass["change_of_possession"] == 1: info_to_pass["change_of_possession"] = 0
        
    elif ("3rd quarter" in play_info[1]) or (len(play_info) >= 4 and "3rd quarter" in play_info[3]):
        info_to_pass["game_half"] = "Half2"
        info_to_pass["posteam_timeouts_remaining"] = info_to_pass["defteam_timeouts_remaining"] = 3
        info_to_pass["home_team_timeouts_remaining"] = info_to_pass["away_team_timeouts_remaining"]= 3
        if info_to_pass["quarter"] != 3:
            info_to_pass["quarter"] += 1
    elif "quarter" in play_info[1] or (len(play_info) > 2 and "quarter" in play_info[2]):
        if "1st quarter" not in play_info[1]:
            info_to_pass["quarter"] += 1
    
    

def general_info(play_dict, play_info):
    play_dict["down"] = play_info[1][0]
    play_dict["goal_to_go"] = 0
    down_info = play_info[1].split(" ")
    yds_to_go = down_info[2]
    if yds_to_go == "GOAL":
        yds_to_go = down_info[len(down_info) - 1][-2:]
        play_dict["goal_to_go"] = 1
    yds_to_go = int(re.findall("\d+", yds_to_go)[0])
    play_dict["side_of_field"] = down_info[len(down_info) - 1][:3].upper()
    if len(play_dict["side_of_field"]) < 3: play_dict["side_of_field"] = down_info[len(down_info) - 2][:3].upper()
    play_dict["yardline100"] = int(re.findall(r'\d+', down_info[len(down_info) - 1][-2:])[0])
    play_dict["yardline"] = play_dict["side_of_field"] + re.findall(r'\d+', down_info[len(down_info) - 1][-2:])[0]
    if play_dict["posteam"] == play_dict["side_of_field"]:
        play_dict["yardline100"] = 100 - play_dict["yardline100"]
    play_dict["yds_to_go"] = yds_to_go
    play_dict["desc"] = play_info[2]
    play_dict["play_type"] = play_type(play_info[2], play_info[1])
    play_dict["sp"] = scoring(play_info[2], play_dict)
    play_dict["yards_gained"] = yards_gained(play_info[2], play_dict)
    if "safety" in play_info[2]: play_dict["safety"] = 1
    else: play_dict["safety"] = 0
    if "touchback" in play_info[2]: play_dict["touchback"] = 1 
    else: play_dict["touchback"] = 0


def play_type(play_desc, situation):
    ret_type = ""
    if " rush " in play_desc:
        if "TEAM rush for loss" in play_desc and "(" not in play_desc:
            ret_type = "qb_kneel"
        else:
            ret_type = "rush"
    elif " pass " in play_desc or "sacked" in play_desc:
        ret_type = "pass"
    elif " punt " in play_desc:
        ret_type = "punt"
    elif "kickoff" in play_desc and "end-zone" not in play_desc:
        ret_type = "kickoff"
    elif "kick " in play_desc and ("1st" in situation or re.findall("\d+", play_desc) == []):
        ret_type = "xp"
    elif "kick " in play_desc or "field goal" in play_desc:
        ret_type = "fg"
    elif "Kneel" in play_desc or "TEAM rush for loss" in play_desc:
        ret_type = "qb_kneel"
    else:
        ret_type = "No Play"

    if "PENALTY" in play_desc and ("declined" in play_desc or "NO PLAY" not in play_desc):
        return ret_type
    elif "PENALTY" in play_desc:
        return "No Play"
    else:
        return ret_type
    

def scoring(desc, play_dict):
    ret_type = 0
    if ("TOUCHDOWN" in desc):
        ret_type = 1
    elif play_dict["play_type"] == "xp":
        if "good" in desc:
            ret_type = 1
    elif play_dict["play_type"] == "fg":
        if "NO GOOD" not in desc and "failed" not in desc and "BLOCKED" not in desc and "MISSED" not in desc:
            ret_type = 1
    elif "safety" in desc:
        ret_type = 1
    elif play_dict["down"] == "1":
        if "good" in desc:
            ret_type = 1

    if "PENALTY" in desc and ("declined" in desc or "NO PLAY" not in desc):
        return ret_type
    elif "PENALTY" in desc:
        return 0
    else:
        return ret_type
    

def yards_gained(desc, play_dict):
    play = desc.split(" ")
    yards = 0
    loss = 1
    if "loss" in desc: loss = -1
    if "for" not in play:
        if "incomplete" in play:
            yards = 0
    else:
        if play[play.index("for") + 1] == "no":
            yards = 0
        else:
            yards = int(re.findall(r'\d+', desc)[0])

    if play_dict["play_type"] == "pass":
        if "incomplete" in desc or "intercepted" in desc:
            play_dict["incomplete_pass"] = 1
            play_dict["complete_pass"] = 0
        elif "complete" in desc or "attempt" in desc:
            play_dict["incomplete_pass"] = 0
            play_dict["complete_pass"] = 1


    if "PENALTY" in desc and ("declined" in desc or "NO PLAY" not in desc):
        return yards * loss
    elif "PENALTY" in desc:
        return 0
    else:
        return yards * loss
            

def touchdown(play_dict, desc):
    play_dict["touchdown"] = play_dict["pass_touchdown"] = play_dict["rush_touchdown"] = play_dict["return_touchdown"] = 0
    play_dict["touchdown_team"] = ""
    if play_dict["sp"] == 1 and "TOUCHDOWN" in desc:
        play_dict["touchdown"] = 1
        if re.findall("[A-Z]+ *0+", desc)[0][:3] == play_dict["defteam"]:
            play_dict["touchdown_team"] = play_dict["posteam"] 
        else: play_dict["touchdown_team"] = play_dict["defteam"]
        if "return" in desc:
            play_dict["return_touchdown"] = 1
        elif "pass" in desc:
            play_dict["pass_touchdown"] = 1
        elif "rush" in desc:
            play_dict["rush_touchdown"] = 1


def penalties(play_dict, desc):
    auto_first = ["unsportmanlike conduct", "unsportsmanlike conduct", "roughing the passer", "personal foul", "pass interference", "holding", "face mask"]
    play_dict["penalty"] = play_dict["first_down_penalty"] = 0
    play_dict["penalty_team"] = play_dict["penalty_type"] = ""
    if "PENALTY" in desc:
        penalty = re.findall("PENALTY.*", desc)[0][8:]
        play_dict["penalty"] = 1
        play_dict["penalty_yards"] = 0
        play_dict["penalty_team"] = re.findall("[A-Z]{3}|Ban",penalty)[0].upper()
        if "(" in penalty: play_dict["penalty_player"] = truncate_name(re.findall("[(][^)]*[)]", penalty)[0][1:-1], play_dict["penalty_team"])
        if "declined" in penalty or "off-setting" in penalty:
            play_dict["penalty_accepted"] = 0
            play_dict["penalty_type"] = re.findall(" [a-zA-Z ]+ (?:decl|off-)", penalty)[0][1:-4].lower()
        else:
            play_dict["penalty_accepted"] = 1
            play_dict["penalty_type"] = re.findall(" [a-zA-Z ]+ (?:\d|[(])", penalty)[0][1:-2].lower()
            if len(re.findall(r"\d+", penalty)) > 0: 
                yards = int(re.findall(r"\d+", penalty)[0])
                if play_dict["penalty_team"] == play_dict["posteam"]: yards *= -1
                play_dict["penalty_yards"] = yards
            if play_dict["penalty_yards"] > 0:
                if (play_dict["penalty_yards"] >= play_dict["yds_to_go"] or \
                    ("PENALTY" in desc and "1ST DOWN" in desc) or play_dict["penalty_type"] in auto_first):
                    if re.findall("[A-Z]+ ball", desc) != []:
                        if re.findall("[A-Z]+ ball", desc)[0][:3] == play_dict["posteam"]:
                            play_dict["first_down_penalty"] = 1
                    elif "punt" in desc: 
                        yards = re.findall("[A-Z]+\d+", desc)
                        if re.findall("[A-Z]+", yards[1]) == re.findall("[A-Z]+", yards[1]) and \
                        abs(int(re.findall("\d+", yards[1])[0]) - int(re.findall("\d+", yards[1])[0])) > 15:
                            play_dict["penalty_first_down"] = 1
                    else: play_dict["first_down_penalty"] = 1
        if play_dict["penalty_type"][0] == " ": play_dict["penalty_type"] = play_dict["penalty_type"][1:]
        if play_dict["penalty_type"][-1] == " ": play_dict["penalty_type"] = play_dict["penalty_type"][:-1]

        if play_dict["penalty_yards"] < 0 and play_dict["yards_gained"] > 0:
            play_dict["yards_gained"] = 0
 

def turnovers(play_dict, desc):
    play_dict["fumble"] = play_dict["interception"] = 0
    if "PENALTY" not in desc or ("PENALTY" in desc and ("declined" in desc or play_dict["play_type"] != "No Play")):
        if "fumble" in desc:
            play_dict["fumble"] = 1
            play_dict["fumble_lost"] = play_dict["fumble_forced"] = 0
            play_dict["fumble_team"] = play_dict["posteam"]
            if "recovered" in desc:
                play_dict["fumble_recovery_team"] = re.findall("recovered by [A-Z]{3}",desc)[0][-3:]
                recovery_player =  re.findall("recovered by [A-Z]+ *[A-Z][a-zA-Z-'.]*[ ,]*[A-Z][a-zA-Z-']*",desc)[0][13:]
                play_dict["fumble_recovery_player"] = truncate_name(recovery_player[recovery_player.index(" ") + 1:], play_dict["fumble_recovery_team"])
            else: play_dict["fumble_recovery_team"] = play_dict["fumble_team"]
            if "forced" in desc:
                play_dict["fumble_forced"] = 1
                forced_player = re.findall("forced by [A-Z][a-zA-Z-'.]*[ ,]*[a-zA-Z-']*",desc)[0][10:]
                if "TEAM" in forced_player: forced_player == "TEAM"
                play_dict["forced_fumble_player"] = truncate_name(forced_player, play_dict["defteam"])
                if forced_player != "TEAM": play_dict["solo_tackle"] = 1
                if "solo_tackle_player" in play_dict:
                    play_dict["solo_tackle_player_2"] = play_dict["solo_tackle_player"]
                play_dict["solo_tackle_player"] = play_dict["forced_fumble_player"]
            if play_dict["fumble_team"] != play_dict["fumble_recovery_team"]:
                play_dict["fumble_lost"] = 1
            if "return" in desc: 
                play_dict["return_yards"] = re.findall(r"\d+", (re.findall("return.*\d+", desc)[0]))[0] 
                play_dict["return_team"] = play_dict["fumble_recovery_team"]
            else: play_dict["return_yards"] = 0
            if "loss" in desc: play_dict["return_yards"] *= -1
        if "muffed" in desc:
            play_dict["fumble"] = 1
            play_dict["fumble_lost"] = play_dict["fumble_forced"] = 0
            play_dict["fumble_team"] = play_dict["defteam"]
            if "recovered" in desc:
                play_dict["fumble_recovery_team"] = re.findall("recovered by [A-Z]{3}",desc)[0][-3:]
                recovery_player =  re.findall("recovered by [A-Z]+ [A-Z][a-zA-Z-'.]*[ ,]*[A-Z][a-zA-Z-']*|recovered by [A-Z]+ [A-Z][a-zA-Z-']*",desc)[0][13:]
                play_dict["fumble_recovery_player"] = truncate_name(recovery_player[recovery_player.index(" ") + 1:], play_dict["fumble_recovery_team"])
            else: play_dict["fumble_recovery_team"] = play_dict["fumble_team"]
            if play_dict["fumble_team"] != play_dict["fumble_recovery_team"]:
                play_dict["fumble_lost"] = 1
            if "return" in desc: 
                play_dict["return_yards"] = re.findall(r"\d+", (re.findall("return \d+", desc)[0]))[0] 
                play_dict["return_team"] = play_dict["fumble_recovery_team"]
            else: play_dict["return_yards"] = 0

        if "intercepted" in desc:
            play_dict["interception"] = 1
            play_dict["return_team"] = play_dict["defteam"]
            interceper = re.findall("intercepted by [A-Z][a-zA-Z-'.]*[ ,]*[a-zA-Z-']*",desc)[0][14:]
            play_dict["interception_player"] = truncate_name(interceper, play_dict["defteam"])
            if "return" in desc: play_dict["return_yards"] = re.findall(r"\d+", (re.findall("return.*\d+", desc)[0]))[0] 
            else: play_dict["return_yards"] = 0
            if "loss" in desc: play_dict["return_yards"] *= -1


def first_down(play_dict, desc):
    play_dict["first_down"] = play_dict["first_down_pass"] = play_dict["first_down_rush"] = 0
    if play_dict["first_down_penalty"] == 1:
        play_dict["first_down"] = 1
    elif play_dict["yards_gained"] >= play_dict["yds_to_go"] or "1ST DOWN" in desc:
        play_dict["first_down"] = 1
        if play_dict["play_type"] == "rush":
            play_dict["first_down_rush"] = 1
        elif play_dict["play_type"] == "pass":
            play_dict["first_down_pass"] = 1

    play_dict["third_down_failed"] = play_dict["third_down_converted"] = ""
    play_dict["fourth_down_attempted"] = ""
    play_dict["fourth_down_failed"] = play_dict["fourth_down_converted"] = ""
    if play_dict["down"] == "3":
        if play_dict["first_down"] == 1:
            play_dict["third_down_converted"] = 1
            play_dict["third_down_failed"] = 0
        elif play_dict["play_type"] in ["rush", "pass"]:
            play_dict["third_down_failed"] = 1
            play_dict["third_down_converted"] = 0

    elif play_dict["down"] == "4":
        play_dict["fourth_down_attempted"] = 0
        if play_dict["play_type"] in ["rush", "pass"]:
            play_dict["fourth_down_attempted"] = 1
            if play_dict["first_down"] == 1:
                play_dict["fourth_down_converted"] = 1
                play_dict["fourth_down_failed"] = 0
            else:
                play_dict["fourth_down_converted"] = 0
                play_dict["fourth_down_failed"] = 1


def timeout_info(play_dict, desc, info_to_pass):
    play_dict["timeout"] = 0
    play_dict["timeout_team"] = ""
    if "Timeout" in desc:
        play_dict["timeout"] = 1
        play_dict["timeout_team"] = desc.split(" ")[1][:3].upper()
        if play_dict["home_team"] == desc.split(" ")[1][:3].upper():            
            info_to_pass["home_team_timeouts_remaining"] -= 1 
            if play_dict["posteam_type"] == "Home":
                info_to_pass["posteam_timeouts_remaining"] -= 1
            elif play_dict["posteam_type"] == "Away":
                info_to_pass["defteam_timeouts_remaining"] -= 1
        elif play_dict["away_team"] == desc.split(" ")[1][:3].upper():
            info_to_pass["away_team_timeouts_remaining"] -= 1
            if play_dict["posteam_type"] == "Home":
                info_to_pass["defteam_timeouts_remaining"] -= 1
            elif play_dict["posteam_type"] == "Away":
                info_to_pass["posteam_timeouts_remaining"] -= 1

    play_dict["home_team_timeouts_remaining"] =  info_to_pass["home_team_timeouts_remaining"]
    play_dict["away_team_timeouts_remaining"] = info_to_pass["away_team_timeouts_remaining"]
    play_dict["posteam_timeouts_remaining"] = info_to_pass["posteam_timeouts_remaining"] 
    play_dict["defteam_timeouts_remaining"] = info_to_pass["defteam_timeouts_remaining"]


def tackling_info(play_dict, desc):
    tacklers = ""
    play_dict["solo_tackle"] = play_dict["assisted_tackle"] = 0
    if play_dict["play_type"] in ["punt", "kickoff", "fg", "xp"] or play_dict["fumble"] == 1 or play_dict["interception"] == 1:
        tackle_team = play_dict["posteam"]
    else: tackle_team = play_dict["defteam"]
    if len(re.findall("(?:\d\d*|ne|ds) [(][^)]*[)]", desc)) >= 1:
        tacklers = re.findall("(?:\d\d*|ne|ds) [(][^)]*[)]", desc)[0]
        tacklers = tacklers[tacklers.index("(") + 1:-1]
    elif re.findall("[A-Z]{3}\d\d*,* 1ST DOWN [A-Z]+ [(].*[)]", desc) != []:
        tacklers = re.findall("[A-Z]{3}\d\d*,* 1ST DOWN [A-Z]+ [(].*[)]", desc)[0]
        tacklers = tacklers[tacklers.index("(") + 1:-1]
    if "blocked" not in tacklers and "(" not in tacklers and play_dict["play_type"] != "No Play":
        if ";" not in tacklers and ", " not in tacklers and tacklers != "":
            play_dict["solo_tackle"] = 1
            play_dict["solo_tackle_player"] = truncate_name(tacklers, tackle_team)
        elif tacklers != "":
            play_dict["assisted_tackle"] = 1
            people = re.split("; *|, ", tacklers)
            play_dict["assisted_tackle_player_1"] = truncate_name(people[0], tackle_team)
            play_dict["assisted_tackle_player_2"] = truncate_name(people[1], tackle_team)

    play_dict["tackled_for_loss"] = play_dict["tackled_for_loss_yards"] = play_dict["sack"] = play_dict["sack_yards"] = 0
    if play_dict["play_type"] not in ["No Play", "qb_kneel"] and "blocked" not in desc:
        if play_dict["yards_gained"] < 0 or "sacked" in desc:
            play_dict["half_tfl"] = play_dict["full_tfl"] = 0
            play_dict["tackled_for_loss"] = 1
            play_dict["tackled_for_loss_yards"] = -1 * play_dict["yards_gained"]
            if play_dict["solo_tackle"] == 1:
                play_dict["full_tfl"] = 1
                play_dict["tackle_for_loss_player_1"] = play_dict["solo_tackle_player"]
            elif play_dict["assisted_tackle"] == 1:
                play_dict["half_tfl"] = 1
                play_dict["tackle_for_loss_player_1"] = play_dict["assisted_tackle_player_1"]
                play_dict["tackle_for_loss_player_2"] = play_dict["assisted_tackle_player_2"]
            if "sacked" in desc:
                play_dict["half_sack"] = play_dict["full_sack"] = 0
                play_dict["sack"] = 1
                play_dict["sack_yards"] = play_dict["yards_gained"] * -1
                if play_dict["solo_tackle"] == 1:
                    play_dict["full_sack"] = 1
                    play_dict["sack_player_1"] = play_dict["solo_tackle_player"]
                elif play_dict["assisted_tackle"] == 1:
                    play_dict["half_tfl"] = 1
                    play_dict["sack_player_1"] = play_dict["assisted_tackle_player_1"]
                    play_dict["sack_player_2"] = play_dict["assisted_tackle_player_2"]
    

def names_and_more(play_dict, desc, info):
    play_dict["rush_attempt"] = play_dict["pass_attempt"] = 0
    play_dict["rusher"] = play_dict["passer"] = play_dict["receiver"] = play_dict["targeted_receiver"] = ""
    if play_dict["play_type"] == "pass":
        pass_player = re.findall("[A-Z][a-zA-Z-'.]*[ ,]*[a-zA-Z-']* pass",desc)
        if pass_player == []:
            pass_player = re.findall("[A-Z][a-zA-Z-'.]*[ ,]*[a-zA-Z-']* sacked",desc)[0][:-7]
        else: pass_player = pass_player[0][:-5]
        play_dict["passer"] = truncate_name(pass_player, play_dict["posteam"])
        if play_dict["sack"] == 0:
            play_dict["pass_attempt"] = 1
            if play_dict["incomplete_pass"] == 1:
                if "incomplete to" in desc:
                    targeted_player = re.findall("incomplete to [A-Z][a-zA-Z-'.]*[ ,]*[a-zA-Z-']*",desc)[0][14:]
                    play_dict["targeted_receiver"] = truncate_name(targeted_player, play_dict["posteam"])
                if "(" in desc[1:] and play_dict["interception"] == 0 and play_dict["penalty"] == 0:
                    pass_deflection = re.findall("\([A-Z][a-zA-Z-'.]*[ ,][A-Z][a-zA-Z-']*", desc)[0][1:]
                    play_dict["pass_deflection_player"] = truncate_name(pass_deflection, play_dict["defteam"])
                elif "broken up" in desc:
                    pass_deflection = re.findall("up by [A-Z][a-zA-Z-'.]*[ ,][A-Z][a-zA-Z-']*", desc)[0][6:]
                    play_dict["pass_deflection_player"] = truncate_name(pass_deflection, play_dict["defteam"])
            elif "failed" not in desc and "Successful" not in desc:
                wr_player = re.findall("to [A-Z][a-zA-Z-'.]*[ ,]*[a-zA-Z-']* (?:for|goo)",desc)[0][3:-4]
                play_dict["receiver"] = play_dict["targeted_receiver"] = truncate_name(wr_player, play_dict["posteam"])
                play_dict["passing_yards"] = play_dict["receiving_yards"] = play_dict["yards_gained"]
        
        if play_dict["pass_touchdown"] == 1:
            play_dict["touchdown_player"] = play_dict["receiver"] 

    elif play_dict["play_type"] == "rush":
        rush_player = re.findall("[A-Z][a-zA-Z-'.]*[ ,]*[a-zA-Z-']* rush",desc)[0][:-5]
        play_dict["rusher"] = truncate_name(rush_player, play_dict["posteam"])
        play_dict["rush_attempt"] = 1
        play_dict["rushing_yards"] = play_dict["yards_gained"]
        if play_dict["rush_touchdown"] == 1:
            play_dict["touchdown_player"] = play_dict["rusher"]
    
    info["yards_net"] += play_dict["yards_gained"]
    play_dict["yards_net"] = info["yards_net"]
    if play_dict["first_down"] == 1: info["drive_first_downs"] += 1
    play_dict["drive_first_downs"] = info["drive_first_downs"]

    
def special_teams_info(play_dict):
    play_dict["xp_attempt"] = play_dict["fg_attempt"] = play_dict["two_point_attempt"] = play_dict["punt_attempt"] = play_dict["kickoff_attempt"] = 0
    play_dict["xp_result"] = play_dict["fg_result"] = play_dict["two_point_result"] = ""
    play_dict["kicker"] = play_dict["kick_distance"] = play_dict["kick_blocked"] = play_dict["blocked_player"] = play_dict["punter"] = "" 
    play_dict["punt_blocked"] = play_dict["punt_downed"] = play_dict["punt_out_of_bounds"] = play_dict["punt_fair_catch"] = play_dict["punt_returner"] ="" 
    play_dict["kickoff_downed"] = play_dict["kickoff_out_of_bounds"] = play_dict["kickoff_fair_catch"] = play_dict["kick_returner"] = ""
    if play_dict["play_type"] == "xp":
        play_dict["kick_blocked"] = 0
        play_dict["xp_attempt"] = 1
        if play_dict["sp"] == 1: play_dict["xp_result"] = "made"
        elif "blocked" in play_dict["desc"]: play_dict["xp_result"] = "blocked"
        else: play_dict["xp_result"] = "missed"

    elif play_dict["play_type"] == "fg":
        play_dict["kick_blocked"] = 0
        play_dict["fg_attempt"] = 1
        if play_dict["sp"] == 1: play_dict["fg_result"] = "made" 
        elif "blocked" in play_dict["desc"]: play_dict["fg_result"] = "blocked"
        else: play_dict["fg_result"] = "missed"   

    elif "kick" not in play_dict["desc"] and ("failed" in play_dict["desc"] or "good" in play_dict["desc"] or "Succes" in play_dict["desc"]):
        play_dict["two_point_attempt"] = 1
        if "good" in play_dict["desc"] or "Succes" in play_dict["desc"]: 
            play_dict["sp"] = 1
            play_dict["two_point_result"] = "success"
        else: play_dict["two_point_result"] = "fail"

    elif play_dict["play_type"] == "punt":
        punt_player =  re.findall("[A-Z][a-zA-Z-'.]*[Jr. ]*[ ,]*[A-Z][a-zA-Z-']*[Jr. ]* punt",play_dict["desc"])[0][:-5]
        play_dict["punter"] = truncate_name(punt_player, play_dict["posteam"])
        play_dict["punt_blocked"] = play_dict["punt_downed"] = play_dict["punt_out_of_bounds"] = play_dict["punt_fair_catch"] = 0
        play_dict["return_team"] = play_dict["defteam"]
        play_dict["punt_attempt"] = 1
        play_dict["punt_downed"] = play_dict["punt_out_of_bounds"] = play_dict["punt_fair_catch"] = 0
        if "downed" in play_dict["desc"]:
            play_dict["punt_downed"] = 1
        elif "out-of-bounds" in play_dict["desc"]:
            play_dict["punt_out_of_bounds"] = 1
        elif "fair catch" in play_dict["desc"]:
            play_dict["punt_fair_catch"] = 1

    elif play_dict["play_type"] == "kickoff":
        play_dict["kickoff_downed"] = play_dict["kickoff_out_of_bounds"] = play_dict["kickoff_fair_catch"] = 0
        play_dict["return_team"] = play_dict["defteam"]
        play_dict["kickoff_attempt"] = 1
        play_dict["kickoff_downed"] = play_dict["kickoff_out_of_bounds"] = play_dict["kickoff_fair_catch"] = 0
        if "downed" in play_dict["desc"]:
            play_dict["kickoff_downed"] = 1
        elif "out-of-bounds" in play_dict["desc"]:
            play_dict["kickoff_out_of_bounds"] = 1
        elif "fair catch" in play_dict["desc"]:
            play_dict["kickoff_fair_catch"] = 1

    if play_dict["play_type"] in ["punt", "fg", "xp"] or play_dict["play_type"] == "kickoff":
        if play_dict["play_type"] != "punt" and play_dict["desc"][0].isupper():
            kick_player = re.findall("[A-Z][a-zA-Z-'.]*[Jr. ]*[ ,]*[A-Z][a-zA-Z-']*[Jr. ]* (?:kick|onsi)", play_dict["desc"])
            if kick_player == []: kick_player = re.findall("[A-Z][a-zA-Z-'.]*[Jr. ]*[ ,]*[A-Z][a-zA-Z-']*[Jr. ]* field", play_dict["desc"])[0][:-6]
            else: kick_player = kick_player[0][:-5]
            play_dict["kicker"] = truncate_name(kick_player, play_dict["posteam"])
        if "blocked" in play_dict["desc"]:
            blocked_player =  re.findall("blocked by [A-Z][a-zA-Z-']*[ ,]*[A-Z][a-zA-Z-']*",play_dict["desc"])[0][11:]
            play_dict["blocked_player"] = truncate_name(blocked_player, play_dict["defteam"])
            if play_dict["play_type"] == "punt":
                play_dict["punt_blocked"] = 1
            elif play_dict["play_type"] in ["xp", "fg"]: play_dict["kick_blocked"] = 1
            play_dict["kick_distance"] = 0
            if "return" in play_dict["desc"]: play_dict["return_team"] = play_dict["defteam"]
        elif play_dict["play_type"] == "xp": play_dict["kick_distance"] = 20
        else:
            if re.findall(r'\d+', play_dict["desc"]) == []: play_dict["kick_distance"] == 0
            else: play_dict["kick_distance"] = int(re.findall(r'\d+', play_dict["desc"])[0])

    return_yards = 0
    if "return" in play_dict["desc"] and "NO PLAY" not in play_dict["desc"]:
        return_info = re.findall("return.*", play_dict["desc"])[0]
        return_player = re.findall("[A-Z][a-zA-Z-'.]*[ ,]*[A-Z][a-zA-Z-']*,* return", play_dict["desc"])
        if return_player == []:
            return_player = re.findall("returned by [A-Z][a-zA-Z-']*[ ,][a-zA-Z-']*", play_dict["desc"])[0][12:]
            if return_player[-1] == " ": return_player = return_player[:-1]
        else: return_player = return_player[0][:-7]
        play_dict["return_player"] = truncate_name(return_player, play_dict["return_team"])
        if len(re.findall("-*\d+", return_info)) > 0:
            return_yards = int(re.findall("-*\d+", return_info)[0])
            if "loss" in play_dict["desc"]: return_yards * -1
    
        if play_dict["play_type"] == "punt": play_dict["punt_returner"] = play_dict["return_player"]
        elif play_dict["play_type"] == "kickoff": play_dict["kick_returner"] = play_dict["return_player"]

    play_dict["return_yards"] = return_yards

    
def change_score(play_dict, info):
    home_team = play_dict["home_team"]
    away_team = play_dict["away_team"]
    if play_dict["posteam"] == home_team:
        play_dict["posteam_score"] = info["home_team_score"]
        play_dict["defteam_score"] = info["away_team_score"]
        play_dict["score_differential"] = play_dict["posteam_score"] - play_dict["defteam_score"]
    elif play_dict["posteam"] == away_team:
        play_dict["posteam_score"] = info["away_team_score"]
        play_dict["defteam_score"] = info["home_team_score"]
        play_dict["score_differential"] = play_dict["posteam_score"] - play_dict["defteam_score"]

    if play_dict["sp"] == 1:
        if play_dict["touchdown"] == 1:
            if play_dict["touchdown_team"] == home_team:
                info["home_team_score"] += 6
            elif play_dict["touchdown_team"] == away_team:
                info["away_team_score"] += 6
                
        elif play_dict["play_type"] == "fg":
            if play_dict["posteam"] == home_team:
                info["home_team_score"] += 3
            elif play_dict["posteam"] == away_team:
                info["away_team_score"] += 3

        elif play_dict["play_type"] == "xp":
            if play_dict["posteam"] == home_team:
                info["home_team_score"] += 1
            elif play_dict["posteam"] == away_team:
                info["away_team_score"] += 1

        elif play_dict["safety"] == 1:
            if play_dict["defteam"] == home_team:
                info["home_team_score"] += 2
            elif play_dict["defteam"] == away_team:
                info["away_team_score"] += 2

        elif play_dict["two_point_result"] == "success":
            if play_dict["posteam"] == home_team:
                info["home_team_score"] += 2
            elif play_dict["posteam"] == away_team:
                info["away_team_score"] += 2

    play_dict["home_team_score_post"] = info["home_team_score"]
    play_dict["away_team_score_post"] = info["away_team_score"]
    if play_dict["posteam"] == home_team:
        play_dict["posteam_score_post"] = info["home_team_score"]
        play_dict["defteam_score_post"] = info["away_team_score"]
        play_dict["score_differential_post"] = play_dict["posteam_score_post"] - play_dict["defteam_score_post"]
    else:
        play_dict["posteam_score_post"] = info["away_team_score"]
        play_dict["defteam_score_post"] = info["home_team_score"]
        play_dict["score_differential_post"] = play_dict["posteam_score_post"] - play_dict["defteam_score_post"]


def truncate_name(name,team):
    if name[-1] == ",": name = name[:-1]
    elif name[0] == " ": name = name[:1]
    return_name = name
    
    if team == "BAN": team = "TRI"
    if "," in name:
        names = re.split(",", name)
        return_name = names[1] + " " + names[0] 

    if " " == return_name[0]: return_name = return_name[1:]
    
    if return_name in NAME_DICT:
        return NAME_DICT[return_name][0]
    else:
        name_keys = list(NAME_DICT.keys())
        count = 0
        weird_case = False    
        if name_keys != []: is_similar = is_similar_name(return_name, name_keys[count], 2)
        else: is_similar = False

        while count < len(name_keys) and (not is_similar or (is_similar and team != NAME_DICT[name_keys[count]][1])):
            if " " in return_name and " " in name_keys[count]:
                first1, last1 = return_name.split(" ",1)
                first2, last2 = name_keys[count].split(" ",1)
                if ((first1 in first2 or first2 in first1) and (last1 in last2 or last2 in last1)) or \
                        (("." in first1 or "." in first2) and (last1 in last2 or last2 in last1)):
                    if first1[0] == first2[0] and last1[0] == last2[0]:
                        weird_case = True
                        break

            count += 1
            if count < len(name_keys): is_similar = is_similar_name(return_name, name_keys[count], 2) 

        if count < len(name_keys) and team == NAME_DICT[name_keys[count]][1] and return_name not in ["Jamar Bumpass", "Jack Ryan"]:
            if is_similar or weird_case:
                # print(f"{team}: {return_name} considered the same as {name_keys[count]}")
                NAME_DICT[return_name] = (NAME_DICT[name_keys[count]][0],team)

        else:
            NAME_DICT[return_name] = (return_name,team)
        
        return NAME_DICT[return_name][0]

def levenshtein_distance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for index2, char2 in enumerate(s2):
        new_distances = [index2 + 1]
        for index1, char1 in enumerate(s1):
            if char1 == char2:
                new_distances.append(distances[index1])
            else:
                new_distances.append(1 + min((distances[index1], distances[index1 + 1], new_distances[-1])))
        distances = new_distances

    return distances[-1]

def is_similar_name(name1, name2, max_distance=2):
    distance = levenshtein_distance(name1.lower(), name2.lower())
    return distance <= max_distance


def main():
    url = "https://athletics.hamilton.edu/sports/football/schedule/2022"
    bases = ["https://colbyathletics.com/", "https://gotuftsjumbos.com/", "https://athletics.hamilton.edu/", 
             "https://bantamsports.com/", "https://ephsports.williams.edu/", "https://gobatesbobcats.com",
             "https://athletics.bowdoin.edu/", "https://athletics.middlebury.edu/", "https://athletics.amherst.edu/", "https://athletics.wesleyan.edu/"]
    ext = "/sports/football/schedule/2022"
    links = []
    # bases = [bases[4]]
    bases = bases[:-1]

    print("Finding data...")
    for base in bases:
        url = base + ext
        html = parseHTML(url)
        get_game_links(html, base, links)

    #Ainsley is the coolest
    print("Loading all games...")
    games = {}
    info = {}
    count = 1
    for link in links:
        game_page = parseHTML(link)
        week, game_id = get_game_info(game_page)
        info[game_id] = week
        if game_id not in games:
            print(count, game_id)
            count += 1
            raw_pbp = game_page.find("section", id="play-by-play").find_all("td")
            games[game_id] = clean_pbp(raw_pbp)
        
    print("Analyzing play by play for data...")
    official_pbp = []
    play_id = 1
    for game_id in games:
        play_id = format_pbp(games[game_id], game_id, official_pbp, play_id)

    pbp_data = {}
    info["posteam"] = info["defteam"] = info["posteam_type"] = info["time"] = ""
    info["drive"] = info["drive_first_downs"] = info["yards_net"] = info["drive_plays"] = 0
    info["game_half"] = "Half1"
    info["quarter"] = 1
    info["home_team_timeouts_remaining"] = info["away_team_timeouts_remaining"] = 3
    info["posteam_timeouts_remaining"] = info["defteam_timeouts_remaining"] = 3
    info["home_team_score"] = info["away_team_score"] = info["posteam_score"] = info["defteam_score"] = 0
    info["change_of_possession"] = 0
    for play in official_pbp:
        play_id = play[13:play.index('\n')]
        pbp_data[play_id] = {}
        parse_line(pbp_data[play_id], play, info)
        if pbp_data[play_id]["game_id"] == "BOW_BAN2022":
            for key in pbp_data[play_id]:
                if isinstance(pbp_data[play_id][key], str) and "BAN" in pbp_data[play_id][key]:
                    pbp_data[play_id][key] = re.sub("BAN", "TRI", pbp_data[play_id][key])
        if pbp_data[play_id]["game_id"] in ["WES_AMH2022", "BAT_WES2022"]:
            pbp_data[play_id]["down"] = pbp_data[play_id]["yardline"] = pbp_data[play_id]["yardline100"] = ""
            pbp_data[play_id]["side_of_field"] = pbp_data[play_id]["yds_to_go"] = ""

    with open("nescac_pbp.csv", mode="w") as csvfile:
        fieldnames = pbp_data["1"].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for play_id in pbp_data:
            writer.writerow(pbp_data[play_id])


    print("Play by play data has been written")


if __name__ == "__main__":
    main()