import sys
from modules.database import get_db
from argparse import ArgumentParser
from itertools import product
import pymysql

division = 'B13IIW'
division = 'B12X'
LABEL = 'Default'

db = get_db()
cursor = db.cursor()
cursor.execute('''
    SELECT team.id, division.id FROM team
    LEFT JOIN division on division.id=division_id
    WHERE label=%s
''', division)
group = cursor.fetchall()

records = []
for pair in product(group, group):
    if pair[0] != pair[1]:
        h, a = pair[0][0], pair[1][0]
        division_id = pair[0][1]
        # records.append((division_id, LABEL, h, a, weights[h,a]))
        records.append((division_id, LABEL, h, a, 0))
        if len(group) < 7:
            # generate second half of home-and-home
            records.append((division_id, LABEL, a, h, 0))

for record in records:
    print(record)

cursor.executemany('''
    INSERT INTO pairing 
    (division_id, label, home, away, cost)
    VALUES (%s, %s, %s, %s, %s)
''', records)
db.commit()
