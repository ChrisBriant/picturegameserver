#export PATH=$PATH:/usr/local/share/

import sqlalchemy as db
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
import os

DBNAME = os.environ.get('DBNAME')
DBPASSWORD = os.environ.get('DBPASSWORD')
DBUSER = os.environ.get('DBUSER')

driver = webdriver.Firefox()
driver.implicitly_wait(1)

engine = db.create_engine('postgresql://{}:{}@localhost/{}'.format(DBUSER,DBPASSWORD,DBNAME))
connection = engine.connect()
metadata = db.MetaData()
words = db.Table('words', metadata, autoload=True, autoload_with=engine)


if __name__ == '__main__':
    driver.execute_script('window.open("");')
    driver.get('https://randomwordgenerator.com/phrase.php')
    driver.switch_to_window(driver.window_handles[0])
    driver.find_element_by_id("qty").clear()
    driver.find_element_by_id("qty").send_keys('50')
    driver.find_element_by_id("btn_submit_generator").click()
    phrases = driver.find_elements_by_class_name('support-phrase')
    for phrase in phrases:
        print(phrase.text)
        query = db.insert(words).values(difficulty=2, word=phrase.text)
        connection.execute(query)
