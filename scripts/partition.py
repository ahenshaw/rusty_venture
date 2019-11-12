''' 
Replaces make_pairings_xp
To-do:  
    * Handle outliers
'''

import sys
import json
from itertools import product
from collections import Counter
from argparse import ArgumentParser

# third-party 
from gurobipy import *

# custom modules
from modules.team_report import get_teams_from_json

OPTIMIZE_TIME = 180 # seconds

def pairings(teams, weights, groups):
    LARGE_UPPER_BOUND = 200  # to-do: compute an actual upper bound from data

    m = Model()
    # m.setParam('OutputFlag', 0)
    m.setParam('TimeLimit', OPTIMIZE_TIME)

    x = {}
    for i in teams:
        for j in teams:
            if i != j:
                for g in range(len(groups)):
                    x[i, j, g] = m.addVar(0, 1, 0, GRB.BINARY, 'x[%s,%s,%s]'% (i, j, g))
    gt = {}
    for g in range(len(groups)):
        for i in teams:
            gt[g, i] = m.addVar(0, 1, 0, GRB.BINARY, 'gt[%s,%s]'% (g, i))

    m.update()

    # create a multiplier for weighting.  If home-and-home, then multiplier
    # is 2, otherwise 1
    scale = [(2 if x < 8 else 1) for x in groups]
    ### constraints ###

    # for each group, each team must play number of games 
    # equal to 'rounds' for that group
    for g in range(len(groups)):
        doubled_games = groups[g]*(groups[g]-1)
        expr = LinExpr()
        for i in teams:
            for j in teams:
                if i != j:
                    expr.addTerms(1, x[i, j, g])
        m.addConstr(expr, GRB.EQUAL, doubled_games)

    # each game with teams (i, j) must also be played by teams (j,i) in group g
    for i in teams:
        for j in teams:
            if i != j:
                for g in range(len(groups)):
                    expr = LinExpr()
                    expr.addTerms( 1, x[i, j, g])
                    expr.addTerms(-1, x[j, i, g])
                    m.addConstr(expr, GRB.EQUAL, 0)

    # each team i must belong to only one group
    for i in teams:
        expr = LinExpr()
        for g in range(len(groups)):
            expr.addTerms( 1, gt[g, i])
        m.addConstr(expr, GRB.EQUAL, 1)

    # link gt and x
    # x_ijg >= g_li + g_lj - 1

    for i in teams:
        for j in teams:
            if i != j:
                for g in range(len(groups)):
                    expr = LinExpr()
                    expr.addTerms( -1, x[i, j, g])
                    expr.addTerms( 1, gt[g, i])
                    expr.addTerms( 1, gt[g, j])
                    m.addConstr(1, GRB.GREATER_EQUAL, expr)

                    m.addConstr(gt[g, i], GRB.GREATER_EQUAL, x[i, j, g])
                    m.addConstr(gt[g, j], GRB.GREATER_EQUAL, x[i, j, g])


    # each team i can play j at most once
    for i in teams:
        for j in teams:
            expr = LinExpr()
            if i != j:
                for g in range(len(groups)):
                    expr.addTerms( 1, x[i, j, g])
            m.addConstr(expr, GRB.LESS_EQUAL, 1)

    final = quicksum([weights[i,j]*x[i,j,g]*scale[g] for (i,j,g) in x])
    m.setObjective(final)
    m.update()
    # m.write('step1.lp')
    m.optimize()

    results = set()
    for xvd in sorted(x):
        if int(x[xvd].X) >= 1:
            i, j, g = xvd
            if (j, i, g) not in results:
                results.add((i, j, g))
                if scale[g] == 2:
                    results.add((j, i, g))

    print(sorted(results))                   
    return sorted(results)

def get_weights(division):
    costs = division['costs']
    teams = division['teams']
    weights = {}
    for t1 in teams:
        for t2 in teams:
            if t1 == t2:
                w = 100000
            else:
                w = costs[t1['venue_id']][t2['venue_id']]
            weights[t1['flt_pos'], t2['flt_pos']] = w
    return weights

def get_params():
    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('division', help='Team agegroup or division')
    params = parser.parse_args()

    return params

if __name__ == '__main__':
    sys.argv.append('/repos/soccer_ng/season/B12C')
    groups = [6,6,6,11]
    params = get_params()
    
    filename = "{}.json".format(params.division)
    with open(filename) as fh:
        division = json.load(fh)

    teams = division['teams']
    weights = get_weights(division)

    team_codes = dict([(x['flt_pos'], x) for x in teams])
    results = pairings(team_codes.keys(), weights, groups)


    round_count = Counter()
    pairings = []
    for i, j, g in results:
        print(g, i, j)
        team_codes[i]['group'] = g
        team_codes[j]['group'] = g
        r = max(round_count[i], round_count[j])
        pairings.append((r, i, j, weights[i,j]))
        round_count[i] += 1
        round_count[j] += 1

    division['pairings'] = pairings
    with open(filename, 'w') as fh:
        json.dump(division, fh, indent=4)
    print('{} teams'.format(len(teams)))
    print('{} pairings added or replaced in data'.format(len(pairings)))
