import sys
from collections import defaultdict
from argparse import ArgumentParser

# third-party 
from gurobipy import *
import arrow

# custom modules
from modules.database    import get_db
from modules.team_report import get_teams

class Blackouts:
    def __init__(self, defaults=None):
        self.all = set()
        self.home   = defaultdict(set)
        self.away   = defaultdict(set)
        if defaults:
            self.all |= set(defaults)

    def is_away_blackout(self, team, day):
        return (day in self.all) or (day in self.away[team])

    def is_home_blackout(self, team, day):
        return (day in self.all) or (day in self.home[team])
    
    def is_blackout(self, team, day, h, a):
        return (h == team and self.is_home_blackout(team, day)) or (a == team and self.is_away_blackout(team, day))

    def set_away(self, team, dates):
        self.away[team] |= set(dates)

    def set_home(self, team, dates):
        self.home[team] |= set(dates)

def weekends(weights):
    days = sorted(weights)
    for i in range(0, len(days),2):
        yield (days[i:i+2])

def balance(games, weights, blackouts, rounds, num_requested):
    # games:     original list of games by round. Only need the home/away columns
    # weights:   penalty weights for different days in the season
    # blackouts: object that tells whether a day is a blackout for a team
    # rounds:    dict mapping days to weekend number
    # num_requested: number of games requested (for each teams). Nominally 10
    # create some structures to track games and teams
    my_games = defaultdict(list)  # list of games for each team
    game_ids = {}                 # game_ids with storage of original home and away teams
    x = {}                        # model variables with bool value for each team, game_id, and possible date slot
    z = {}                        # per team scoring for goodness of schedule
    
    # for d1, d2 in weekends(weights):
    #     print(d1, d2)
    # import sys
    # sys.exit()

    doubles = set()
    reverse = {}
    for h, a in games:
        gid = len(game_ids)
        game_ids[gid] = (h,a)
        if (a, h) in reverse:
            doubles.add((gid, reverse[a,h]))
        reverse[h,a]  = gid
        my_games[h].append(gid)  # this team plays in this game
        my_games[a].append(gid)  # so does this team

    print('doubles:', doubles)
    m = Model()
    m.setParam('TimeLimit', 60)

    # Initialize the x variables in the model
    for team, game_list in my_games.items():
        for gid in game_list:
            for d in weights:
                x[team, gid, d] = m.addVar(0, 1, 0, GRB.BINARY, '%s_%s_%s'% (team, gid, d.format('MMDD')))

    # Initialize the z variables in the model
    largest_weight = max(weights.values())
    for team in my_games:
        num_games = len(my_games[team])
        z[team] = m.addVar(0, num_games*largest_weight, 0, GRB.INTEGER, 'z[%s]' % team)

    m.update()

    ######## CONSTRAINTS #########

    # Each game must be played on same day by h and a
    for gid, (h,a) in game_ids.items():
        for d in weights:
            expr = LinExpr()
            expr.addTerms( 1, x[h, gid, d])
            expr.addTerms(-1, x[a, gid, d])
            m.addConstr(expr, GRB.EQUAL, 0)

    # For each team, compute sum of game day weights times 1 (game) or 0 (no game) or mark blackouts
    for team, game_list in my_games.items():
        expr = LinExpr()
        for game in game_list:
            h, a = game_ids[game]
            for d, value in weights.items():
                if blackouts.is_blackout(team, d, h, a):
                #if (h == team and blackouts.is_home_blackout(team, d)) or (a == team and blackouts.is_away_blackout(team, d)):
                    value = 100  # override normal weight value
                expr.addTerms(value, x[team, game, d, ])
        expr.addTerms(-1, z[team])
        m.addConstr(expr, GRB.LESS_EQUAL, 0)

    # For each team, try to eliminate open weekends for num_requested-1 weekends
    for team, game_list in my_games.items():
        for d1, d2 in list(weekends(sorted(weights)))[:(num_requested-1)]:
                possibles = []
                for game in game_list:
                    h, a = game_ids[game]
                    if not blackouts.is_blackout(team, d1, h, a):
                        possibles.append((d1, game))
                    if not blackouts.is_blackout(team, d2, h, a):
                        possibles.append((d2, game))
                expr = LinExpr()
                for d, game in possibles:
                    expr.addTerms(value, x[team, game, d])
                if possibles:
                    m.addConstr(expr, GRB.GREATER_EQUAL, 1)

    # For each team, the game count must equal the number of games to be played
    for team, game_list in my_games.items():
        count = LinExpr()
        for game in game_list:
            for d, value in weights.items():
                count.addTerms(1, x[team, game, d])
        m.addConstr(count, GRB.EQUAL, len(game_list))

    # Each team can only play one game a day
    for team, game_list in my_games.items():
        for d in weights:
            expr = LinExpr()
            for game in game_list:
                expr.addTerms(1, x[team, game, d])
            m.addConstr(expr, GRB.LESS_EQUAL, 1)

    # All games must be scheduled for one day only
    for gid, (h,a) in game_ids.items():
        expr = LinExpr()
        for d in weights:
            # only need to use the home team for this 
            expr.addTerms(1, x[h, gid, d])
        m.addConstr(expr, GRB.EQUAL, 1, 'onedayonly%d' % gid)

    # Games against same opponent must be separated by at least three weekends
    for gid1, gid2 in doubles:
        h, a = game_ids[gid1]
        for d1 in weights:
            for d2 in weights:
                if d1 != d2:
                    r1 = rounds[d1]
                    r2 = rounds[d2]
                    if abs(r1 - r2) < 3:
                        expr = LinExpr()
                        expr.addTerms(1, x[h, gid1, d1])
                        expr.addTerms(1, x[h, gid2, d2])
                        m.addConstr(expr, GRB.LESS_EQUAL, 1)

    final = quicksum([z[team] for team in my_games])
    m.setObjective(final)
    m.update()
    m.write('step3.lp')
    m.optimize()

    results = []
    recorded = set()
    for x_key in sorted(x):
        if int(x[x_key].X) >= 0.5:
            team, game, date = x_key
            if game not in recorded:
                h, a = game_ids[game]
                results.append((date, h, a))
                recorded.add(game)
    return results

