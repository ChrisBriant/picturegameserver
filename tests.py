#export PATH=$PATH:/usr/local/share/

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
import sys, random, string, time

driver = webdriver.Firefox()
driver.implicitly_wait(1)


def test_set_name():
    # chrome_options = Options()
    # chrome_options.add_experimental_option("detach", True)
    # driver = webdriver.Chrome(options=chrome_options)

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

    driver.switch_to_window(driver.window_handles[0])
    driver.find_element_by_id("Room A").click()

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
    # windows = driver.window_handles
    # for window in windows:
    #     print()
    #     print(window)
    #     driver.switch_to_window(window)
    #     try:
    #         driver.find_element_by_id("guess").send_keys(word)
    #         driver.find_element_by_id("sendguess").click()
    #         break
    #     except Exception as e:
    #         print(e)
        # if window == driver.current_window_handle:
        #     print('This is the current window')


#
# def test_setuproom():
#     #Open four sessions
#     for i in range(0,3):
#         driver.execute_script('window.open("");')
#         driver.get('http://localhost:5000/')
#         letters = string.ascii_letters
#         name = ''.join(random.choice(letters) for i in range(6))
#         driver.find_element_by_id("name").send_keys(name)
#         driver.find_element_by_id("sendname").click()
#         driver.switch_to_window(driver.window_handles[-1])
#     driver.get('http://localhost:5000/')
#     letters = string.ascii_letters
#     name = ''.join(random.choice(letters) for i in range(6))
#     driver.find_element_by_id("name").send_keys(name)
#     driver.find_element_by_id("sendname").click()
#
#     #Create two rooms
#     driver.switch_to_window(driver.window_handles[0])
#     driver.find_element_by_id("room-name").send_keys('Room A')
#     driver.find_element_by_id("sendroom").click()
#
#     #First two windows open room a
#     driver.switch_to_window(driver.window_handles[0])
#     driver.find_element_by_id("Room A").click()
#     #Second person joins
#     driver.switch_to_window(driver.window_handles[1])
#     driver.find_element_by_id("Room A").click()
#
# def test_play_round():
#     test_startgame()
#     handle1 = driver.window_handles[0]
#     handle2 = driver.window_handles[1]
#     for i in range(0,12):
#         cards = driver.find_elements_by_class_name('cardfront-img')
#         print(cards[1])
#         cards[-1].click()
#         if driver.current_window_handle == handle1:
#             driver.switch_to_window(driver.window_handles[1])
#         else:
#             print("Window one")
#             driver.switch_to_window(driver.window_handles[0])
#         # try:
#         #     driver.find_element_by_id("firstgo")
#         #     cards = driver.find_elements_by_class_name('cardfront-img')
#         #     cards[1].click()
#         #     if driver.current_window_handle == handle1:
#         #         driver.switch_to_window(driver.window_handles[1])
#         #     else:
#         #         print("Window one")
#         #         driver.switch_to_window(driver.window_handles[0])
#         # except Exception as e:
#         #     print(e)
#         #     if driver.current_window_handle == handle1:
#         #         driver.switch_to_window(driver.window_handles[1])
#         #     else:
#         #         driver.switch_to_window(driver.window_handles[0])
#         #     cards = driver.find_elements_by_class_name('cardfront-img')
#         #     cards[1].click()
#
#
#         # driver.switch_to_window(driver.window_handles[1])
#         # cards = driver.find_elements_by_class_name('cardfront-img')
#         # print(len(cards))
#         # cards[1].click()
#         # driver.switch_to_window(driver.window_handles[1])
#         # cards = driver.find_elements_by_class_name('cardfront-img')
#         # print(len(cards))
#         # cards[1].click()
#
#
#     # #Second exits and joins Room B
#     # driver.find_element_by_id("exit").click()
#     # driver.find_element_by_id("Room B").click()
#     # driver.switch_to_window(driver.window_handles[2])
#     # driver.find_element_by_id("Room B").click()
#
# def test_end_game():
#     test_startgame()
#
# def switch_window(current_handle,handle1):
#     if current_handle == handle1:
#         driver.switch_to_window(driver.window_handles[1])
#     else:
#         print("Window one")
#         driver.switch_to_window(driver.window_handles[0])
#
#
# def get_cards():
#     try:
#         print('Trying')
#         cards = driver.find_elements_by_class_name('cardfront-img')
#         return cards
#     except Exception as e:
#         print("No such class ", e)
#         return None
#
# def click_card(suit,cards):
#     if suit:
#         selected_card = None
#         for idx, card in enumerate(cards):
#             #image = driver.find_element_by_xpath("//img")
#             if card.get_attribute("id")[0] == suit:
#                 selected_card = card
#             print("Image here", card.get_attribute("id"), idx)
#         if selected_card:
#             selected_card.click()
#         else:
#             cards[-1].click()
#     else:
#         cards[-1].click()
#
# def get_suit():
#     try:
#         trick = driver.find_element_by_id('latestintrick')
#         return trick.get_attribute('class')[0]
#     except Exception as e:
#         return None
#
# def is_first():
#     try:
#         driver.find_element_by_id('firstgo')
#         return True
#     except Exception as e:
#         print('notfirst', e)
#         return False
#
#
# def test_tie_break_round():
#     test_startgame()
#     print("hello")
#
#     #print('Card length ',len(cards))
#     handle1 = driver.window_handles[0]
#     handle2 = driver.window_handles[1]
#
#     for i in range(0,12):
#         if not is_first():
#             switch_window(driver.current_window_handle,handle1)
#         cards = get_cards()
#         if cards:
#             print("clicking")
#             suit = get_suit()
#             print(suit)
#             click_card(suit,cards)
#             #cards[-1].click()
#         else:
#             print("clicking after fail")
#             #switch_window(driver.current_window_handle,handle1)
#             #cards = get_cards()
#             #cards[-1].click()
#
# def setup_three_players():
#     #Open four sessions
#     for i in range(0,2):
#         driver.execute_script('window.open("");')
#         driver.get('http://localhost:5000/')
#         letters = string.ascii_letters
#         name = ''.join(random.choice(letters) for i in range(6))
#         driver.find_element_by_id("name").send_keys(name)
#         driver.find_element_by_id("sendname").click()
#         driver.switch_to_window(driver.window_handles[-1])
#     driver.get('http://localhost:5000/')
#     letters = string.ascii_letters
#     name = ''.join(random.choice(letters) for i in range(6))
#     driver.find_element_by_id("name").send_keys(name)
#     driver.find_element_by_id("sendname").click()
#
#     #Create a room
#     driver.switch_to_window(driver.window_handles[0])
#     driver.find_element_by_id("room-name").send_keys('Room A')
#     driver.find_element_by_id("sendroom").click()
#
#     #First two windows open room a
#     driver.switch_to_window(driver.window_handles[0])
#     driver.find_element_by_id("Room A").click()
#     #Second person joins
#     driver.switch_to_window(driver.window_handles[1])
#     driver.find_element_by_id("Room A").click()
#     #Third person joins
#     driver.switch_to_window(driver.window_handles[2])
#     driver.find_element_by_id("Room A").click()
#     driver.find_element_by_id("startgame-btn").click()
#
# def switch_toactive(handles):
#     for handle in handles:
#         driver.switch_to_window(handle)
#         if is_first():
#             return
#
# def test_three_player_knockout():
#     setup_three_players()
#
#     handles = []
#     handles.append(driver.window_handles[0])
#     handles.append(driver.window_handles[1])
#     handles.append(driver.window_handles[2])
#
#     for i in range(0,18):
#         switch_toactive(handles)
#         cards = get_cards()
#         if cards:
#             print("clicking")
#             suit = get_suit()
#             print(suit)
#             click_card(suit,cards)
#             #cards[-1].click()
#         else:
#             print("clicking after fail")


## TODO:
#   1. Block card clicking unless active player - DONE
#   2. Card must follow suite rules - best in front end -DONE
#   3. Test tie breaker when middle of game
#   4. Factor in knockout rule
#       I believe it needs to have an option to knock out players if 0 is scored
#       in a round after the first one

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
    # elif sys.argv[1] == 'test_setuproom':
    #     print(str(sys.argv[1]))
    #     test_setuproom()
    # elif sys.argv[1] == 'test_round_winner':
    #     test_round_winner()
    # elif sys.argv[1] == 'test_play_round':
    #     test_play_round()
    #
    # elif sys.argv[1] == 'test_tie_break_round':
    #     test_tie_break_round()
    # elif sys.argv[1] == 'test_three_player_knockout':
    #     test_three_player_knockout()
