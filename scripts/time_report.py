import svgwrite as svg
import json
import random

infile = '/repos/soccer_ng/season/B12C.json'
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
    hr, min = divmod(minutes,60)
    return f'{hr}:{min:02d}'

def timebar(doc, times, x, y, fill) :
    group = doc.svg(x=x, y=y, style=bar_style)
    sx = 0
    longest = 0
    total = 0
    for width in sorted(times, reverse=True):
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

with open(infile) as fh:
    data = json.load(fh)

rows = len(data['teams']) + 1
doc = svg.Drawing(filename="/repos/soccer_ng/season/test.svg", 
                  style=label_style,
                  size=("100%", rows*HEIGHT),)
base = 400
ends = []
for i, team in enumerate(data['teams']):
    y = (i+1)*HEIGHT
    doc.add(doc.text(team['name'], text_anchor="end", insert = (base-10, y)))
    times = [10*(random.randint(0, 100)//10) for i in range(5)]
    group, end = timebar(doc, times, base, y-5, '#66cc99')
    doc.add(group)
    ends.append(end)
    times = [10*(random.randint(0, 100)//10) for i in range(5)]
    group, end = timebar(doc, times, base, y-5-BAR, '#cc667f')
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
