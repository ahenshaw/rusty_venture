from datetime import datetime
from collections import Counter
import json

ACCEPTABLE = 'Accepted'

class Team:
    def __init__(self, node):
        self.blackout   = None
        self.black_home = []
        self.black_away = []
        self.__dict__.update(node)
        # if self.blackout is not None and self.blackout != 'blackout':
        #     for blackout in self.blackout.split(','):
        #         desc = blackout.strip().lower().split(' ', 1)
        #         if len(desc) == 1:
        #             desc.append('home & away')
        #         date = datetime.strptime(desc[0], '%m/%d/%Y').date()
        #         if 'home' in desc[1]:
        #             self.black_home.append(date)
        #         if 'away' in desc[1]:
        #             self.black_away.append(date)
                
        #~ print self.blackout
    
    def __str__(self):
        home = '  Home blackout: %s' % self.black_home if self.black_home else ''
        away = '  Away blackout: %s' % self.black_away if self.black_away else '' 
        other = '{:4s} {}  {:16s}  {:16s}'.format(self.flt_pos, self.gssa_id[8:12], truncate(self.clubname, 16), truncate(self.name, 16))
        
        #~ return '\n'.join(filter(None, [other, home, away]))
        return other
        
    def __lt__(self, other):
        return (self.name < other.name)

def truncate(s, width):
    if len(s) > width:
        s = s[0:width-5]+'..'+s[-3:]
    return s

        
def get_teams(filename):
    teams = []
    with open(filename) as json_file:
        data = json.load(json_file)
        for node in data['teams']:
            team = Team(node)
            if team.status == ACCEPTABLE and team.flt_pos is not None:
                teams.append(team)
    return teams

def get_teams_from_json(data):
    teams = []
    for node in data['teams']:
        team = Team(node)
        if team.status == ACCEPTABLE and team.flt_pos is not None:
            teams.append(team)
    return teams

if __name__ == '__main__':
    teams = get_teams('../season/B14R.json')
    for team in teams:
        print(team)
        print('   {} {} {}', team.blackout, team.black_home, team.black_away)
