#export PATH=$PATH:/usr/local/share/

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
import sys, random, string, time

driver = webdriver.Firefox()
driver.implicitly_wait(1)


def test_set_name():
    driver.execute_script('window.open("");')
    driver.switch_to_window(driver.window_handles[-1])
    driver.get('http://localhost:5000/')

def test_rooms():
    #Open four sessions
    for i in range(0,3):
        driver.execute_script('window.open("");')
        driver.get('http://localhost:5000/')
        letters = string.ascii_letters
        name = ''.join(random.choice(letters) for i in range(6))
        driver.find_element_by_id("name").send_keys(name)
        driver.find_element_by_id("sendname").click()
        driver.switch_to_window(driver.window_handles[-1])
    driver.get('http://localhost:5000/')
    letters = string.ascii_letters
    name = ''.join(random.choice(letters) for i in range(6))
    driver.find_element_by_id("name").send_keys(name)
    driver.find_element_by_id("sendname").click()

    #Create two rooms
    driver.switch_to_window(driver.window_handles[0])
    driver.find_element_by_id("room-name").send_keys('Room A')
    driver.find_element_by_id("sendroom").click()
    driver.switch_to_window(driver.window_handles[2])
    driver.find_element_by_id("room-name").send_keys('Room B')
    driver.find_element_by_id("sendroom").click()

    #First two windows open room a
    driver.switch_to_window(driver.window_handles[0])
    driver.find_element_by_id("Room A").click()
    driver.switch_to_window(driver.window_handles[1])
    driver.find_element_by_id("Room A").click()

def test_rooms_2():
    #Open four sessions don't enter any rooms
    for i in range(0,3):
        driver.execute_script('window.open("");')
        driver.get('http://localhost:5000/')
        letters = string.ascii_letters
        name = ''.join(random.choice(letters) for i in range(6))
        driver.find_element_by_id("name").send_keys(name)
        driver.find_element_by_id("sendname").click()
        driver.switch_to_window(driver.window_handles[-1])
    driver.get('http://localhost:5000/')
    letters = string.ascii_letters
    name = ''.join(random.choice(letters) for i in range(6))
    driver.find_element_by_id("name").send_keys(name)
    driver.find_element_by_id("sendname").click()

    #Create two rooms
    driver.switch_to_window(driver.window_handles[0])
    driver.find_element_by_id("room-name").send_keys('Room A')
    driver.find_element_by_id("sendroom").click()
    driver.switch_to_window(driver.window_handles[2])
    driver.find_element_by_id("room-name").send_keys('Room B')
    driver.find_element_by_id("sendroom").click()


def test_room_timer():
    #Create rooms and join one of them
    test_rooms_2()
    driver.switch_to_window(driver.window_handles[0])
    driver.find_element_by_id("Room A").click()
    driver.switch_to_window(driver.window_handles[1])
    driver.find_element_by_id("Room A").click()
    driver.switch_to_window(driver.window_handles[1])
    driver.find_element_by_id("start-game").click()

def test_startgame():
    test_rooms()
    driver.switch_to_window(driver.window_handles[1])
    driver.find_element_by_id("start-game").click()


def test_3_player():
    #Open four sessions
    for i in range(0,2):
        driver.execute_script('window.open("");')
        driver.get('http://localhost:5000/')
        letters = string.ascii_letters
        name = ''.join(random.choice(letters) for i in range(6))
        driver.find_element_by_id("name").send_keys(name)
        driver.find_element_by_id("sendname").click()
        driver.switch_to_window(driver.window_handles[-1])
    driver.get('http://localhost:5000/')
    letters = string.ascii_letters
    name = ''.join(random.choice(letters) for i in range(6))
    driver.find_element_by_id("name").send_keys(name)
    driver.find_element_by_id("sendname").click()

    #Create two rooms
    driver.switch_to_window(driver.window_handles[0])
    driver.find_element_by_id("room-name").send_keys('Room A')
    driver.find_element_by_id("sendroom").click()
    #First two windows open room a
    driver.switch_to_window(driver.window_handles[0])
    driver.find_element_by_id("Room A").click()
    driver.switch_to_window(driver.window_handles[1])
    driver.find_element_by_id("Room A").click()
    driver.switch_to_window(driver.window_handles[2])
    driver.find_element_by_id("Room A").click()
    #Start the game
    driver.switch_to_window(driver.window_handles[1])
    driver.find_element_by_id("start-game").click()


