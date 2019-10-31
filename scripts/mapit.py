import folium
import math
import pandas as pd
from args import get_args
from collections import Counter
args = get_args()
from team_report import get_teams, truncate
from possible_pairings import get_venues


output = 'season/maps/%s.html' % args.division
 

mapping = {}

teams = get_teams(args.report, filter=args.type)
for team in teams:
    mapping[team.flt_pos] = team
print(args)
if not get_venues(teams):
    print('\nFix errors before proceeding')
    sys.exit()

# count the locations at same point
total = Counter()
for team in teams:
    total[(team.lat, team.lon)] += 1

seen = Counter()
radius = 0.005
for team in teams:
    pt = (team.lat, team.lon)
    if total[pt] > 1:
        print(total[pt], pt, team.name)
    # compute angle offset for each instance at this location
    angle = seen[pt]*2*math.pi/total[pt]
    team.lat += radius * math.sin(angle)
    team.lon += radius * math.cos(angle)
    seen[pt] += 1

map = folium.Map(tiles='Stamen Toner',)
print(map.get_root())

df = pd.read_csv('season/%s.balanced' % args.division, sep='\t', names=['round', 'home', 'away', 'minutes'])
df.replace(0,2, inplace=True)
for row in df.iterrows():
    i, x = row
    pt1 = mapping[x.home].lat, mapping[x.home].lon 
    pt2 = mapping[x.away].lat, mapping[x.away].lon 
    folium.PolyLine([pt1, pt2]).add_to(map)

lats = []
lons = []
for team in teams:
    pt = [team.lat, team.lon]
    folium.CircleMarker(pt, 
        tooltip=team.name, 
        stroke=True, 
        radius=5, 
        color='black', 
        fill_color='purple', 
        fill=False, 
        fill_opacity=0.8, 
        weight=1.0,
        clustered_marker = True,
        ).add_to(map)
    lats.append(team.lat)
    lons.append(team.lon)

bounds = [[min(lats), min(lons)], [max(lats), max(lons)]]
map.fit_bounds(bounds)
map.save(output)
