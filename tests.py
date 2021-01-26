#export PATH=$PATH:/usr/local/share/

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
import sys, random, string, time

driver = webdriver.Firefox()
driver.implicitly_wait(100)


def test_set_name():
    # chrome_options = Options()
    # chrome_options.add_experimental_option("detach", True)
    # driver = webdriver.Chrome(options=chrome_options)

    driver.execute_script('window.open("");')
    driver.switch_to_window(driver.window_handles[-1])
    driver.get('http://localhost:3000/')

def test_rooms():
    #Open four sessions
    for i in range(0,3):
        driver.execute_script('window.open("");')
        driver.get('http://localhost:3000/')
        letters = string.ascii_letters
        name = ''.join(random.choice(letters) for i in range(6))
        driver.find_element_by_id("name").send_keys(name)
        driver.find_element_by_id("sendname").click()
        driver.switch_to_window(driver.window_handles[-1])
    driver.get('http://localhost:3000/')
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


def test_room_privatemessage():
    #Create three users
    for i in range(0,2):
        driver.execute_script('window.open("");')
        driver.get('http://localhost:3000/')
        letters = string.ascii_letters
        name = ''.join(random.choice(letters) for i in range(6))
        driver.find_element_by_id("name").send_keys(name)
        driver.find_element_by_id("sendname").click()
        driver.switch_to_window(driver.window_handles[-1])
    driver.get('http://localhost:3000/')
    letters = string.ascii_letters
    name = ''.join(random.choice(letters) for i in range(6))
    driver.find_element_by_id("name").send_keys(name)
    driver.find_element_by_id("sendname").click()
    #Create one room and join three
    driver.switch_to_window(driver.window_handles[0])
    driver.find_element_by_id("room-name").send_keys('Room A')
    driver.find_element_by_id("sendroom").click()
    for i in range(0,3):
        driver.switch_to_window(driver.window_handles[i])
        driver.find_element_by_id("Room A").click()

    # #Send some messages
    # for i in range(0,5):
    #     time.sleep(2)
    #     driver.find_element_by_id("chatmessage").send_keys('Test')
    #     driver.find_element_by_id("send-message").click()


def test_create_room():
    driver.execute_script('window.open("");')
    driver.switch_to_window(driver.window_handles[-1])
    driver.get('http://localhost:3000/')
    letters = string.ascii_letters
    name = ''.join(random.choice(letters) for i in range(6))
    driver.find_element_by_id("name").send_keys(name)
    driver.find_element_by_id("sendname").click()


def test_joinandrejoin_room():
    #Open four sessions
    for i in range(0,3):
        driver.execute_script('window.open("");')
        driver.get('http://localhost:3000/')
        letters = string.ascii_letters
        name = ''.join(random.choice(letters) for i in range(6))
        driver.find_element_by_id("name").send_keys(name)
        driver.find_element_by_id("sendname").click()
        driver.switch_to_window(driver.window_handles[-1])
    driver.get('http://localhost:3000/')
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
    #Second exits and joins Room B
    driver.find_element_by_id("exit").click()
    driver.find_element_by_id("Room B").click()
    driver.switch_to_window(driver.window_handles[2])
    driver.find_element_by_id("Room B").click()




if __name__ == '__main__':
    print ('Argument List:', str(sys.argv))
    if sys.argv[1] == 'set_name':
        test_set_name()
    elif sys.argv[1] == 'test_rooms':
        test_rooms()
    elif sys.argv[1] == 'test_room_privatemessage':
        test_room_privatemessage()
    elif sys.argv[1] == 'test_create_room':
        test_create_room()
    elif sys.argv[1] == 'test_joinandrejoin_room':
        test_joinandrejoin_room()
