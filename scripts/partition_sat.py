''' 
Replaces make_pairings_xp
To-do:  
    * Handle outliers
'''

import sys
import time
import json
from itertools import product
from collections import Counter
from argparse import ArgumentParser
from modules.database import get_db
import pymysql

# third-party 
# from gurobipy import *
from ortools.sat.python import cp_model

# custom modules
from modules.team_report import get_teams_from_json

def pairings_sat(teams, weights, groups):

    m = cp_model.CpModel()
    x = {}
    for i in teams:
        for j in teams:
            if i != j:
                for g in range(len(groups)):
                    x[i, j, g] = m.NewBoolVar('x[%s,%s,%s]'% (i, j, g))
    gt = {}
    for g in range(len(groups)):
        for i in teams:
            gt[g, i] = m.NewBoolVar('gt[%s,%s]'% (g, i))

    # create a multiplier for weighting.  If home-and-home, then multiplier
    # is 2, otherwise 1
    scale = [(2 if group < 8 else 1) for group in groups]

    ### constraints ###

    # for each group, each team must play number of games 
    # equal to 'rounds' for that group
    for g in range(len(groups)):
        doubled_games = groups[g]*(groups[g]-1)
        expr = []
        for i in teams:
            for j in teams:
                if i != j:
                    expr.append(x[i, j, g])
        m.Add(sum(expr) == doubled_games)

    # each game with teams (i, j) must also be played by teams (j,i) in group g
    for i in teams:
        for j in teams:
            if i != j:
                for g in range(len(groups)):
                    expr = []
                    expr.append(x[i, j, g])
                    expr.append(-x[j, i, g])
                    m.Add(sum(expr) == 0)

    # each team i must belong to only one group
    for i in teams:
        expr = []
        for g in range(len(groups)):
            expr.append(gt[g, i])
        m.Add(sum(expr) == 1)

    # link gt and x
    # x_ijg >= g_li + g_lj - 1
    for i in teams:
        for j in teams:
            if i != j:
                for g in range(len(groups)):
                    m.Add(1 >= gt[g, i] + gt[g, j] - x[i, j, g])
                    m.Add(gt[g, i] >= x[i, j, g])
                    m.Add(gt[g, j] >= x[i, j, g])


    # each team i can play j at most once
    for i in teams:
        for j in teams:
            expr = []
            if i != j:
                for g in range(len(groups)):
                    expr.append(x[i, j, g])
            m.Add(sum(expr) <= 1)

    final = sum([weights[i,j]*x[i,j,g]*scale[g] for (i,j,g) in x])
    m.Minimize(final)
    
    solver = cp_model.CpSolver()
    # solver.parameters.max_time_in_seconds = 180.0
    time.clock()
    status = solver.Solve(m)
    print('Elapsed:', time.clock())
    print(status == cp_model.OPTIMAL, status== cp_model.FEASIBLE)

    results = set()
    for key, variable in sorted(x.items()):
        if int(solver.Value(variable)) >= 1:
            i, j, g = key
            if (j, i, g) not in results:
                results.add((i, j, g))
                if scale[g] == 2:
                    results.add((j, i, g))

    print(sorted(results))                   
    return sorted(results)

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
    cursor.execute('SELECT id, flt_pos, venue_id FROM team WHERE division_id=%s', (division_id,))
    return cursor.fetchall()

def get_params():
    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('division', help='Team agegroup or division')
    params = parser.parse_args()

    return params

if __name__ == '__main__':
    sys.argv.append('B12X')
    groups = [6,6,6,5]
    label = '-'.join(map(str,groups)) + 'SAT'
    params = get_params()
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM division where label=%s', params.division)
    division_id, = cursor.fetchone()

    # filename = "{}.json".format(params.division)
    # with open(filename) as fh:
    #     division = json.load(fh)
    teams = get_teams(db, division_id)
    # teams = division['teams']
    weights = get_weights(db, teams)

    team_codes = dict([(x['flt_pos'], x) for x in teams])
    # results = pairings(team_codes.keys(), weights, groups)
    results = pairings_sat(team_codes.keys(), weights, groups)

    round_count = Counter()
    pairings = []
    for i, j, g in results:
        # print(g, i, j)
        team_codes[i]['group'] = g
        team_codes[j]['group'] = g
        r = max(round_count[i], round_count[j])
        pairings.append((r, i, j, weights[i,j]))
        round_count[i] += 1
        round_count[j] += 1

    # division['pairings'] = pairings
    # with open(filename, 'w') as fh:
    #     json.dump(division, fh, indent=4)
    records = []
    for r,i,j,cost in pairings:
        h = team_codes[i]['id']
        a = team_codes[j]['id']
        records.append((division_id, label, h, a, cost))
    if records:
        cursor.execute('DELETE FROM pairing WHERE division_id=%s AND label=%s', (division_id, label))
        cursor.executemany('INSERT INTO pairing (division_id, label, home, away, cost) VALUES (%s, %s, %s, %s, %s)', records)
        db.commit()
    print('{} teams'.format(len(teams)))
    print('{} pairings added or replaced in data'.format(len(pairings)))