def test_5_player():
    #Open four sessions
    for i in range(0,4):
        driver.execute_script('window.open("");')
        driver.get('http://localhost:5000/')
        letters = string.ascii_letters
        name = ''.join(random.choice(letters) for i in range(6))
        driver.find_element_by_id("name").send_keys(name)
        driver.find_element_by_id("sendname").click()
        driver.switch_to_window(driver.window_handles[-1])
    driver.get('http://localhost:5000/')
    letters = string.ascii_letters
    name = ''.join(random.choice(letters) for i in range(6))
    driver.find_element_by_id("name").send_keys(name)
    driver.find_element_by_id("sendname").click()

    #Create two rooms
    driver.switch_to_window(driver.window_handles[0])
    driver.find_element_by_id("room-name").send_keys('Room A')
    driver.find_element_by_id("sendroom").click()
    #First two windows open room a
    driver.switch_to_window(driver.window_handles[0])
    driver.find_element_by_id("Room A").click()
    driver.switch_to_window(driver.window_handles[1])
    driver.find_element_by_id("Room A").click()
    driver.switch_to_window(driver.window_handles[2])
    driver.find_element_by_id("Room A").click()
    driver.switch_to_window(driver.window_handles[3])
    driver.find_element_by_id("Room A").click()
    driver.switch_to_window(driver.window_handles[4])
    driver.find_element_by_id("Room A").click()
    #Start the game
    driver.switch_to_window(driver.window_handles[1])


def test_5_player_giveup():
    test_5_player()
    for i in range(0,4):
        for j in range(0,5):
            try:
                driver.switch_to_window(driver.window_handles[j])
                driver.find_element_by_id("giveup").click()
            except Exception as e:
                print(e)
        for k in range(0,5):
            try:
                driver.switch_to_window(driver.window_handles[k])
                driver.find_element_by_id("continue").click()
            except Exception as e:
                print(e)

def test_limit_5():
    test_5_player()
    #Open 6th window shouldn't be able to join room
    driver.execute_script('window.open("");')
    driver.switch_to_window(driver.window_handles[2])
    driver.get('http://localhost:5000/')
    letters = string.ascii_letters
    name = ''.join(random.choice(letters) for i in range(6))
    driver.find_element_by_id("name").send_keys(name)
    driver.find_element_by_id("sendname").click()


def test_endgame():
    #two player
    test_startgame()
    #Get the word
    try:
        word = driver.find_element_by_id("the-word")
    except:
        driver.switch_to_window(driver.window_handles[0])
        word = driver.find_element_by_id("the-word")
    print(word.text)


if __name__ == '__main__':
    print ('Argument List:', str(sys.argv))
    if sys.argv[1] == 'set_name':
        test_set_name()
    elif sys.argv[1] == 'test_rooms':
        print(str(sys.argv[1]))
        test_rooms()
    elif sys.argv[1] == 'test_rooms_2':
        print(str(sys.argv[1]))
        test_rooms_2()
    elif sys.argv[1] == 'test_startgame':
        print(str(sys.argv[1]))
        test_startgame()
    elif sys.argv[1] == 'test_endgame':
        test_endgame()
    elif sys.argv[1] == 'test_3_player':
        test_3_player()
    elif sys.argv[1] == 'test_5_player':
        test_5_player()
    elif sys.argv[1] == 'test_5_player_giveup':
        test_5_player_giveup()
    elif sys.argv[1] == 'test_limit_5':
        test_limit_5()
    elif sys.argv[1] == 'test_room_timer':
        test_room_timer()
