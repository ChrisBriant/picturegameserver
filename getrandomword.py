import sqlalchemy as db
import os

DBNAME = os.environ.get('DBNAME')
DBPASSWORD = os.environ.get('DBPASSWORD')
DBUSER = os.environ.get('DBUSER')

def get_random_word(difficulty):
    engine = db.create_engine('postgresql://{}:{}@localhost/{}'.format(DBUSER,DBPASSWORD,DBNAME))
    connection = engine.connect()
    metadata = db.MetaData()
    words = db.Table('words', metadata, autoload=True, autoload_with=engine)
    query = db.select([words]).where(words.columns.difficulty == difficulty).order_by(db.func.random()).limit(1)
    ResultProxy = connection.execute(query)
    ResultSet = ResultProxy.fetchall()
    return ResultSet
