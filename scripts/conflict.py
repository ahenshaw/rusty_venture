from argparse import ArgumentParser
from modules.database import get_db

def get_params():
    parser = ArgumentParser()
    parser.add_argument('division', help='Team agegroup or division')
    parser.add_argument('t1', help='Flight position of team')
    parser.add_argument('t2', help='Flight position of conflicting team')
    params = parser.parse_args()

    return params

if __name__ == "__main__":
    args = get_params()
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO conflict set division=%s, t1=%s, t2=%s', (args.division, args.t1, args.t2))
    db.commit()
