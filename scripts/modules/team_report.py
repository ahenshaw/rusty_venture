import pymysql
from datetime import datetime

ACCEPTABLE = 'Accepted'

class Team:
    def __init__(self, node):
        self.blackout   = None
        self.black_home = []
        self.black_away = []
        self.__dict__.update(node)
        if self.blackout is not None and self.blackout != 'blackout':
            for blackout in self.blackout.split(','):
                desc = blackout.strip().lower().split(' ', 1)
                if len(desc) == 1:
                    desc.append('home & away')
                date = datetime.strptime(desc[0], '%m/%d/%Y').date()
                if 'home' in desc[1]:
                    self.black_home.append(date)
                if 'away' in desc[1]:
                    self.black_away.append(date)
                    
    def __str__(self):
        home = '  Home blackout: %s' % self.black_home if self.black_home else ''
        away = '  Away blackout: %s' % self.black_away if self.black_away else '' 
        other = '{:>4s} {:16s}  {:16s}'.format(self.flt_pos, truncate(self.clubname, 16), truncate(self.name, 16))
        
        # return '\n'.join(filter(None, [other, home, away]))
        return other
        
    def __lt__(self, other):
        return (self.name < other.name)

def truncate(s, width):
    if len(s) > width:
        s = s[0:width-5]+'..'+s[-3:]
    return s

def get_teams(db, division):
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute('''
        SELECT team.id, name, venue, venue_id, clubname, COALESCE(team.flt_pos, '--') as flt_pos, comment, division_id, outlier, blackout
        FROM team 
        LEFT JOIN division ON division.id=division_id
        WHERE division.label=%s
        ORDER BY name''', division)
    teams = []
    count = 0
    for i, record in enumerate(cursor.fetchall()):
        t = Team(record)
        t.seq = i
        t.division = division
        if t.flt_pos == '--':
            t.flt_pos = f'Z{i:02}'
        teams.append(t)
    return teams

def get_costs(db, teams):
    ''' Get cost of travel from team to team (indexed by position in list)'''
    cursor = db.cursor()
    cursor.execute('''
        SELECT home_id, away_id, cost
        FROM venue_venue''')
    venue_costs = {(hid, aid):cost for hid, aid, cost in cursor.fetchall()}
    costs = dict()
    for h in teams:
        for a in teams:
            if h == a:
                cost = 100000
            else:
                cost = venue_costs[(h.venue_id, a.venue_id)]
            costs[h.seq, a.seq] = cost
    return costs

def get_weights(db, teams):
    ''' Get cost of travel from team to team.
        If teams involved have conflicts, mark cost as very high.'''
    cursor = db.cursor()
    cursor.execute('''
        SELECT home_id, away_id, cost
        FROM venue_venue''')
    venue_costs = {(hid, aid):cost for hid, aid, cost in cursor.fetchall()}

    cursor.execute('SELECT t1, t2 FROM conflict WHERE division=%s', teams[0].division)
    conflicts = set()
    for t1, t2 in cursor.fetchall():
        conflicts.add((t1, t2))
        conflicts.add((t2, t1))

    costs = dict()
    for h in teams:
        for a in teams:
            if h == a:
                cost = 100000
            elif (h.flt_pos, a.flt_pos) in conflicts:
                cost = 100000
                print('conflict', h.id, a.id)
            else:
                cost = venue_costs[(h.venue_id, a.venue_id)]
                if cost>1000:
                    print(h.venue_id)
            costs[h.id, a.id] = cost

    return costs

def get_venues(db, teams):
    cursor = db.cursor()
    # prepare clubname lookup table
    cursor.execute('''
        SELECT name, club_id, venue_id 
        FROM club_venue 
        LEFT JOIN club 
        ON club_id=club.id''')
    lookup = dict([(x, (y, z)) for x,y,z in cursor.fetchall()])
    complete = True
    missing = set()

    # find venue_id for teams
    for team in teams:
        cn = team.clubname
        if cn not in missing:
            if cn not in lookup:
                print(f'{cn} is not in database')
                complete = False
                missing.add(cn)
            else:
                team.venue_id = lookup[cn][1]
    return complete


if __name__ == '__main__':
    from database import get_db

    db = get_db()
    teams = get_teams(db, 'B14R')
    for team in teams:
        print(team)
