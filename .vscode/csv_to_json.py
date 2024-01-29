import csv
import json
import os

def csv_to_json(csv_file_path,json_file_path):
    json_array = []

    # read csv file
    with open(csv_file_path, encoding='utf-8') as csvf:
        # load csv file data using dictionary reader
        csv_reader = csv.DictReader(csvf)

        # convert each csv row into python dict
        for row in csv_reader:
            # add the dict to json array
            json_array.append(row)
    
    # convert python json_array to JSON string and write to json file
    with open(json_file_path, 'w', encoding='utf-8') as jsonf:
        json_string = json.dumps(json_array, indent=4)
        jsonf.write(json_string)

csv_files = ['action_type','game_version','players','property']
wd = "H:/Python/monopoly-companion-app/monopoly_companion/static/"

for file in csv_files:
    csv_to_json(wd + file + ".csv", wd + file + '.json')


