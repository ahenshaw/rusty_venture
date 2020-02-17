import argparse
import sys
import svgwrite as svg
from collections import defaultdict
from modules.database import get_db
from modules.team_report import get_teams


BAR = 14
HEIGHT = BAR*3
bar_style = f'''font-size:{BAR-1}px;
font-family:Verdana;
font-weight:normal;
font-style:roman;
stroke:black;
stroke-width:0;
fill:black'''

label_style = f'''font-size:{int(1.2*BAR)}px;
font-family:Verdana;
font-weight:normal;
font-style:roman;
stroke:black;
stroke-width:0;
fill:black'''
def pp(minutes):
    hr, minute = divmod(minutes,60)
    if hr == 0:
        return f'{minute:d}m'
    elif minute==0:
        return f'{hr}h'
    else:
        return f'{hr}h{minute:d}m'

def timebar(doc, times, x, y, fill) :
    group = doc.svg(x=x, y=y, style=bar_style)
    sx = 0
    longest = 0
    total = 0
    # for width in sorted(times, reverse=True):
    for width in times:
        total += width
        width = max(width, 2) # make box show up
        group.add(doc.rect(fill=fill, 
                  stroke="black", 
                  style="stroke-width:1", 
                  insert=(sx, 0), 
                  size=(width, BAR)))
        sx += width
    num = len(times)
    group.add(doc.text(f"{pp(total//num)}", insert=(sx+5,BAR-2)))
    return group, total

def get_pairings(db, division, label):
    cursor = db.cursor()
    cursor.execute('''
        SELECT pairing.id, home, away, cost 
        FROM pairing
        LEFT JOIN division on division.id=division_id
        WHERE division.label=%s
        AND pairing.label=%s''', (division, label))
    return cursor.fetchall()

def process(db, division, label, outfile):
    pairings = get_pairings(db, division, label)
    teams    = get_teams(db, division)

    homes = defaultdict(list)
    aways = defaultdict(list)
    for _, home, away, t in pairings:
        homes[home].append(t)
        aways[away].append(t)

    rows = len(teams) + 1
    doc = svg.Drawing(filename=outfile,
                      style=label_style,
                      size=("100%", rows*HEIGHT),)
    base = 400
    ends = []
    for i, team in enumerate(teams):
        y = (i+1)*HEIGHT
        doc.add(doc.text(team.name, text_anchor="end", insert = (base-10, y)))

        key = team.id
        group, end = timebar(doc, aways[key], base, y-5, '#66cc99')
        doc.add(group)
        ends.append(end)

        group, end = timebar(doc, homes[key], base, y-5-BAR, '#cc667f')
        doc.add(group)
        ends.append(end)

    end_time = 60*((max(ends) + 59)//60)
    print(end_time, max(ends))
    for i, t in enumerate(range(0, end_time+59, 60)):
        doc.add(doc.line(start=(base+t, 0), 
                end=(base+t, y+HEIGHT), 
                stroke="gray", 
                stroke_opacity=0.3,
                style="stroke-width:1"))
        doc.add(doc.text(f'{i}:00', insert = (base+t, BAR), style=bar_style, ))
    doc.attribs['width']=base+end_time+60
    doc.save()


if __name__ == '__main__':
    # test purposes
    parser = argparse.ArgumentParser()
    parser.add_argument('division')
    parser.add_argument('label', nargs='?', default='Default')

    args = parser.parse_args()
    db = get_db()
    outfile = '../season/{}.svg'.format(args.division)
    pairings = process(db, args.division, args.label, outfile)
