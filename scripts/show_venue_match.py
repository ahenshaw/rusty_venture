from argparse import ArgumentParser
import pymysql
import sys
from modules.database import get_db
from modules.team_report import get_teams, get_costs, get_venues

def show_venues(db, division, fix=False):
    cursor = db.cursor()
    cursor.execute('''SELECT name, id FROM venue''')
    venues = dict(cursor.fetchall())
    cursor.execute('''SELECT label, id FROM alias''')
    aliases = dict(cursor.fetchall())
    cursor.execute('''
        SELECT team.name, coalesce(declaredvenue, '--'), coalesce(team.venue, '--'), venue.name, flt_pos
        FROM team
        LEFT JOIN venue ON venue.id = venue_id 
        LEFT JOIN division ON division.id = division_id
        WHERE division.label=%s
        ORDER BY team.name''', (division,))
    to_add = []
    for i, (team_name, declared, venue, venue_name, flt_pos) in enumerate(cursor.fetchall()):
        okay = declared in aliases or declared in venues
        flag = ' ' if okay else '*'
        print(f'{i+1:2}. {flt_pos:>3}. {team_name[:40]:40} {flag} {declared:32}  {venue_name}')
        if fix and declared not in venues:
            if declared not in aliases:
                alias_id = int(input('Alias venue id? '))
                if alias_id == -1:
                    break
                aliases[declared] = alias_id
                to_add.append((declared, alias_id))
    if to_add:
        cursor.executemany('INSERT INTO alias set label=%s, venue_id=%s', to_add)
        db.commit()

    
def get_params():
    parser = ArgumentParser()
    parser.add_argument('division', help='Team agegroup or division')
    parser.add_argument('--fix', action='store_true')
    params = parser.parse_args()

    return params

if __name__ == "__main__":
    args = get_params()
    db = get_db()
    show_venues(db, args.division, args.fix)