def get_params():
    parser = ArgumentParser()
    parser.add_argument('division', help='Team agegroup or division')
    parser.add_argument('label', nargs='?', default='Default')
    parser.add_argument('--blackout', default=[])
    parser.add_argument('--start', default='2020-03-01')
    parser.add_argument('--end', default='2020-06-01')
    parser.add_argument('-r', '--rounds', type=int, default=10)
    parser.add_argument('-t', '--timeout', type=int, default=30, help='Timeout for solver')
    params = parser.parse_args()
    return params

def get_games(db, division, label):
    #games = [tuple(map(str.strip,game.split('\t'))) for game in open('season/%s.balanced' % args.division)]
    cursor = db.cursor()
    cursor.execute('''
        SELECT home, away FROM pairing
        LEFT JOIN division on division.id=division_id
        WHERE division.label=%s
        AND   pairing.label=%s
    ''', (division, label))
    return cursor.fetchall()


db = get_db()
args = get_params()
teams = sorted(get_teams(db, args.division))
blackouts = Blackouts([arrow.get(x) for x in args.blackout])
for team in teams:
    blackouts.set_away(team.flt_pos, [arrow.get(x) for x in team.black_away])
    blackouts.set_home(team.flt_pos, [arrow.get(x) for x in team.black_home])

print('\n\n\n========= start blackouts ============')
print(blackouts.home)
print('========= end blackouts ============')

start = arrow.get(args.start)
end   = arrow.get(args.end)

weights   = {}
rounds = {}
for i, saturday in enumerate(arrow.Arrow.range('week', start, end)):
    sunday = saturday.shift(days=1)
    rounds[saturday]  = i
    rounds[sunday]    = i
    weights[saturday] = 1 if i < args.rounds else 20
    if i < args.rounds // 2:
        weights[sunday]   = 5 
    elif i < args.rounds:
        weights[sunday]   = 10 
    else: 
        weights[sunday]   = 25


# games = [tuple(map(str.strip,game.split('\t'))) for game in open('season/%s.balanced' % args.division)]
games = get_games(db, args.division, args.label)
print('Number of games:', len(games))
num_requested = args.rounds
results = balance(games, weights, blackouts, rounds, num_requested)

# fh = open('%s.csv'%args.division, 'w')
# fh.write('GameNum,Date,Time,FieldID,HomeTeam,AwayTeam,RoundTypeCode\n')
records = []
for d, h, a in sorted(results):
    # fh.write('0,{},00:00,0,{},{},B\n'.format(d.format('MM/DD/YYYY'), h, a))
    records.append((args.division, d.format('YYYY-MM-DD'), h, a, '00:00:00'))
print(f'Writing {len(records)} records into database')
cursor = db.cursor()
cursor.executemany('INSERT INTO game SET agegroup=%s, gamedate=%s, home=%s, away=%s, gametime=%s', records)
db.commit()
