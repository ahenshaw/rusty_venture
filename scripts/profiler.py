from argparse import ArgumentParser
import pandas as pd
import pymysql
import sys
from modules.database import get_db
from modules.team_report import get_teams, get_costs, get_venues

CUTOFF = 45
ROUNDS = 10

def do_profile(db, args):
    teams = get_teams(db, args.division)
    division_id = teams[0].division_id

    if not get_venues(db, teams):
        print("\nFix errors before proceeding\n")
        sys.exit()

    weights = get_costs(db, teams)
    nearest = {}
    rlookup = {}
    for i, t1 in enumerate(teams):
        rlookup[t1.flt_pos] = t1.id
        dist = []
        for j, t2 in enumerate(teams):
            if t1 != t2:
                dist.append((weights[(i, j)], t2.flt_pos))
        dist = list(sorted(dist))[: args.rounds]
        nearest[t1] = dist
        # print(t1.flt_pos, dist)

    stats = []
    for team in sorted(teams, key=lambda x: x.name):
        if not args.quiet:
            print(team, end=" |")
        total = 0
        for w, t in nearest[team]:
            if not args.quiet:
                print("{:3d}:{:3s}".format(w, t), end=" ")
            total += w
        avg = total / len(nearest[team])
        if not args.quiet:
            print("   ", avg)
        stats.append((team.flt_pos, avg))
    df = pd.DataFrame(stats, columns=["Team", "Travel"])
    mean = df.Travel.mean()
    stddev = df.Travel.std()
    print("\nNum teams: %d" % len(teams))
    print("Mean     : {:0.1f}".format(mean))
    print("Std Dev  : {:0.1f}".format(stddev))
    excess = df[df.Travel > max(CUTOFF, mean + stddev)].Team.tolist()
    if excess:
        print("Outlier teams:", excess)
        by_id = [(rlookup[x],) for x in excess]
        cursor = db.cursor()
        cursor.execute('UPDATE team SET outlier=0 WHERE division_id=%s', division_id)
        cursor.executemany('UPDATE team SET outlier=1 WHERE id=%s', by_id)
        db.commit()

def get_params():
    parser = ArgumentParser()
    parser.add_argument('-q', '--quiet', action='store_true')
    parser.add_argument('division', help='Team agegroup or division')
    parser.add_argument('-r', '--rounds', type=int, default=ROUNDS)
    params = parser.parse_args()

    return params

if __name__ == "__main__":
    args = get_params()
    db = get_db()
    do_profile(db, args)
