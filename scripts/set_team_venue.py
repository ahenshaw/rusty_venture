# Standard library
import sys
from argparse import ArgumentParser
from itertools import product

# Third-party libraries
import pymysql
from fuzzywuzzy import fuzz

# Custom modules
from modules.database import get_db
from modules.team_report import get_venues, get_teams

def update_venue(division):
    db = get_db()
    cursor = db.cursor()

    cursor.execute('SELECT name, id FROM venue')
    venues = cursor.fetchall()
    print(venues)

    cursor.execute('''SELECT team.id, name, declaredvenue, venue 
                      FROM team 
                      LEFT JOIN division ON division.id=division_id
                      WHERE venue_id IS NULL
                      AND division.label=%s
                      ORDER BY name''', division)
    updates = []
    print('\n\n')
    for i, (tid, team_name, decl, venue) in enumerate(cursor.fetchall()):
        # choose "venue" or "declared venue", with preference to "venue"
        target = venue or decl
        scores = []
        if target:
            for venue_name, venue_id in venues:
                scores.append((fuzz.partial_ratio(target, venue_name), venue_id, venue_name))
        scores.sort(reverse=True)
        if scores and scores[0][0] > 90:
            updates.append((tid, scores[0][1]))
            print(f'{i+1:2}. Matched "{team_name}" using "{target}" with "{scores[0][2]}"\n')
        elif target is None:
            print(f'{i+1:2}. Error: No declared venue for "{team_name}"')
        else:
            print(f'{i+1:2}. Error: No good matches for "{team_name}" using "{target}"')
            print('    Best matches are:')
            for best in scores[:3]:
                print('       ', best[2])

def update_teams(db, teams):
    records = []
    for team in teams:
        records.append((team.venue_id, team.id))
    cursor = db.cursor()
    cursor.executemany('UPDATE team SET team.venue_id=%s WHERE team.id=%s', records)
    db.commit()
    print(f'Updated {len(teams)} records')

def get_params():
    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('division', help='Team agegroup or division')
    params = parser.parse_args()

    return params

if __name__ == '__main__':
    db = get_db()
    args = get_params()
    teams = get_teams(db, args.division)
    get_venues(db, teams)
    update_teams(db, teams)

    # update_venue(args.division)