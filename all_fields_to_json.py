import lxml.etree as et
import json
import argparse


''' 
Read the Tournament All Fields Info XML file.  Delete several fields and
rename the rest.  Filter on fields (if any selected).  Filtering works
by checking if value is "in" the field.  Write out JSON.
'''

INPUT = 'season/B12.xml'
OUTPUT = 'season/B12.json'

DROP = ("textbox50" ,"textbox51", "textbox52", "TeamManager",
        "textbox25", "textbox26", "textbox28", "textbox29", 
        "textbox30", "FourthContact", "FourthEmail", "FourthCellPhone",
        "AltTeamNumber",
       )

MAP = {'Comment'       : 'comment',
       'ClubName'      : 'clubname',
       'teamName'      : 'name',
       'textbox15'     : 'gssa_id',
       'textbox16'     : 'program',
       'textbox48'     : 'program2', 
       'textbox44'     : 'group', 
       'TeamStatus'    : 'status',
       'BlackoutDates' : 'blackout',
       'textbox31'     : 'preferred_day',
       'FlightPosition': 'flt_pos',
       'textbox49'     : 'flight',
       'venue'         : 'venue',
       'SubmissionDate': 'submission_date'
      }

def filter_and_transform(args):
    valid = set(MAP.values())
    filters = [(k, v) for (k,v) in vars(args).items() if k in valid and v is not None]
    doc = et.parse('{}/{}.xml'.format(args.path, args.xml_in))
    teams = []
    for element in doc.findall('.//{TournamentTeamInfoAllFields}Detail'):
        d = {}
        for key, value in element.attrib.items():
            if key not in DROP: 
                d[MAP.get(key, key)] = value
        ok = True   
        for k, v in filters:
            if k not in d or v not in d[k]:
                ok = False
        if ok:
            teams.append(d)
    data = {'teams':teams}

    with open('{}/{}.json'.format(args.path, args.json_out), 'w') as outfile:
        json.dump(data, outfile, indent=4)
    print(f'Number of teams: {len(teams)}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('xml_in', help='Input file name')
    parser.add_argument('json_out')
    parser.add_argument('--path', default='season')
    for field in MAP.values():
        parser.add_argument('--'+field, default=None)
    args = parser.parse_args()
    filter_and_transform(args)
    



