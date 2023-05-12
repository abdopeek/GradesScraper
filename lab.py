from selenium import webdriver  # use it to open the actual browser for cookies
from selenium.webdriver.edge.service import Service  
from selenium.webdriver.common.keys import Keys  # to use a keyboard
from selenium.webdriver.common.by import By  # to locate element
import requests  # to work with requests instead of selenium
from utils import head  # header variable
import json  # work with the return from the website
from time import sleep  # sleep


ser = Service(Driver_location)
op = webdriver.EdgeOptions()
op.add_argument('headless')
op.add_experimental_option('excludeSwitches', ['enable-logging'])
# op.add_experimental_option('detach', True)
driver = webdriver.Edge(service=ser, options=op)
driver.minimize_window()
driver.get("https://upeisis.uofcanada.edu.eg/PowerCampusSelfService/Grades/GradeReport")
sleep(2)

def set_cookies(s, cookies):
    default = ['messagesUtk=50c6732c976448b3abbeadcea96c0180', '', '']
    for cookie in cookies:
        updated = f"{cookie['name']}={cookie['value']}"
        if cookie['name'] == "SelfService":
            default[2] = updated
        elif cookie['name'] == "ASP.NET_SessionId":
            default[1] = updated
    head['cookie'] = ';'.join(default)




def enterUsername(username):
    search = driver.find_element(By.XPATH, '//*[@id="txtUserName"]')
    search.send_keys(username)
    search.send_keys(Keys.RETURN)


def enterPassword(password):
    sleep(0.5)
    search = driver.find_element(By.XPATH, '//*[@id="txtPassword"]')
    search.send_keys(password)
    search.send_keys(Keys.RETURN)


def get_data():
    grade_link = 'https://upeisis.uofcanada.edu.eg/PowerCampusSelfService/Students/ActivityGrades'

    param = [{"sectionId": "4965"}, {"sectionId": "5120"}, {"sectionId": "5014"}, {"sectionId": "5034"}]  # hard code course id's
    s = requests.Session()
    sleep(1.5)  # wait for cookies to load in
    cookies = driver.get_cookies()
    set_cookies(s, cookies)
    outputs = []
    for section in param:
        resp = s.post(grade_link, data=json.dumps(section), headers=head)
        if resp.status_code == 200:  # accepted
            resp = resp.json()
        else:
            return "Error"
        json_value = json.loads(resp)['data']
        output = {
            'name': json_value['sectionName'],
            'data': json_value
        }
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
    print(f"\t\t{name}\t\t")
    for assignment in assignments:
        print(f"{assignment['description']}")
        for sub_assignment in assignment['studentAssignments']:
            if sub_assignment['isEarned']:
                total_score += float(sub_assignment['earnedPoints'])
                highest_score += float(sub_assignment['possiblePoints'])
                print(f"\t{sub_assignment['title']}\t\t{sub_assignment['earnedPoints']}/{sub_assignment['possiblePoints']}")
            else:
                print(f"\t{sub_assignment['title']}\t\tNot earned yet/{sub_assignment['possiblePoints']}")
    percentage = total_score / highest_score * 100
    print(f"Final Score: {total_score:.2f}/{highest_score:.2f} | %{percentage:.2f}")
    print("-------------------------------------------")
    print("-------------------------------------------")


def main():
    enterUsername(USERNAME)
    enterPassword(PASSWORD)
    jsons = get_data()
    if jsons == "Error":
        return "Error"
    for json_data in jsons:
        processed = process(json_data['data'])
        json_data['data'] = processed
        print_output(json_data)
main()
