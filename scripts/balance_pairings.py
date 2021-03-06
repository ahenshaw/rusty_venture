import sys
from argparse import ArgumentParser
from gurobipy import *
from collections import defaultdict
from itertools import groupby

from modules.database import get_db

def balance(pairings, t, results = None, time_limit=300):
    
    LARGE_UPPER_BOUND = 1000 if results is None else 10000 # to-do: compute an actual upper bound from data

    m = Model()
    m.setParam('TimeLimit', time_limit)

    x = {}
    for i in pairings:
        for j in pairings[i]:
            x[i, j] = m.addVar(0, 1, 0, GRB.BINARY, 'x[%d,%d]'%(i, j))

    z = {}
    for i in pairings:
        z[i] = m.addVar(0, LARGE_UPPER_BOUND, 0, GRB.INTEGER, 'z[%d]' % i)

    if results is None:
        w = m.addVar(0, GRB.INFINITY, 1, GRB.INTEGER, 'w')

    m.update()
    if results is not None:
        for i in pairings:
            for j in pairings[i]:
                x[i,j].start = (i, j) in results


    # for each pairing (i,j)
    # if x[i,j] is a home game, then x[j,i] is an away game
    # x[i,j] + x[j,i] = 1
    for i in pairings:
        for j in pairings[i]:
            expr = LinExpr()
            expr.addTerms(1, x[i,j])
            expr.addTerms(1, x[j,i])
            m.addConstr(expr, GRB.EQUAL, 1)

    # for each team i
    # -1 <= x[i,j] - x[j,i] <= 1
    # or, abs(num_home - num_away) <= 1
    for i in pairings:
        diff = LinExpr()
        for j in pairings[i]:
            diff.addTerms(1, x[i,j])
            diff.addTerms(-1, x[j,i])
        m.addConstr(diff, GRB.LESS_EQUAL, 1)
        m.addConstr(diff, GRB.GREATER_EQUAL, -1)

    # for each team i and opponent j
    # t[i,j]*x[i,j] - t[j,i]*x[j,i] <= z[i]
    for i in pairings:
        expr = LinExpr()
        for j in pairings[i]:
            expr.addTerms( t[i,j], x[i,j])
            expr.addTerms(-t[j,i], x[j,i])
        expr.addTerms(-1, z[i])
        m.addConstr(expr, GRB.LESS_EQUAL,0)

    # for each team i and opponent j
    # -t[i,j]*x[i,j] + t[j,i]*x[j,i] <= z[i]
    for i in pairings:
        expr = LinExpr()
        for j in pairings[i]:
            expr.addTerms(-t[i,j], x[i,j])
            expr.addTerms( t[j,i], x[j,i])
        expr.addTerms(-1, z[i])
        m.addConstr(expr, GRB.LESS_EQUAL, 0)

    if results is None:
        print('first objective')
        # for each team i
        w >= z[i]
        for i in pairings:
            m.addConstr(w - z[i]>=0)

    if results is not None:
        print('second objective')
        m.setObjective(quicksum([z[i] for i in pairings]))        
    m.update()
    m.write('step2.lp')
    m.optimize()
    results = set()
    out = open('temp.out', 'w')
    for xv in sorted(x):
        out.write('{}: {}\n'.format(xv, x[xv].X))
        if int(x[xv].X) > 0.5:
            results.add(xv)
    return results


def get_pairings(db, division_id):
    cursor = db.cursor()
    cursor.execute('''SELECT pairing.label, round, home, away, cost
                      FROM pairing 
                      WHERE division_id=%s
                      ORDER BY pairing.label''', (division_id))
    results = []
    for k, v in groupby(cursor.fetchall(), key=lambda x:x[0]):
        results.append((k, [x[1:] for x in v]))
    return dict(results)

def extract(original):
    times   = {}
    mapping = {}
    pairings = defaultdict(list)
    paired = set()
    for _, home, away, time in original:
        if home not in mapping:
            mapping[home] = len(mapping)

        if away not in mapping:
            mapping[away] = len(mapping)

        h = mapping[home]
        a = mapping[away]
        if (h,a) not in paired and (a,h) not in paired:
            pairings[h].append(a)
            pairings[a].append(h)
            paired.add((h,a))
            paired.add((a,h))
        else:
            print(h, a, pairings)
            pairings[h].remove(a)
            pairings[a].remove(h)
        times[h,a] = times[a,h] = int(time)
         
    return pairings, times, mapping

def get_params():
    parser = ArgumentParser()
    parser.add_argument('division', help='Team agegroup or division')
    parser.add_argument('label', nargs='?', default='Default')
    parser.add_argument('-t', '--timeout', type=int, default=300, help='Timeout for solver')
    params = parser.parse_args()
    return params

if __name__ == '__main__':
    db = get_db()
    params = get_params()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM division where label=%s', params.division)
    division_id, = cursor.fetchone()

    try:
        original = get_pairings(db, division_id)[params.label]
    except KeyError:
        print(f'No pairings for division "{params.division}" with label "{params.label}"')
        sys.exit()
    pairings, times, mapping = extract(original)

    inv_map = dict([(x,y) for (y,x) in mapping.items()])
    for key, value in mapping.items():
        print(key, [inv_map[x] for x in pairings[value]])
    print(mapping)
    print('Number of teams: {}'.format(len(pairings)))
    results = balance(pairings, times, time_limit=params.timeout)

    results = balance(pairings, times, results, time_limit=params.timeout)

    played_earlier = set()
    schedule = defaultdict(list)
    pairings = []
    for r, home, away, time in original:
        h = mapping[home]
        v = mapping[away]

        # pairing eliminated due to home-and-home
        if (h, v) not in results and (v, h) not in results:
            t1, t2 = sorted([home, away])
            if (t1, t2) not in played_earlier:
                played_earlier.add((t1, t2))
                home, away = t1, t2
            else:
                home, away = t2, t1
        else:
            # if not in results as (h,v) then it is as (v,h), so swap home and away
            if (h, v) not in results:
                home, away = away, home
        pairings.append((division_id, params.label, r, home, away, time))
        schedule[home].append(str(away)+' ')
        schedule[away].append(str(home)+'*')

    if pairings:
        cursor.execute('''DELETE FROM pairing 
                          WHERE division_id=%s 
                          AND label=%s''', (division_id, params.label))
        cursor.executemany('INSERT INTO pairing (division_id, label, round, home, away, cost) VALUES (%s, %s, %s, %s, %s, %s)', pairings)
        db.commit()
    # # print schedule (* means away match)
    # for t in sorted(schedule, key=lambda x: int(x[1:])):
    #     print('{:3s}: '.format(t), end='')
    #     for o in schedule[t]:
    #         print('{:4s}'.format(o), end=' ')
    #     print()
