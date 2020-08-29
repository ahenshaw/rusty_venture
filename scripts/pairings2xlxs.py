#! /usr/bin/env python
from io import StringIO
from xlsxwriter.workbook import Workbook
from modules.database import get_db
import pymysql


def getGames(division):
    header = [('GameNum', 'Date', 'Time', 'FieldID', 'HomeTeam', 'AwayTeam', 'RoundTypeCode')]
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''SELECT 0, DATE_FORMAT(gamedate, "%%m/%%d/%%Y") as date, 
                             TIME_FORMAT(gametime, "%%T") as time, 0, 
                             home, away, "B"
                      FROM game 
                      WHERE agegroup=%s AND archive IS NULL''', division)
    return header + list(cursor.fetchall())

def makeExcel(fn, division):
    # Create a workbook and add a worksheet.
    # output   = StringIO()
    # book  = Workbook(output)
    book  = Workbook(fn)
    sheet = book.add_worksheet()

    for row, record in enumerate(getGames(division)):
        for col, cell in enumerate(record):
            sheet.write(row, col, cell)

    book.close()
    # return output.getvalue()

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('division')
    args = parser.parse_args()
 
    fn = '../output/%s.xlsx' % args.division
    xlxs = makeExcel(fn, args.division)
        # fh.write(xlxs)
    print('Written to', fn)
