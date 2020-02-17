from argparse import ArgumentParser
import pymysql
import sys
from modules.database import get_db
from modules.team_report import get_teams, truncate

def show_comments(db, division):
    for team in get_teams(db, division):
        if team.comment:
            comment = team.comment.replace('\n', '\n'+' '*56)
            clubname = truncate(team.clubname, 30)
            name = truncate(team.name, 20)
            print(f'{team.flt_pos:>3} {clubname:30} {name:20} {comment}')
    
def get_params():
    parser = ArgumentParser()
    parser.add_argument('division', help='Team agegroup or division')
    params = parser.parse_args()

    return params

if __name__ == "__main__":
    args = get_params()
    db = get_db()
    print("\x1B[H\x1B[J", end='')
    print('Division:', args.division)
    show_comments(db, args.division)
