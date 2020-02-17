''' 
To be used for Select teams where each team needs
to be in a group where every teams plays all of the other
teams.
'''

import sys
from itertools import product, combinations
from argparse import ArgumentParser
from modules.database import get_db
import pymysql
from random import shuffle
import copy

# custom modules
from modules.team_report import get_teams_from_json

OPTIMIZE_TIME = 600 # seconds

def get_weights(db, teams):
    cursor = db.cursor()
    cursor.execute('SELECT home_id, away_id, cost FROM venue_venue')
    costs = dict((((h, a), cost) for (h, a, cost) in cursor.fetchall()))
    weights = {}
    for t1 in teams:
        for t2 in teams:
            if t1 == t2:
                w = 100000
            else:
                try:
                    w = costs[t1['venue_id'],t2['venue_id']]
                except:
                    print(repr(t1['venue_id']))
                    print(repr(t2['venue_id']))
                    print(costs)
                    raise
            weights[t1['flt_pos'], t2['flt_pos']] = w
    return weights

def get_teams(db, division_id):
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute('SELECT id, flt_pos, venue_id, name FROM team WHERE division_id=%s', (division_id,))
    return cursor.fetchall()

def get_params():
    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('division', help='Team agegroup or division')
    params = parser.parse_args()

    return params

def score(groups, weights):
    total = 0
    for sub in groups:
        for x, y in combinations(sub, 2):
            total += 2*weights[(x, y)]
    return total

def assign_to_groups(group_sizes, team_codes, weights):
    # rank teams by distance from others
    ranking = []
    closest = {}
    for team in team_codes:
        total = 0
        others = []
        for other in team_codes:
            if other != team:
                total += weights[team, other]
                others.append((weights[team, other], other))
        others.sort()
        closest[team] = [x[1] for x in others]
        ranking.append((total, team))
    ranking = [x[1] for x in sorted(ranking, reverse=True)]

    # make the first assignment to each group
    unused = []
    assigned = 0
    # we will assign the most remote to the smallest groups
    group_sizes.sort()
    min_size = group_sizes[0]
    # make the empty groups
    groups = [[] for i in range(len(group_sizes))]
    while assigned < len(group_sizes):
        candidate = ranking.pop(0)
        for i in range(assigned):
            # check to see if candidate is one of the closest to the group anchor
            if candidate in closest[groups[i][0]][:min_size]:
                print(f'{candidate} should go in group {i}')
                unused.append(candidate)
                break
        else:
            # not a good candidate to go with an existing group
            groups[assigned].append(candidate)
            assigned += 1
    unused.extend(ranking)
    while unused:
        x = unused.pop(0)
        # add x to each group in turn and choose the group
        # that gives the lowest score
        scores = []
        for i in range(len(groups)):
            if len(groups[i]) < group_sizes[i]:
                # group isn't full, okay to test
                temp = copy.deepcopy(groups)
                temp[i].append(x)
                scores.append((score(temp, weights), i))
        # assign to best group
        scores.sort()
        groups[scores[0][1]].append(x)
        print(f'put {x} in group {scores[0][1]}')
    return groups




def simple_assign_to_groups(group_sizes, team_codes, weights):
    index = 0
    groups = []
    for g in group_sizes:
        groups.append(team_codes[index:index+g])
        index += g
    return groups

if __name__ == '__main__':
    group_sizes = [6, 6, 6, 5]
    label = '-'.join(map(str,group_sizes))
    params = get_params()
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM division where label=%s', params.division)
    division_id, = cursor.fetchone()

    teams = get_teams(db, division_id)
    shuffle(teams)
    weights = get_weights(db, teams)

    # team_codes = dict([(x['flt_pos'], x) for x in teams])
    team_codes = [x['flt_pos'] for x in teams]
    groups = assign_to_groups(group_sizes, team_codes, weights)
    print(score(groups, weights))
    for group in groups:
        print(group)

    for team in sorted(teams, key=lambda x: x['flt_pos']):
        print(team['flt_pos'], team['name'])


    
