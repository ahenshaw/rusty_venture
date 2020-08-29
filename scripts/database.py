import pymysql
from .mysecrets import PASSWORD

USER     = 'soccer_admin'
HOST     = 'soccer.henshaw.us'
DATABASE = 'soccer'

def get_db():
    return pymysql.connect(host   = HOST, 
                           db     = DATABASE,
                           user   = USER, 
                           passwd = PASSWORD)
if __name__ == '__main__':
    get_db()

