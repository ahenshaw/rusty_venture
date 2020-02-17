from collections import defaultdict
import sys
import json
from argparse import ArgumentParser
from modules.team_report import truncate

def get_params():
    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('division', help='Team agegroup or division')
    params = parser.parse_args()

    return params

if __name__ == '__main__':
    # sys.argv.append('/repos/soccer_ng/season/B12X')
    params = get_params()
    
    filename = "{}.json".format(params.division)
    with open(filename) as fh:
        division = json.load(fh)

    teams = division['teams']
    brackets = defaultdict(list)
    for team in teams:
        brackets[team['group']].append(team)
    
    for bracket, names in sorted(brackets.items()):
        print()
        for team in names:
            print('{:20}\t{}'.format(truncate(team['clubname'], 20), 
                                 team['name']))
