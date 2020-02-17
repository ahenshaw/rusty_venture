import sys
from modules.database import get_db
from argparse import ArgumentParser
from itertools import product
import pymysql


def get_weights(db, division):
    dcursor = db.cursor(pymysql.cursors.DictCursor)
    dcursor.execute('''
        SELECT team.id, team.venue_id
        FROM team
        LEFT JOIN division ON division.id=division_id
        WHERE division.label = %s
    ''', args.division
    )
    teams = dcursor.fetchall()

    cursor = db.cursor()
    cursor.execute('SELECT home_id, away_id, cost FROM venue_venue')
    costs = dict((((h, a), cost) for (h, a, cost) in cursor.fetchall()))
    weights = {}
    for t1 in teams:
        for t2 in teams:
            if t1 == t2:
                w = 100000
            else:
                w = costs[t1['venue_id'],t2['venue_id']]
            weights[t1['id'], t2['id']] = w
    return weights


sys.argv.append('B12X')

parser = ArgumentParser()
parser.add_argument("division")
args = parser.parse_args()
groups = [[
    (51, 'CFA Calhoun Elite'),
    (52, 'CFA Dalton Elite'),
    (53, 'CFA Rome Elite'),
    (58, 'Georgia Storm 08B Select'),
    (62, 'MAYS Striker 08B Blue'),
    (68, 'TRAC Dalton Red Wolves 08 Elite'),],
    [
    (56, 'GA Alliance FC  2008 Boys'),
    (57, 'GA Rush B2008'),
    (60, 'IAFC 08 Boys Elite'),
    (61, 'MAYS Buckhead 08B Blue - B12U'),
    (63, 'MOBA-08 Boys'),
    (66, "Roswell Santos Blue '08 Academy"),],
    [
    (49, 'Atlanta Fire United South 08B Elite'),
    (54, 'CFC Red Star - B12U Elite'),
    (59, 'Hinesville Soccer Association - BR12U'),
    (64, 'MSC 2008 Boys Elite'),
    (65, 'Old Capitol S - B12U- 9v9'),
    (67, 'Savannah United 08B Premier'),],
    [
    (47, 'All-In Futbol Club - Sugar Hill 08'),
    (48, 'ATHENS UNITED 08 BOYS'),
    (50, 'BPSC 08 Real FA - Elite'),
    (55, 'DDYSC Wolves 08 Elite'),
    (69, 'Triumph 08 Boys'),]
]
LABEL = '6-6-6-5B'
db = get_db()
cursor = db.cursor()
cursor.execute('SELECT id FROM division WHERE division.label = %s', args.division)
division_id, = cursor.fetchone()
weights = get_weights(db, args.division)

records = []
for group in groups:
    for pair in product(group, group):
        if pair[0] != pair[1]:
            h, a = pair[0][0], pair[1][0]
            records.append((division_id, LABEL, h, a, weights[h,a]))
cursor.executemany('''
    INSERT INTO pairing 
    (division_id, label, home, away, cost)
    VALUES (%s, %s, %s, %s, %s)
''', records)
db.commit()
# cursor = db.cursor()
# cursor.execute('''
#     SELECT team.id, team.name
#     FROM team
#     LEFT JOIN division ON division.id=division_id
#     WHERE division.label = %s
# ''', args.division
# )

# for row in cursor.fetchall():
#     print(f"{row},")
