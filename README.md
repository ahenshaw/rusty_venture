# How to schedule the season.

## Login
Login to affinity-sports.com
User name: andyrils

Use the Tournament tab
Make sure to select the current season.

## Accept Teams
1. Under *Team Application Lookup* select correct program and search for **New** status.
2. Mouse over the status column, each row will change to a drop-down box.  Change to **Final Acceptance**.  Do this for each team.
3. Click on *Save Changes* button.

## Create Play Levels
1. Go to Flight Schemas|Play Levels and delete any team assignments.
2. Go to Bracket Play
3. Fill-in the following:
    1. Select Play Group: (e.g., U19 Boys)
    2. Teams per Bracket: (same as Total # of Teams)
    3. \# of Brackets: (1)
    4. Teams to Advance from Bracket: (1)
4. Click <Create Bracketing> button
5. Click <Rank All Unranked Teams> button
6. Click <Update Rankings> button

7. Go to Play Levels
8. Update game time and interval

B19, G19
Start Time Interval: 95
Play Time Length: 90
Halftime Length: 5
Intergame Interval: 600

B16, G16
Start Time Interval: 85
Play Time Length: 80
Halftime Length: 5
Intergame Interval: 600

B14, G14
Start Time Interval: 80
Play Time Length: 75
Halftime Length: 5
Intergame Interval: 600

B12, G12
Start Time Interval: 75
Play Time Length: 70
Halftime Length: 5
Intergame Interval: 600

## Generate Reports

1. Under Reports|Team Reports, generate "Tournament All Fields Info" for each age group (XML format).  Export to the season subdirectory.  
2. Use a name like "B19.xml".

## Run Programs
1. **Run py subset.py B19 -t R -o RB19** to get a REC subset of clubs
2. **Run py profiler.py B19**.  
   * If there are any missing field names, an error message will
be shown.  
   * If so, make sure that there is a venue associated with 
the club (edit data/Clubs and Fields.xls).  
   * Then **run database/club_venue.py**.
   * If new venues have been added, you will then need to **run 
get_lat_lon.py** and then **distance_grid.py**.  distance_grid 
will take a while to run.

3. **Run py profiler.py B19** again.  Note the outliers.

3. **Run make_pairings.py B19 --outliers 1,4,...**. Output will be "season/B19.pairings".
    * if home-and-home use py make_pairings G12 --hh -r 5 . Don't specify outliers.

4. **Run py balance_home_and_away.py B19**. Output will be "season/B19.balanced".
4. A plot of drive time can be generated by **running time_report.py**.
4. **Run py make_calendar.py B19**. Output will be "season/B19.csv".
7. **Run py pairings2html.py B19**    -> creates .HTML
8. **Run py put.py B19** -> pushes CSV and HTML to web server 
   
9. Go to website app directory.  
10. Run csv2db.py B19.

10. Check for blackout problems by viewing the .HTML file (unless changed, defaults to 'web/recpairing/dategrid.html') and moving games. 
Download the updated schedule file by doing:
    1. cd app
    2. ./pairings2xlsx.py G12
    3. pscp root@soccer.henshaw.us:/var/www/soccer/data/G12.xlsx data

or
just run py pairings2xlsx.py B19

11. Upload to GSSA

12. Run make_brackets.py to create smaller brackets for the age group.  Updates have to be made by hand using the PlayLevel screen.



