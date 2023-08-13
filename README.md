# NESCAC Scrapr
Web Scrapes the NESCAC Football play by play data from the 2022 Season. This play by play data is provided by SIDEARM Sports and as a result this code is applicable to any SIDEARM Sport football play by play website. This scraper reads each play and extrapolates **131** variables of data to be used for analysis. The variables are outlined below. The main file is *scrape.py* and the raw CSV of NESCAC outputted is included. 

## NOTES
* The logic is applicable to all play by play data represented by SIDEARM Sports but the file is specific to the NESCAC data and as such there are many hardcoded error fixes specific to this data. For example Trinity College was labeled as Ban instead of TRI for one game and that was fixed. Additionally, not all the information is available online. Notably the down and distance information is missing from the Wesleyan Bates game from this past year and has been slighlty adjusted as a result. 
* Names were the most common incorrect infromation. I incoporated the Levenshtein distance and other strategies to match names to the best of my ability. 2 names were incorrectly matched as they were differnt by one charachter and played on the same team. As a result these names were accounted for. In order to see which names have been changed you can uncomment the print statement near line 800. 
* The game links for the NESCAC or coded into the main function but can be altered for any conferences that utilizes the same PBP format. 

## Variables
play_id -- Unique Play ID  
game_id -- Unique Game ID  
home_team -- Home team  
away_team -- Away team  
week -- Week game was played  
posteam -- Possession Team  
posteam_type -- If possession team is home or away  
defteam -- Team on defense  
game_half -- Half of game  
drive -- Drive number in game  
drive_plays -- Number of plays on the drive  
quarter -- Quarter of game  
home_team_score -- Score of the home team  
away_team_score -- Score of away team  
posteam_score -- Score of possesion team  
defteam_score -- Score of defensive team  
score_differential -- Possesion Team Score - Defensive Team Score  
side_of_field -- What team side the ball is on  
yardline100 -- How far team is from endzone  
down -- Down  
yds_to_go -- Distance for first down  
goal_to_go -- Binary indicator if play is goal to go  
sp -- Binary indicator if play is a scoring play  
yardline -- Yardline  
play_type -- Playtype: pass, rush, fg, xp, kickoff, punt, No Play, qb_kneel, NA  
desc -- Play description from PBP  
yards_gained -- Yards gained on the play  
first_down -- Binary indicator if play was a first down  
first_down_pass -- Binary indicator if first down was from a pass  
first_down_rush -- Binary indicator if frist down was from a rush  
first_down_penalty -- Binary indicator if first down was a penalty  
third_down_failed -- Binary indicator if the 3rd down wasn't converted  
third_down_converted -- Binary indicator if the 3rd down was converted  
fourth_down_attempted -- Binary indicator if the 4th down was attempted  
fourth_down_failed -- Binary indicator if the 4th down wasn't converted  
fourth_down_converted -- Binary indicator if the 4th down was converted  
rush_attempt -- Binary indicator if the play was a rush  
pass_attempt -- Binary indicator if the play was a pass  
rusher -- Rusher name  
passer -- Passer name  
receiver -- Receiver name  
targeted_receiver -- Targeted receiver name  
rushing_yards -- Number of rushing yards on the play  
passing_yards -- Number of passing yards on the play  
receiving_yards -- Number of receiving yards on the play  
yards_net -- Total yards gained on the drive  
drive_first_downs -- Total number of first downs on the drive  
touchdown -- Binary indicator if the play was a touchdown  
pass_touchdown -- Binary indicator if the touchdown was a pass  
rush_touchdown -- Binary indicator if the touchdown was a rush  
return_touchdown -- Binary indicator if the touchdwon was a return (special teams or interception / fumble)  
touchdown_team -- Scoring team  
touchdown_player -- Scoring player  
complete_pass -- Binary indicator if pass was complete  
incomplete_pass -- Binary indicator if pass was incomplete  
solo_tackle -- Binary indicator if tackle was a solo tackle  
assisted_tackle -- Binary indicator if tackle was an assited tackle  
tackled_for_loss -- Binary indicator if tackle was for a loss  
tackled_for_loss_yards -- Yards lost if it was a TFL  
sack -- Binary indicator if play was a sack  
sack_yards -- Yards lost if it was a sack  
half_tfl -- Binary indicator if it was an assited TFL  
full_tfl -- Binary indicator if it was a solo TFL  
full_sack -- Binary indicator if it was a solo sack  
half_sack -- Binary indicator if it was an assited sack  
penalty -- Binary indicator if there was a penalty  
penalty_team -- Penalty team  
penalty_type -- Penalty that was called  
penalty_accepted -- Binary indicator if the penalty was accepted  
penalty_yards -- Yards from the penalty  
penalty_player -- Penalty player (if present)  
fumble -- Binary indicator if there was a fumble  
interception -- Binary indicator if there was an interceptiom  
interception_player -- Interception player  
pass_deflection_player -- Player who broke up the pass  
fumble_lost -- Binary indicator if the fumble was lost  
fumble_forced -- Binary indicator if the fumble was  
fumble_team -- Team that fumbled  
fumble_recovery_team -- Team that recovered the fumbled  
forced_fumble_player -- Player that forced the fumble  
fumble_recovery_player -- Player that recovered the fumble  
return_yards -- Yards gained on a return  
return_team -- Team returning the ball  
touchback -- Binary indicator if there was a touchback  
return_player -- Return player name  
assisted_tackle_player_1 -- Assisted tackle player name (1)  
assisted_tackle_player_2 -- Assisted tackle player name (2)  
solo_tackle_player -- Solo tackle player name  
tackle_for_loss_player_1 -- Tackle for loss player name (1)  
tackle_for_loss_player_2 -- Tackle for loss player name (2)  
sack_player_1 -- Sack player name (1)  
sack_player_2 -- Sack Player name (2)  
solo_tackle_player_2 -- Solo tackler player name (2 if there was a fumble)  
timeout -- Binary indicator if there was a timeout called  
timeout_team -- Timeout team  
safety -- Binary indicator if there was a safety  
posteam_score_post -- Posteam score after the play  
defteam_score_post -- Defteam score after the play  
score_differential_post -- Score differential after the play  
home_team_score_post -- Home team score after the play  
away_team_score_post -- Away team score after the play  
recent_time -- Most recent seen time  
quarter_time -- Most recent time in quarter (early, mid, late)  
late_half -- Binary indicator if the play is late in the half  
change_of_possession -- Binary indicator if there was a change of possesssion on the play  
home_team_timeouts_remaining -- Number of home team timeouts remaining  
away_team_timeouts_remaining -- Number of away team timeouts remaining  
posteam_timeouts_remaining -- Number of posteam timeouts remaining  
defteam_timeouts_remaining -- number of defteam timeouts remaining  
xp_attempt -- Binary indicator if play was an xp attempt  
fg_attempt -- Binary indicator if play was a fg attempt  
two_point_attempt -- Binary indicator if play was a two point attempt  
punt_attempt -- Binary indicator if play was a punt attempt  
kickoff_attempt -- Binary indicator if play was a kickoff  
xp_result -- Extra point result: made, missed, blocked  
fg_result -- Field Goal result: made, missed, blocked   
two_point_result -- Result of two point conversion: fail, success  
kicker -- kicker name  
kick_distance -- Distance of fg, xp, kickoff or punt  
kick_blocked -- Binary indicator if kick was blocked  
blocked_player -- Player who blocked kick  
punter -- Punter name  
punt_blocked -- Binary indicator if punt was blocked  
punt_downed -- Binary indicator if punt was downed  
punt_out_of_bounds -- Binary indicator if punt was out of bounds  
punt_fair_catch -- Binary indicator if punt was fair caught  
punt_returner -- Punt Returner name  
kickoff_downed -- Binary indicator if kickoff was downed  
kickoff_out_of_bounds -- Binary indicator if kickoff was out of bounds  
kickoff_fair_catch -- Binary indicator if kickoff was fair caught  
kick_returner -- Kick returner name  
