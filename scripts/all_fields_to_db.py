# standard library
import json
import sys
from collections import defaultdict

# third-party
import lxml.etree as et
import argparse

# custom modules
from modules.database import get_db

''' 
Read the Tournament All Fields Info XML file.  Delete several fields and
rename the rest.  Filter on fields (if any selected).  Filtering works
by checking if value is "in" the field.  Write to database.
'''

DROP = ("textbox50" ,"textbox51", "textbox52", "TeamManager",
        "textbox25", "textbox26", "textbox28", "textbox29", 
        "textbox30", "FourthContact", "FourthEmail", "FourthCellPhone",
        "AltTeamNumber",
       )

MAP = {'Comment'       : 'comment',
       'ClubName'      : 'clubname',
       'teamName'      : 'name',
       'textbox15'     : 'league_id',
       'textbox16'     : 'program',
       'textbox48'     : 'program2', 
       'textbox44'     : 'grp', 
       'TeamStatus'    : 'status',
       'BlackoutDates' : 'blackout',
       'textbox31'     : 'preferred_day',
       'FlightPosition': 'flt_pos',
       'textbox49'     : 'flight',
       'venue'         : 'venue',
       'responseName1' : 'declaredvenue',
       'SubmissionDate': 'submission_date'
      }

def filter_and_transform(args):
    valid = set(MAP.values())
    filters = [(k, v) for (k,v) in vars(args).items() if k in valid and v is not None]
    doc = et.parse(args.xml_in)
    teams = []
    for element in doc.findall('.//{TournamentTeamInfoAllFields}Detail'):
        attributes = element.attrib.items()
        for x in element.findall('.//{TournamentTeamInfoAllFields}fieldTitle'):
            attributes.extend(x.attrib.items())
        d = {}
        for key, value in attributes:
            if key not in DROP: 
                d[MAP.get(key, key)] = value
        ok = True   
        for k, v in filters:
            if k not in d:
                ok = False
            else:
                if v.startswith('='):
                    if v[1:] != d[k]:
                        ok = False
                elif v not in d[k]:
                    ok = False
        if ok:
            teams.append(d)
    return teams

def store(teams, division):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM division WHERE label=%s', division)
    cursor.execute('INSERT INTO division set label=%s', division)
    division_id = cursor.lastrowid

    # clear old version of teams using that division label
    #cursor.execute('DELETE FROM team WHERE division_id=%s', division_id)
    # should be handled by foreign key constraint
    for team in teams:
        team['division_id'] = division_id

    cursor.execute('DESCRIBE team')
    fields = set((x[0] for x in cursor.fetchall()))

    for team in teams:
        keys = []
        values = []
        for k, v in team.items():
            if k in fields:
                keys.append(k)
                values.append(v)
        placeholder = ", ".join(["%s"] * len(keys))
        stmt = "insert into `{table}` ({columns}) values ({values});".format(table='team', 
                columns=",".join(keys), values=placeholder)
        cursor.execute(stmt, list(values))
    db.commit()

def show(teams):
    counts = defaultdict(set)
    for team in teams:
        for attr in MAP.values():
            if attr in team:
                counts[attr].add(team[attr])
    
    for v, values in counts.items():
        if 1 < len(values) < 9:
            print(v)
            for value in sorted(values):
                print(' ', value)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('xml_in',   help='Input file name')
    parser.add_argument('division', help='Division label')
    parser.add_argument('--store', action='store_true')
    parser.add_argument('-s', '--show', action='store_true')

    # add fields to filter on
    for field in MAP.values():
        try:
            parser.add_argument('--'+field, default=None)
        except argparse.ArgumentError:
            pass

    args = parser.parse_args()
    teams = filter_and_transform(args)
    print(f'Number of teams: {len(teams)}')
    if args.show:
        show(teams)
    else:
        if args.store:
            print('Writing teams to database as', args.division)
            store(teams, args.division)

    



