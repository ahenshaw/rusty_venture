#! /usr/bin/python3
import numpy
import datetime
import re
import json
from collections import defaultdict
from argparse import ArgumentParser

from modules.team_report import get_teams
from modules.database import get_db
from modules.calendar_tools import get_season_info

# SEASON_END = '2020-05-17'
# BLACKOUTS  = []
TEMPLATE     = open('static/grid_template.html').read()

class Game:
    def __init__(self, date, time, field, _, division, home, visitor, home_code, visitor_code):
        self.__dict__.update({'date':date, 'time':time, 
                              'field':field, 'division':division, 
                              'home':home,'visitor':visitor, 
                              'home_code':home_code,'visitor_code':visitor_code})
    
    def __str__(self):
        return str(self.__dict__)

def iso_year_start(iso_year):
    "The gregorian calendar date of the first day of the given ISO year"
    fourth_jan = datetime.date(iso_year, 1, 4)
    delta = datetime.timedelta(fourth_jan.isoweekday()-1)
    return fourth_jan - delta 

def iso_to_gregorian(iso_year, iso_week, iso_day):
    "Gregorian calendar date for the given ISO year, week and day"
    year_start = iso_year_start(iso_year)
    return year_start + datetime.timedelta(days=iso_day-1, weeks=iso_week-1)

def daterange(start_date, end_date):
    for n in range((end_date - start_date).days+1):
        yield start_date + datetime.timedelta(n)

def getDates(dates, end_date):
    '''given a set of dates (as string in format yyyy-mm-dd), 
       this will create a new set that bounds the old set and 
       includes any days of the week found in the old set'''
    days = set([7])
    expanded_dates = set()
    
    if end_date:
        # year, month, day = [int(x) for x in end_date.split('-')]
        # date = datetime.date(year, month, day)
        expanded_dates.add(end_date.isocalendar())
        
    for date in dates:
        days.add(date.isoweekday())
        expanded_dates.add(date.isocalendar())
    expanded_dates = sorted(list(expanded_dates))  
    first_year, first_week, _ = expanded_dates[0]
    last_year,  last_week,  _ = expanded_dates[-1]
    start  = iso_to_gregorian(first_year, first_week, 1)
    finish = iso_to_gregorian(last_year,  last_week,  7)
    print('start', start, first_year, first_week)
    print('finish', finish, last_year, last_week)
    new_days = []
    for date in daterange(start, finish):
        year, week, day = date.isocalendar()
        if day in days:
            new_days.append(date)
    return new_days
        
def formatGrid(table_class, teamlist, days, teams, global_blackouts):
    home_black, away_black, comments, names = getTeamInfo(teams)
    html = []
    html.append('<table class="%s"><tr><th><div style="width:20em">Team</div></th>' % table_class)
    all_black = set()
    for date in global_blackouts:
        all_black.add(date)
        
    for day in days:
        y, w, d = day.isocalendar()
        alt = (d==6)  #w % 2
        html.append('<th class="a%d">%s</th>' % (alt, day.strftime('%a<br>%b&nbsp;%d')))
        
    html.append('<th><div style="width:40em">Comments</div></th>')
    html.append('</tr>')
    
    teamlist = sorted([(names[x], x) for x in teamlist])

    for name, team in teamlist:
        print(name, team)
        html.append('''<tr class="data">
                       <th id="%s:" 
                           class="rh" 
                           title="%s">%s</th>''' % (team, names[team], '<span style="float:left">%s</span> <span style="float:right">%s</span>' % (name, team)))
        for day in days:
            y, w, d = day.isocalendar()
            alt = (d==6)  # w%2
            key = (team,day)
            if day in all_black:
                blackout = 'all_blackout' 
            elif (key in home_black) and (key in away_black):
                blackout = 'blackout' 
            elif key in home_black:
                blackout = 'home_black'
            elif key in away_black:
                blackout = 'away_black'
            else:
                blackout = ''
            cell_id = '%s:%s' % (team, day)
            html.append('''<td onclick="select(this)"
                               id="%s" 
                               class="a%d %s">&nbsp;</td>''' % (cell_id, alt, blackout))
        html.append('<td class="comment">%s</td>' % (comments[team] or '&nbsp;'))
        html.append('</tr>')
    html.append('</table>')
    return '\n'.join(html)
    
def makeGrid(games, teams, end_date, global_blackouts):
    json_games = []
    home_count = defaultdict(list)
    away_count = defaultdict(list)
        
    teamlist = [x.flt_pos for x in teams]
    # teamlist = [str(x.id) for x in teams]
    dates = set()
    for gamedate, gametime, home, away in games:
        json_games.append({'date':gamedate, 'home':home, 'away':away})
        dates.add(gamedate)
    # jsfile.write('var games = %s' % json.dumps(json_games))

    teamlist = dict([(x,i) for (i, x) in enumerate(teamlist)])
    print(teamlist)
    
    # create list of dates that might be used for game days 
    # (includes some days that may not be used)
    all_dates = getDates(dates, end_date)
    dates = dict([(x,i) for (i, x) in enumerate(sorted(all_dates))])
    data = numpy.zeros((len(teams), len(all_dates)), dtype=int)

    for gamedate, gametime, home, away in games:
        home = teamlist[home]
        visitor = teamlist[away]
        date_index = dates[gamedate]
        if data[home][date_index]: 
            print('**** CONFLICT **** home', home, date_index)
        if data[visitor][date_index]:
            print('**** CONFLICT **** visitor', visitor, date_index)
        data[home][date_index] = (visitor+1)
        data[visitor][date_index] = -(home+1)
    #filename = '<div id="datafile">%s</div>\n' % os.path.basename(fn)
    #~ return filename + formatGridNew('gamegrid', sorted(teamlist), all_dates, teams)                
    return formatGrid('gamegrid', teamlist, all_dates, teams, global_blackouts)                

def getTeamInfo(teams):
    home_black = set()
    away_black = set()
    comments  = {}
    names     = {}
    for team in teams:
        comments[team.flt_pos] = team.comment
        names[team.flt_pos]    = team.name
        for hb in team.black_home:
            home_black.add((team.flt_pos, hb))
        for ab in team.black_away:
            away_black.add((team.flt_pos, ab))
    return home_black, away_black, comments, names

def get_games(db, division, teams):
    lookup = {str(t.id): t.flt_pos for t in teams}
    cursor = db.cursor()
    cursor.execute('''
        SELECT gamedate, gametime, home, away
        FROM game
        WHERE agegroup=%s''', (division,))
    result = []
    # for gamedate, gametime, home, away in cursor.fetchall():
    #     h = lookup[home]
    #     a = lookup[away]
    #     result.append((gamedate, gametime, h, a))
    # return result
    return cursor.fetchall()

def get_params():
    parser = ArgumentParser()
    parser.add_argument('division', help='Team agegroup or division')
    parser.add_argument('season')
    params = parser.parse_args()
    return params

if __name__ == '__main__':
    # import sys
    # sys.argv.append('B16R')
    args = get_params()
    db   = get_db()
    start_date, end_date, global_blackouts = get_season_info(db, args.season)
    output    = '../output/%s.html' % args.division

    teams = sorted(get_teams(db, args.division))
    # for team in teams:
    #     print(team.flt_pos, team.name)
    games = get_games(db, args.division, teams)
    out = open(output, 'w')
    out.write(TEMPLATE % (args.division, makeGrid(games, teams, end_date, global_blackouts)))
    