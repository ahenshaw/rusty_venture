import sys
import json
import folium
from folium import plugins
import math
from argparse import ArgumentParser
from collections import Counter
from modules.team_report import get_teams_from_json
import os.path

parser = ArgumentParser()
parser.add_argument("division")
args = parser.parse_args()

output   = 'maps/%s.html' % args.division
filename = '%s.json' % args.division
with open(filename) as fh:
    division = json.load(fh)

mapping = {}

teams = get_teams_from_json(division)
for team in teams:
    mapping[team.flt_pos] = team
    team.lat = float(team.lat)
    team.lon = float(team.lon)

# count the locations at same point
total = Counter()
for team in teams:
    total[(team.lat, team.lon)] += 1

seen = Counter()
radius = 0.005
origin = {}
for team in teams:
    pt = (team.lat, team.lon)
    # compute angle offset for each instance at this location
    angle = seen[pt]*2*math.pi/total[pt]
    team.lat += radius * math.sin(angle)
    team.lon += radius * math.cos(angle)
    if total[pt] > 1:
        origin[(team.lat, team.lon)] = pt
    seen[pt] += 1

#map = folium.Map(tiles='Stamen Toner',)
map = folium.Map(tiles='OpenStreetMap',)
folium.TileLayer('Stamen Toner').add_to(map)

pairing_group = folium.FeatureGroup(name='Pairings')
team_group = folium.FeatureGroup(name='Teams')

# check for home-and-home
seen = set()
h_and_h = set()
if 'pairings' not in division:
    division['pairings'] = []

for _, home, away, _ in division['pairings']:
    if (away, home) in seen:
        h_and_h.add((home, away))
        h_and_h.add((away, home))
    seen.add((home, away))

for r, home, away, weight in division['pairings']:
    if mapping[home].group != mapping[away].group:
        print('**', home, mapping[home].group, away, mapping[away].group)
    pt1 = mapping[home].lat, mapping[home].lon 
    pt2 = mapping[away].lat, mapping[away].lon 
    if (home, away) in h_and_h:
        path = folium.PolyLine([pt1, pt2], color='navy',opacity=0.3)
    else:
        path = plugins.AntPath(locations=[pt1, pt2], weight=3, color='navy', delay=3200)
    path.add_to(pairing_group)

lats = []
lons = []
for i, team in enumerate(teams):
    print("{:2}.  {} {}".format(i+1, team, team.venue))
    pt = (team.lat, team.lon)
    if pt in origin:
        folium.PolyLine([pt, origin[pt]],
                         color='red', weight=1
                         ).add_to(team_group)
    folium.CircleMarker(pt, 
        tooltip=team.name, 
        stroke=True, 
        radius=5, 
        color='black', 
        fill_color='red', 
        fill=False, 
        fill_opacity=0.8, 
        weight=1.0,
        clustered_marker = True,
        ).add_to(team_group)
    lats.append(team.lat)
    lons.append(team.lon)

bounds = [[min(lats), min(lons)], [max(lats), max(lons)]]
map.add_child(pairing_group)
map.add_child(team_group)
folium.LayerControl().add_to(map)
map.fit_bounds(bounds)
map.save(output)
print("Map saved to {}".format(os.path.abspath(output)))
