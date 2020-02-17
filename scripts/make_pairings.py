import sys
from itertools import product
from collections import Counter
from argparse import ArgumentParser

# third-party 
from gurobipy import *

# custom modules
from modules.team_report import get_teams, get_weights
from modules.database import get_db

OPTIMIZE_TIME = 300 # seconds

MAX_REPS = 2
def pairings(teams, weights, rounds, outliers, verbose):
    LARGE_UPPER_BOUND = 200  # to-do: compute an actual upper bound from data

    m = Model()
    m.setParam('OutputFlag', verbose)
    m.setParam('TimeLimit', 180)

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

    # each game with teams (i, j) must also be played by teams (j, i)
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

    final = quicksum([weights[i,j]*x[i,j,r] for (i,j,r) in x])
    m.setObjective(final)
    m.update()
    m.write('/temp/step1.lp')
    m.optimize()

    results = set()
    for xvd in sorted(x):
        if int(x[xvd].X) >= 1:
            i, j, r = xvd
            if (j, i, r) not in results:
                results.add((i, j, r))
    return sorted(results)

def get_params():
    parser = ArgumentParser()
    parser.add_argument('division', help='Team agegroup or division')
    parser.add_argument('label', nargs='?', default='Default')

    parser.add_argument('-r', '--rounds', default=10, type=int, help='Number of Rounds')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-p', '--pretend', action='store_true')

    parser.add_argument('--hh', action='store_true', help='Use home-and-home strategy')
    parser.add_argument('--all', action='store_true', help='Treat all teams as outliers (leads to lots of home-and-home pairings)')
    # parser.add_argument('--outliers', help='Outlier teams (may play more games against each other)')
    args = parser.parse_args()

    if args.hh and args.all:
        print('Warning: Unlikely to want both -all and --hh')

    if args.hh and args.rounds > 6:
        print('Warning: With home-and-home flag, twice as many games will be scheduled')
    return args

if __name__ == '__main__':
    db = get_db()
    args = get_params()

    teams = sorted(get_teams(db, args.division))
    weights = get_weights(db, teams)
    # # add penalties for extra long drives
    # for key in weights:
    #     v = weights[key]
    #     weights[key] = v*v
        
    division_id = teams[0].division_id

    team_codes = [x.id for x in teams]
    if args.all:
        # All teams treated as outlier.  This allows every pairing to possibly be home-and-home.
        outliers = set([x.id for x in teams])
    elif args.hh:
        outliers = set()
    else:
        outliers = set([x.id for x in teams if getattr(x,"outlier", 0) == 1])
    print('outliers:', outliers)
    results = pairings(team_codes, weights, args.rounds, outliers, args.verbose)
    if args.hh:
        first_half = results.copy()
        for i, j, r in first_half:
            results.append((j,i,r+args.rounds))

    round_count = Counter()
    pairings = []
    for i, j, repetition in results:
        r = max(round_count[i], round_count[j])
        pairings.append((r, i, j, weights[i,j]))
        round_count[i] += 1
        round_count[j] += 1


    # division['pairings'] = pairings
    # with open(filename, 'w') as fh:
    #     json.dump(division, fh, indent=4)
    print('{} teams'.format(len(teams)))
    if not args.pretend:
        print(f'Saving {len(pairings)} records to database')
        cursor = db.cursor()
        records = []
        for round, home, away, cost in pairings:
            records.append((division_id, args.label, home, away, cost))
        cursor.execute('DELETE FROM pairing WHERE division_id=%s AND label=%s', (division_id, args.label))
        cursor.executemany('''
            INSERT INTO pairing
            SET division_id=%s, label=%s, home=%s, away=%s, cost=%s
        ''', records)
        db.commit()
    else:
        print(f'{len(pairings)} pairings generated (not saved to database)')
