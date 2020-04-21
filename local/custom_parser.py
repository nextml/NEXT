import json

initMat_file = open('initMat.json')
initMat_arr = json.load(initMat_file)

for item in initMat_arr:
    targetId = item['targetId']
    feature = item['feature']

print("the end")
