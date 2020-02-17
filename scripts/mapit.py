import sys
import json
import folium
from folium import plugins
import math
from argparse import ArgumentParser
from collections import Counter
import os.path
import pymysql
from modules.database import get_db
from itertools import groupby

def get_teams(db, division):
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute('''SELECT team.id, team.name, lat, lon, venue.name as venue_name
                      FROM team 
                      LEFT JOIN division ON division.id = division_id
                      LEFT JOIN venue ON venue.id = venue_id
                      WHERE division.label=%s''', (division))
    return cursor.fetchall()

def get_pairings(db, division):
    cursor = db.cursor()
    cursor.execute('''SELECT pairing.label, home, away 
                      FROM pairing 
                      LEFT JOIN division ON division.id = division_id
                      WHERE division.label=%s
                      ORDER BY pairing.label''', (division))
    results = []
    for k, v in groupby(cursor.fetchall(), key=lambda x:x[0]):
        results.append((k, [x[1:] for x in v]))
    return results


parser = ArgumentParser()
parser.add_argument("division")
args = parser.parse_args()

db = get_db()
output   = 'c:/repos/soccer_ng/season/maps/%s.html' % args.division
# filename = '%s.json' % args.division
# with open(filename) as fh:
#     division = json.load(fh)

mapping = {}

teams = get_teams(db, args.division)
for team in teams:
    print(team)
    mapping[team['id']] = team
    # team['lat'] = float(team.lat)
    # team['lon'] = float(team.lon)

# count the locations at same point
total = Counter()
for team in teams:
    total[(team['lat'], team['lon'])] += 1

seen = Counter()
radius = 0.005
origin = {}
for team in teams:
    pt = (team['lat'], team['lon'])
    # compute angle offset for each instance at this location
    angle = seen[pt]*2*math.pi/total[pt]
    team['lat'] += radius * math.sin(angle)
    team['lon'] += radius * math.cos(angle)
    if total[pt] > 1:
        origin[(team['lat'], team['lon'])] = pt
    seen[pt] += 1

#map = folium.Map(tiles='Stamen Toner',)
map = folium.Map(tiles='OpenStreetMap',)
folium.TileLayer('Stamen Toner').add_to(map)

# team_group = folium.FeatureGroup(name='Teams')
show = True
for label, pairings in get_pairings(db, args.division):
    pairing_group = folium.FeatureGroup(name=label, show=show)
    # check for home-and-home
    seen = set()
    h_and_h = set()

    for home, away in pairings:
        if (away, home) in seen:
            h_and_h.add((home, away))
            h_and_h.add((away, home))
        seen.add((home, away))

    for home, away in pairings:
        # if mapping[home].group != mapping[away].group:
        #     print('**', home, mapping[home].group, away, mapping[away].group)
        pt1 = mapping[home]['lat'], mapping[home]['lon'] 
        pt2 = mapping[away]['lat'], mapping[away]['lon'] 
        if (home, away) in h_and_h:
            path = folium.PolyLine([pt1, pt2], color='navy',opacity=0.3)
        else:
            path = plugins.AntPath(locations=[pt1, pt2], weight=3, color='navy', delay=3200)
        path.add_to(pairing_group)

    map.add_child(pairing_group)
    show = False # show the first featuregroup only
try:
    pairing_group
except NameError:
    pairing_group = folium.FeatureGroup(name='Teams', show=show)
    map.add_child(pairing_group)

lats = []
lons = []
for i, team in enumerate(teams):
    print("{:2}.  {} {}".format(i+1, team, team['venue_name']))
    pt = (team['lat'], team['lon'])
    if pt in origin:
        folium.PolyLine([pt, origin[pt]],
                         color='red', weight=1
                         ).add_to(pairing_group)
    folium.CircleMarker(pt, 
        tooltip=team['name'], 
        stroke=True, 
        radius=5, 
        color='black', 
        fill_color='red', 
        fill=False, 
        fill_opacity=0.8, 
        weight=1.0,
        clustered_marker = True,
        ).add_to(map)
    lats.append(team['lat'])
    lons.append(team['lon'])

bounds = [[min(lats), min(lons)], [max(lats), max(lons)]]
# map.add_child(team_group)
folium.LayerControl().add_to(map)
map.fit_bounds(bounds)
map.save(output)
print("Map saved to {}".format(os.path.abspath(output)))
