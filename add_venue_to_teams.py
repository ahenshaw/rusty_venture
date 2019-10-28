import json
import argparse
import sqlite3


DATABASE = '/repos/soccer/data/soccer.db'

SQL_CLUB  = 'SELECT id FROM club WHERE name=?'
SQL_VENUE = '''SELECT venue_id, venue.name, venue.lat, venue.lon
               FROM club_venue 
               JOIN venue ON venue_id=venue.id
               WHERE club_id=?'''
               
SQL_COST  = 'SELECT cost     FROM venue_venue WHERE home_id=? and away_id=?'

def add_venues(data):
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    
    okay = True
    duplicates = set()
    for team in data['teams']:
        clubname = team['clubname']
        cursor.execute(SQL_CLUB, (clubname,))
        results = cursor.fetchall()
        if not results:
            if clubname not in duplicates:
                print('Club not found:', clubname)
                duplicates.add(clubname)
            okay = False
        elif len(results) > 1:
            print('Multiple IDs for:', clubname)
            okay = False
        else:
            club_id, = results[0]
            cursor.execute(SQL_VENUE, (club_id,))
            results = cursor.fetchall()
            if not results:
                print('Venue not found for', clubname)
                okay = False
            else:
                team.update(dict(zip(['venue_id', 'venue', 'lat', 'lon'], results[0])))
    return okay

def add_costs(data):
    ''' Get the cost (time) associated with traveling from 
        venue to venue
    '''
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    
    okay = True
    costs = {}
    teams = data['teams']
    # use the conflicts list, if present in the JSON
    conflicts = set(data.get('conflicts', []))
    for home in teams:
        team_costs = {}
        for away in teams:
            cursor.execute(SQL_COST, (home['venue_id'], away['venue_id']))
            results = cursor.fetchone()
            if results:
                cost, = results
                team_costs[away['gssa_id']] = cost
            else:
                print('Missing cost for', (home['venue'], away['venue']) )
                okay = False
            if (home['flt_pos'], away['flt_pos']) in conflicts or \
               (away['flt_pos'], home['flt_pos']) in conflicts:
                   print("conflict detected", home['flt_pos'], away['flt_pos'])
                   team_costs[away['gssa_id']] = 1e10
        costs[home['gssa_id']] = team_costs
    data['costs'] = costs
    return okay

def load(args):
    fp = open('{}/{}.json'.format(args.path, args.division))
    return json.load(fp)

def store(data, args):
    with open('{}/{}.json'.format(args.path, args.division), 'w') as outfile:
        json.dump(data, outfile, indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('division', help='Input file name')
    parser.add_argument('--path', default='season')
    args = parser.parse_args()
    data = load(args)
    if add_venues(data):
        if add_costs(data):
            store(data, args)


