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

OPTIMIZE_TIME = 300 # seconds

MAX_REPS = 2
def pairings(teams, weights, rounds, outliers):
    LARGE_UPPER_BOUND = 200  # to-do: compute an actual upper bound from data

    m = Model()
    m.setParam('OutputFlag', 0)
    m.setParam('TimeLimit', 10)

    reps = {}
    for i in teams:
        for j in teams:
            if i != j:
                r = MAX_REPS = 2 if (i in outliers) and (j in outliers) else 1
                reps[(i,j)] = r

    x = {}
    for i in teams:
        for j in teams:
            if i != j:
                for r in range(reps[(i,j)]):
                    x[i, j, r] = m.addVar(0, 1, 0, GRB.BINARY, 'x[%s,%s,%s]'% (i, j, r))
    m.update()

    ### constraints ###

    # each team must play number of games equal to 'rounds'
    for i in teams:
        expr = LinExpr()
        for j in teams:
            if i != j:
                for r in range(reps[(i,j)]):
                    expr.addTerms(1, x[i, j, r])
        m.addConstr(expr, GRB.EQUAL, rounds)

    # each game with teams (i, j) must also be played by teams (j,i)
    for i in teams:
        for j in teams:
            if i != j:
                for r in range(reps[(i,j)]):
                    expr = LinExpr()
                    expr.addTerms( 1, x[i, j, r])
                    expr.addTerms(-1, x[j, i, r])
                    m.addConstr(expr, GRB.EQUAL, 0)

    # each team i should only play j 0 or 1 or 2 (if outliers) times
    for i in teams:
        for j in teams:
            if i != j:
                expr = LinExpr()
                for r in range(reps[(i,j)]):
                    expr.addTerms(1, x[i, j, r])
                m.addConstr(expr, GRB.LESS_EQUAL, reps[(i,j)])

    final = quicksum([weights[i,j]*x[i,j, r] for (i,j,r) in x])
    m.setObjective(final)
    m.update()
    m.write('step1.lp')
    m.optimize()

    results = set()
    for xvd in sorted(x):
        if int(x[xvd].X) >= 1:
            i, j, r = xvd
            if (j, i, r) not in results:
                results.add((i, j, r))
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
    parser.add_argument('-r', '--rounds', default=10, type=int, help='Number of Rounds')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--hh', action='store_true', help='Use home-and-home strategy')
    parser.add_argument('--outliers', help='Outlier teams (may play more games against each other)')
    parser.add_argument('division', help='Team agegroup or division')
    params = parser.parse_args()

    if params.hh and params.rounds > 6:
        print('Warning: With home-and-home flag, twice as many games will be scheduled')
    return params

if __name__ == '__main__':
    params = get_params()
    
    # if params.outliers is not None:
    #     outliers = set([int(x) for x in params.outliers.split(',')])
    # else:
    #     outliers = set()

    filename = "{}.json".format(params.division)
    with open(filename) as fh:
        division = json.load(fh)

    teams = sorted(get_teams_from_json(division))
    weights = get_weights(division)

    team_codes = [x.flt_pos for x in teams]
    if params.hh:
        outliers = set()
    else:
        outliers = set([x.flt_pos for x in teams if getattr(x,"outlier", "0") == "1"])
    results = pairings(team_codes, weights, params.rounds, outliers)
    if params.hh:
        first_half = results.copy()
        for i, j in first_half:
            results.append((j,i))

    round_count = Counter()
    pairings = []
    for i, j, repetition in results:
        r = max(round_count[i], round_count[j])
        pairings.append((r, i, j, weights[i,j]))
        round_count[i] += 1
        round_count[j] += 1

    division['pairings'] = pairings
    with open(filename, 'w') as fh:
        json.dump(division, fh, indent=4)
    print('{} teams'.format(len(teams)))
    print('{} pairings added or replaced in data'.format(len(pairings)))
