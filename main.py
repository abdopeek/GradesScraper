from sys import exit
from tools import *

username = input("Enter username: ")
password = input("Enter password: ")
enterUsername(username)
enterPassword(password)
student = get_student_id()
sections = get_sections(student)
sections = [{'sectionId': f"{id}"} for id in sections]
jsons = get_data(sections)
if jsons == "Error":
    print("Error occured")
    exit()
for json_data in jsons:
    processed = process(json_data['data'])
    json_data['data'] = processed
    print_output(json_data)

input("Press any key to exit")
exit()
