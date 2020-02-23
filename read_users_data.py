import json

allowedMaps = {
    "custom_level_D0B25B0B05C7B14C5EA55774D1F751705F360026": 3,
    "custom_level_AB36FD22C1060AC3696AF0CD6BD1E25DB3AEBF18": 9,
    "custom_level_B3BD1BBBB18A53381E183EEADF78CCC5E523F07D": 9
}

def make_play(username, plays):
    return {
        "user": user,
        "score": sum([p['score'] for p in plays])
    }

with open("sorted_users.json", 'r') as f:
    sorted_users = json.load(f)

sorted_users = sorted_users[:16]

schools = {}

with open("users.json", 'r') as f:
    data = json.load(f)
    for user in data.keys():
        if user in sorted_users:
            continue
        item = data[user]
        if item['team'] not in schools.keys():
            schools[item['team']] = {
                "score": 0,
                "plays": []
            }
        p = make_play(user, item['plays'])
        
        if len(schools[item['team']]['plays']) == 2:
            minIndex = 0
            for i in range(len(schools[item['team']]['plays'])):
                if schools[item['team']]['plays'][minIndex]['score'] > schools[item['team']]['plays'][i]['score']:
                    minIndex = i
            schools[item['team']]['score'] -= schools[item['team']]['plays'][minIndex]['score']
            schools[item['team']]['plays'][minIndex] = p
            schools[item['team']]['score'] += p['score']
        else:
            schools[item['team']]['plays'].append(p)
            schools[item['team']]['score'] += p['score']
    with open("schools.json", 'w') as q:
        json.dump(schools, q, indent=4)

sorted_schools = sorted(schools, key=lambda item: -schools[item]["score"])
rank = 1
for item in sorted_schools:
    if len(schools[item]['plays']) != 2:
        print("Skipping team: " + str(item) + " because they do not have 2 players!")
    # print(str(rank) + ": " + item + " Score: " + str(schools[item]['score']))
    print(item)
    rank += 1

print("Complete!")