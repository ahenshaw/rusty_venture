# Standard library
import sys
from argparse import ArgumentParser

# Third-party libraries
import pymysql

# Custom modules
from modules.database import get_db
from modules.team_report import get_venues, get_teams

def get_all_venues():
    db = get_db()
    cursor = db.cursor()

    cursor.execute('SELECT id, name FROM venue ORDER BY name')
    return cursor.fetchall()
        
def get_params():
    parser = ArgumentParser()
    parser.add_argument('--check', action='store')
    parser.add_argument('--show', action='store_true')
    parser.add_argument('-c', action='store')
    parser.add_argument('-v', action='store', type=int)
    params = parser.parse_args()

    return params

if __name__ == '__main__':
    db = get_db()
    args = get_params()
    if args.check:
        teams = get_teams(db, args.check)
        venues = get_venues(db, teams)
        if not venues:
            if args.show:
                for vid, name in get_all_venues():
                    print(f'{vid:3} {name}')
            print('Assign a venue to the missing club')
    if args.c:
        if not args.v:
            print('Provide a venue ID to be assigned to the club')
        else:
            cursor = db.cursor()
            c_id = cursor.execute('INSERT INTO club SET name=%s', args.c)
            cursor.execute('INSERT INTO club_venue SET club_id=%s, venue_id=%s', (cursor.lastrowid, args.v))
            db.commit()
