import sqlalchemy as db
import pandas as pd
import os

DBNAME = os.environ.get('DBNAME')
DBPASSWORD = os.environ.get('DBPASSWORD')
DBUSER = os.environ.get('DBUSER')

if __name__ == '__main__':
    engine = db.create_engine('postgresql://{}:{}@localhost/{}'.format(DBUSER,DBPASSWORD,DBNAME))
    connection = engine.connect()
    metadata = db.MetaData()
    words = db.Table('words', metadata, autoload=True, autoload_with=engine)

    # Print the column names
    print(words.columns.keys())

    #Select
    query = db.select([words])
    ResultProxy = connection.execute(query)
    ResultSet = ResultProxy.fetchall()
    print(ResultSet)

    #Import words into DB from csv
    import_data = pd.read_csv('./wordlist.csv',error_bad_lines=False)
    for i in range(len(import_data)):
        word = str(import_data.loc[i,'word'])
        #Insert into db
        query = db.insert(words).values(difficulty=1, word=word)
        connection.execute(query)
