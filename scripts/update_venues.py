import json
import argparse
import sqlite3


DATABASE = '/repos/soccer/data/soccer.db'

SQL_VENUE = '''SELECT id, venue.name, venue.lat, venue.lon
               FROM venue
               WHERE name like ?'''
               
SQL_COST  = 'SELECT cost FROM venue_venue WHERE home_id=? and away_id=?'

def check_venues(data):
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    
    ok = True
    for team in data['teams']:
        if 'venue_id' not in team:
            #print(team['name'], team['venue'])
            cursor.execute(SQL_VENUE, (team['venue'],))
            row = cursor.fetchone()
            if row is None:
                print(team['venue'])
                ok = False
            else:
                team['venue_id'] = str(row[0])
                team['venue']    = str(row[1])
                team['lat']      = str(row[2])
                team['lon']      = str(row[3])
    return ok

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
                team_costs[away['venue_id']] = cost
            else:
                print('Missing cost for', (home['venue'], away['venue']) )
                okay = False
            if (home['flt_pos'], away['flt_pos']) in conflicts or \
               (away['flt_pos'], home['flt_pos']) in conflicts:
                   print("conflict detected", home['flt_pos'], away['flt_pos'])
                   team_costs[away['venue_id']] = 1e10
        costs[home['venue_id']] = team_costs
    data['costs'] = costs
    return okay

def load(args):
    fp = open('{}.json'.format(args.division))
    return json.load(fp)

def store(data, args):
    with open('{}.json'.format(args.division), 'w') as outfile:
        json.dump(data, outfile, indent=4)


if __name__ == '__main__':
    import sys
    sys.argv.append('/repos/soccer_ng/season/B12X')
    parser = argparse.ArgumentParser()
    parser.add_argument('division', help='Input file name')
    args = parser.parse_args()
    data = load(args)
    if check_venues(data):
        if add_costs(data):
            store(data, args)


