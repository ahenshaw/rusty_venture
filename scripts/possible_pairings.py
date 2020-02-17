import sys
import sqlite3
import csv

from settings import CONFLICTS

DATABASE = 'data/soccer.db'

SQL_CLUB  = 'SELECT id       FROM club WHERE name=?'
SQL_VENUE = '''SELECT venue_id, venue.name, venue.lat, venue.lon
               FROM club_venue 
               JOIN venue ON venue_id=venue.id
               WHERE club_id=?'''
               
SQL_COST  = 'SELECT cost     FROM venue_venue WHERE home_id=? and away_id=?'

def get_venues(teams):
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    
    # these csv files are just for post analysis
    team_venue_log = csv.writer(open('data/team_venue.csv', 'w', newline=''), 
                                delimiter=',')
    team_log       = csv.writer(open('data/team.csv', 'w', newline=''), 
                                delimiter=',')
    team_venue_log.writerow(['team_id', 'venue_id'])
    team_log.writerow(['id', 'name'])
    okay = True
    print()
    duplicates = set()
    for team in teams:
        cursor.execute(SQL_CLUB, (team.clubname,))
        results = cursor.fetchall()
        if not results:
            if team.clubname not in duplicates:
                print('Club not found:', team.clubname)
                duplicates.add(team.clubname)
            okay = False
        elif len(results) > 1:
            print('Multiple IDs for:', team.clubname)
            okay = False
        else:
            team.club_id, = results[0]
            cursor.execute(SQL_VENUE, (team.club_id,))
            results = cursor.fetchall()
            if not results:
                print('Venue not found for', team.clubname)
                okay = False
            else:
                #print(results)
                team.venue_id, team.venue, team.lat, team.lon = results[0]
                team_log.writerow((team.flt_pos, team.name))
                team_venue_log.writerow((team.flt_pos, team.venue_id))
            
    return okay

def get_costs(teams):
    ''' Get the cost (time) associated with traveling from 
        venue to venue
    '''
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    
    okay = True
    costs = {}
    for i, home in enumerate(teams):
        for j, away in enumerate(teams):
            cursor.execute(SQL_COST, (home.venue_id, away.venue_id))
            results = cursor.fetchone()
            if results:
                cost, = results
                ## cost_squared[(i, j)] = cost * cost
                costs[(i, j)] = cost
            else:
                print('Missing cost for', (home.venue_id, away.venue_id) )
                okay = False
            if (home.flt_pos, away.flt_pos) in CONFLICTS or \
               (away.flt_pos, home.flt_pos) in CONFLICTS:
                   print("conflict detected", home.flt_pos, away.flt_pos)
                   ## cost_squared[(i, j)] = 1e10
                   costs[(i, j)] = 1e10
    return costs

                
if __name__ == '__main__':
    FILENAME = 'c:/users/ah6/Downloads/U19G-Spring-2015.xml'
    from team_report import get_teams
    teams = get_teams(FILENAME)
    print(len(teams))
    print(get_costs(teams))
    
        