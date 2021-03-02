import sqlalchemy as db
import os

DBNAME = os.environ.get('DBNAME')
DBPASSWORD = os.environ.get('DBPASSWORD')
DBUSER = os.environ.get('DBUSER')

if __name__ == '__main__':
    engine = db.create_engine('postgresql://{}:{}@localhost/{}'.format(DBUSER,DBPASSWORD,DBNAME))
    connection = engine.connect()
    metadata = db.MetaData()
    words = db.Table('words', metadata, autoload=True, autoload_with=engine)
    query = db.select([words]).where(words.columns.difficulty == 1).order_by(db.func.random()).limit(1)
    ResultProxy = connection.execute(query)
    ResultSet = ResultProxy.fetchall()
    print(ResultSet)
