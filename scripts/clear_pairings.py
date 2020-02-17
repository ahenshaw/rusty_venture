from argparse import ArgumentParser
import sys
# custom modules
from modules.database import get_db

def get_params():
    parser = ArgumentParser()
    parser.add_argument('division', help='Team agegroup or division')
    parser.add_argument('label', nargs='?', default='Default')

    args = parser.parse_args()

    return args

if __name__ == '__main__':
    args = get_params()
    print(f'This will clear the pairings for the {args.division} division with the {args.label} label')
    answer = input('Are you sure? [y/N] ')
    if not answer.lower().startswith('y'):
        print('Canceling')
        sys.exit()
        
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM division WHERE label=%s', (args.division,))
    division_id, = cursor.fetchone()
    count = cursor.execute('DELETE FROM pairing WHERE division_id=%s AND label=%s', (division_id, args.label))
    print(f"{count} records deleted")
    db.commit()

