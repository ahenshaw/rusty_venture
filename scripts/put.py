from subprocess import run
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('division')
args = parser.parse_args()
division = args.division

run(['pscp', '-load', 'soccer', '../output/%s.html' % division,
     'root@soccer.henshaw.us:/var/www/soccer/%s' % division])

run(['pscp', '-load', 'soccer', "../season/maps/%s.html" % division, 
      'root@soccer.henshaw.us:/var/www/soccer/maps/%s' % division])
