''' 
To be used for Select teams where each team needs
to be in a group where every teams plays all of the other
teams.
'''

import sys
import json
from itertools import product
from collections import Counter, defaultdict
from argparse import ArgumentParser
from modules.database import get_db
import pymysql

# third-party 
from gurobipy import *

# custom modules
from modules.team_report import get_teams_from_json

OPTIMIZE_TIME = 600 # seconds

def pairings(teams, weights, groups):
    LARGE_UPPER_BOUND = 200  # to-do: compute an actual upper bound from data

    m = Model()
    # m.setParam('OutputFlag', 0)
    m.setParam('TimeLimit', OPTIMIZE_TIME)

    # x = {}
    # for i in teams:
    #     for j in teams:
    #         if i != j:
    #             for g in range(len(groups)):
    #                 x[i, j, g] = m.addVar(0, 1, 0, GRB.BINARY, 'x[%s,%s,%s]'% (i, j, g))
    gt = {}
    for g in range(len(groups)):
        for i in teams:
            gt[g, i] = m.addVar(0, 1, 0, GRB.BINARY, 'gt[%s,%s]'% (g, i))

    m.update()

    # create a multiplier for weighting.  If home-and-home, then multiplier
    # is 2, otherwise 1
    scale = [(2 if x < 8 else 1) for x in groups]
    ### constraints ###

    # each group must have team count equal to group value
    for g in range(len(groups)):
        expr = LinExpr()
        for i in teams:
            expr.addTerms( 1, gt[g, i])
        m.addConstr(expr, GRB.EQUAL, groups[g])

    # # x[i,j,g_2] <= 1 - gt[g_1,i]
    # for i in teams:
    #     for j in teams:
    #         if i != j:
    #             for g1 in range(len(groups)):
    #                 for g2 in range(len(groups)):
    #                     if g1 != g2:
    #                         m.addConstr(1-gt[g1, i], GRB.GREATER_EQUAL, x[i, j, g2])

    # # for each group, each team must play number of games 
    # # equal to 'rounds' for that group
    # for g in range(len(groups)):
    #     doubled_games = groups[g]*(groups[g]-1)
    #     expr = LinExpr()
    #     for i in teams:
    #         for j in teams:
    #             if i != j:
    #                 expr.addTerms(1, x[i, j, g])
    #     m.addConstr(expr, GRB.EQUAL, doubled_games)

    # # each game with teams (i, j) must also be played by teams (j,i) in group g
    # for i in teams:
    #     for j in teams:
    #         if i != j:
    #             for g in range(len(groups)):
    #                 expr = LinExpr()
    #                 expr.addTerms( 1, x[i, j, g])
    #                 expr.addTerms(-1, x[j, i, g])
    #                 m.addConstr(expr, GRB.EQUAL, 0)

    # each team i must belong to only one group
    for i in teams:
        expr = LinExpr()
        for g in range(len(groups)):
            expr.addTerms( 1, gt[g, i])
        m.addConstr(expr, GRB.EQUAL, 1)

    # # link gt and x
    # # x_ijg >= gt_gi + gt_gj - 1
    # for i in teams:
    #     for j in teams:
    #         if i != j:
    #             for g in range(len(groups)):
    #                 expr = LinExpr()
    #                 expr.addTerms( -1, x[i, j, g])
    #                 expr.addTerms( 1, gt[g, i])
    #                 expr.addTerms( 1, gt[g, j])
    #                 m.addConstr(1, GRB.GREATER_EQUAL, expr)

    #                 m.addConstr(gt[g, i], GRB.GREATER_EQUAL, x[i, j, g])
    #                 m.addConstr(gt[g, j], GRB.GREATER_EQUAL, x[i, j, g])


    # # each team i can play j at most once
    # for i in teams:
    #     for j in teams:
    #         expr = LinExpr()
    #         if i != j:
    #             for g in range(len(groups)):
    #                 expr.addTerms( 1, x[i, j, g])
    #         m.addConstr(expr, GRB.LESS_EQUAL, 1)

    final = QuadExpr()
    for g in range(len(groups)):
        for i in range(len(teams)-1):
            for j in range(i+1, len(teams)):
                t1 = list(teams)[i]; t2 = list(teams)[j]
                final.addTerms(scale[g]*weights[t1,t2], gt[g, t1], gt[g, t2])


    # final = quicksum([weights[i,j]*x[i,j,g]*scale[g] for (i,j,g) in x])
    m.setObjective(final)
    m.update()
    m.write('quadmodel.lp')
    m.optimize()

    # results = set()
    # for xvd in sorted(x):
    #     if int(x[xvd].X) >= 1:
    #         i, j, g = xvd
    #         if (j, i, g) not in results:
    #             results.add((i, j, g))
    #             if scale[g] == 2:
    #                 results.add((j, i, g))

    gout = defaultdict(list)
    for gi in sorted(gt):
        if int(gt[gi].X) >= 1:
            g, i = gi
            gout[g].append(i)
    results = set()
    for g, t in gout.items():
        for i in range(len(t)-1):
            for j in range(i+1, len(t)):
                results.add((t[i], t[j], g))
                if scale[g] == 2:  # home-and-home
                    results.add((t[j], t[i], g))

    print(sorted(results))                   
    return sorted(results)

# def get_weights(division):
#     costs = division['costs']
#     teams = division['teams']
#     weights = {}
#     for t1 in teams:
#         for t2 in teams:
#             if t1 == t2:
#                 w = 100000
#             else:
#                 try:
#                     w = costs[t1['venue_id']][t2['venue_id']]
#                 except:
#                     print(repr(t1['venue_id']))
#                     print(repr(t2['venue_id']))
#                     print(costs)
#                     raise
#             weights[t1['flt_pos'], t2['flt_pos']] = w
#     return weights

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
    groups = [6, 6, 6, 5]
    label = '-'.join(map(str,groups))
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
    results = pairings(team_codes.keys(), weights, groups)

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

