import sys
from modules.database import get_db
from argparse import ArgumentParser

def pretty(minutes):
    hr, minutes = divmod(minutes, 60)
    return f'{hr}:{minutes:02d}'

sys.argv.append('B12X')

parser = ArgumentParser()
parser.add_argument("division")
args = parser.parse_args()

db = get_db()
cursor = db.cursor()
cursor.execute('''
    SELECT pairing.label, min(cost), max(cost), floor(avg(cost))
    FROM pairing
    LEFT JOIN division ON division.id=division_id
    WHERE division.label = %s
    GROUP BY pairing.label
''', args.division
)

print('{:10}\t{:5}\t{:5}\t{:5}'.format('Partition', 'Min', 'Max', 'Average'))
for row in cursor.fetchall():
    pp = list(map(pretty, row[1:]))
    print(f'{row[0]:10}\t{pp[0]}\t{pp[1]}\t{pp[2]}')