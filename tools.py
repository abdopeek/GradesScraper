import re
from utils import *
from selenium import webdriver  # use it to open the actual browser for cookies
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.keys import Keys  # to use a keyboard
from selenium.webdriver.support.ui import WebDriverWait  # wait till site loads
from selenium.webdriver.support import expected_conditions as EC  # if conditions for selenium
from selenium.common.exceptions import NoSuchElementException, TimeoutException  # exceptions
from selenium.webdriver.common.by import By  # to locate element
import requests  # to work with requests instead of selenium
import json  # work with the return from the website
from time import sleep  # sleep

ser = Service(DRIVER_LOCATION)
op = webdriver.EdgeOptions()
op.add_argument('headless')
op.add_argument('--log-level=3')
op.add_argument('--log-path=path/to/edge.log')
# op.add_experimental_option('excludeSwitches', ['enable-logging'])
op.add_experimental_option('detach', True)
driver = webdriver.Edge(service=ser, options=op)
driver.minimize_window()
driver.get("https://upeisis.uofcanada.edu.eg/PowerCampusSelfService/Registration/Schedule")
s = requests.Session()
sleep(2)


def set_cookies(cookies, header):
    default = ['messagesUtk=50c6732c976448b3abbeadcea96c0180', '', '']
    for cookie in cookies:
        updated = f"{cookie['name']}={cookie['value']}"
        if cookie['name'] == "SelfService":
            default[2] = updated
        elif cookie['name'] == "ASP.NET_SessionId":
            default[1] = updated
        header['cookie'] = ';'.join(default)


def enterUsername(username):
    try:
        search = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="txtUserName"]'))
        )
    except NoSuchElementException:
        print("Element not found, exiting")
        driver.quit()
    except TimeoutException:
        print("Time out")
        driver.quit()
    search.send_keys(username)
    search.send_keys(Keys.RETURN)


def enterPassword(password):
    sleep(0.5)
    search = driver.find_element(By.XPATH, '//*[@id="txtPassword"]')
    search.send_keys(password)
    search.send_keys(Keys.RETURN)

def get_student_id():
    url = 'https://upeisis.uofcanada.edu.eg/PowerCampusSelfService/Registration/Schedule'
    sleep(1.5)
    cookies = driver.get_cookies()
    set_cookies(cookies, section_head)
    resp = s.get(url, headers=section_head)
    pattern = r'<input\s+id="hdnPersonId"\s+type="hidden"\s+value="(\d+)"\s*/>'
    match = re.search(pattern, resp.text)
    if match:
        value = match.group(1)
        return value
    else:
        raise "ERROR"


def get_sections(id):
    sections = []
    url = r'https://upeisis.uofcanada.edu.eg/PowerCampusSelfService/Schedule/Student'
    session = {"year": "2023", "term": "FALL", "session": ""}  # update this every semester
    payload = {'personId': id, "yearTermSession": session}
    sleep(1.5)
    cookies = driver.get_cookies()
    set_cookies(cookies, sched_head)
    resp = s.post(url, data=json.dumps(payload), headers=sched_head)
    if resp.status_code == 200:
        resp = resp.json()
    else:
        raise "ERROR"
    data = json.loads(resp)['data']['schedule'][0]['sections']
    for i in data:
        if i:
            data = i
    for section in data:
        if section['eventSubType'] == "Lecture":
            sections.append(section['id'])
    return sections


def get_data(param):
    grade_link = 'https://upeisis.uofcanada.edu.eg/PowerCampusSelfService/Students/ActivityGrades'

    sleep(1.5)  # wait for cookies to load in
    cookies = driver.get_cookies()
    set_cookies(cookies, grades_head)
    outputs = []
    for section in param:
        resp = s.post(grade_link, data=json.dumps(section), headers=grades_head)
        if resp.status_code == 200:  # accepted
            resp = resp.json()
        else:
            return "Error"
        try:
            json_value = json.loads(resp)['data']
            output = {
                'name': json_value['sectionName'],
                'data': json_value
            }
        except:
            pass
        else:
            outputs.append(output)

    return outputs


def process(data):
    finalTermAssignments = data['finaltermAssignments']
    for indice, i in enumerate(finalTermAssignments):
        i = {
            'description': i['description'],
            'studentAssignments': i['studentAssignments']
        }
        assignments = i['studentAssignments']

        for index, assignment in enumerate(assignments):
            filtered = {
                'activityScore': assignment['activityScore'],
                'earnedPoints': assignment['earnedPoints'],
                'isEarned': assignment['isEarned'],
                'title': assignment['title'],
                'possiblePoints': assignment['possiblePoints']
            }

            i['studentAssignments'][index] = filtered

        finalTermAssignments[indice] = i

    data['finaltermAssignments'] = finalTermAssignments
    result = {
        'finalscore': data['finalScore'],
        'finalTermAssignments': data['finaltermAssignments']
    }
    return result


def print_output(data):
    total_score = 0
    highest_score = 0
    name = data['name']
    scores = data['data']
    assignments = scores['finalTermAssignments']
    print("-------------------------------------------")
    print(f"\t\t{name}\t\t")
    for assignment in assignments:
        print(f"{assignment['description']}")
        for sub_assignment in assignment['studentAssignments']:
            if sub_assignment['isEarned']:
                total_score += float(sub_assignment['earnedPoints'])
                highest_score += float(sub_assignment['possiblePoints'])
                print(f"\t{sub_assignment['title']}\t\t{sub_assignment['earnedPoints']}/{sub_assignment['possiblePoints']}"
                      f" | %{(float(sub_assignment['earnedPoints'])/float(sub_assignment['possiblePoints'])) * 100:.2f}")
            else:
                print(f"\t{sub_assignment['title']}\t\tNot earned yet/{sub_assignment['possiblePoints']}")
    try:
        lost = highest_score - total_score
        print(f"Final Score: {total_score:.2f}/{highest_score:.2f} | %{lost:.2f} lost")
        if lost < 9:
            print("Best case scenario: A+")
        elif 9 < lost < 15:
            print("Best case scenario: A")
        elif 15 < lost < 20:
            print("Best case scenario: A-")
        else:
            print("Less than A")

        print("-------------------------------------------")
        print("-------------------------------------------")
    except:
        print(f"Final Score: {total_score:.2f}/{highest_score:.2f}")
        print("-------------------------------------------")
        print("-------------------------------------------")


