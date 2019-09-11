import discord
import json
import os
import asyncio
import discord.utils
import requests
import datetime
import dateutil.parser

READY_STATUS = "Discord Bot now online!"

client = discord.Client()
dat = {
    "GetScoresAPI": "https://cvrescores.herokuapp.com/api/scores?access_token=iuzIoEccueRwNpUf1spQfnIA5Y4IVMZcoCcy0U5YLmNEv6bQ0RXfydx86ZR9EUj0",
    "Messages": [
        {
            "ServerName": "Collegiate VR Esports",
            "ChannelID": None,
            "ChannelName": "it-has-things",
            "Delay": 3600,
            "TopPlayers": 20,
            "AllowedMaps": [
                "Chikatto Chika Chika",
                "Koi no Hime Hime Pettanko",
                "Redo (TV Size)"
            ],
            "Header": "**Collegiate VR Esports Qualification Rankings!**```\n",
            "Format": "Rank: UserName | (School) | MostRecentSubmission",
            "Footer": "\n```"
        }
    ],
}

def createPlay(item):
    return {
        "mapName": item['mapName'],
        "score": item['score'],
        "accuracy": item['accuracy'],
        "time": item['time'],
        "averageCut": item['stats']['averageCutScore'],
    }

def createMessage(url, header, footer, formatStr, allowedMaps, playerCount):
    data = requests.get(url=url).json()
    users = {}
    teams = {}
    for item in data:
        if item['mapName'] in allowedMaps:
            if item['username'] not in users.keys():
                users[item['username']] = {
                    "team": item['team'],
                    "plays": [
                        createPlay(item)
                    ]
                }
            else:
                # Double check that only the best map scores are calculated
                replacedPlay = 0
                for existingItem in users[item['username']]['plays']:
                    if existingItem['mapName'] == item['mapName']:
                        # Compare accuracy, determine new best map
                        if item['score'] >= existingItem['score']:
                            # Replace old item
                            p = createPlay(item)
                            for k in existingItem.keys():
                                existingItem[k] = p[k]
                            replacedPlay = 1
                        replacedPlay = -1
                        break
                if replacedPlay == 0:
                    users[item['username']]['plays'].append(createPlay(item))
    for user in users.keys():
        users[user]['score'] = sum([s['score'] for s in users[user]['plays']])
        users[user]['mostRecent'] = max([dateutil.parser.parse(q['time']) for q in users[user]['plays']])
        users[user]['averageAccuracy'] = sum([s['accuracy'] for s in users[user]['plays']]) / float(len(users[user]['plays']))
    sorted_users = sorted(users, key=lambda u: -users[u]['score'])

    rankPad = max(len(str(min(playerCount, len(sorted_users)))), len("Rank"))
    userPad = max(len(max(sorted_users, key=len)), len("UserName"))
    teamPad = max(len(users[max(users, key=lambda k: len(users[k]['team']))]['team']), len("Team"))
    recentPad = 0
    averageAccPad = max(6, len("AverageAccuracy"))
    scorePad = max(len(str(users[max(users, key=lambda k: len(str(users[k]['score'])))]['score'])), len("Score"))
    playsPad = max(len(str(len(users[max(users, key=lambda k: len(str(users[k]['plays'])))]['plays']))), len("Plays"))

    modFormat = formatStr.replace("Rank", "Rank".ljust(rankPad, ' '))
    modFormat = modFormat.replace("UserName", "UserName".ljust(userPad, ' '))
    modFormat = modFormat.replace("Team", "Team".ljust(teamPad, ' '))
    modFormat = modFormat.replace("AverageAccuracy", "AverageAccuracy".ljust(averageAccPad, ' '))
    modFormat = modFormat.replace("Score", "Score".ljust(scorePad, ' '))
    modFormat = modFormat.replace("Plays", "Plays".ljust(playsPad, ' '))

    message = header + modFormat + "\n\n"
    for i in range(min(playerCount, len(sorted_users))):
        m = formatStr.replace("Rank", str(i + 1).ljust(rankPad, ' '))
        m = m.replace("UserName", sorted_users[i].ljust(userPad, ' '))
        m = m.replace("Team", (users[sorted_users[i]]['team']).ljust(teamPad, ' '))
        m = m.replace("MostRecentSubmission", users[sorted_users[i]]['mostRecent'].astimezone(dateutil.tz.tzutc()).strftime("%B %d, %H:%M:%S"))
        m = m.replace("AverageAccuracy", ("%.2f%%" % (100 * users[sorted_users[i]]['averageAccuracy'])).ljust(averageAccPad, ' '))
        m = m.replace("Score", ("%d" % users[sorted_users[i]]['score']).ljust(scorePad, ' '))
        m = m.replace("Plays", ("%d" % len(users[sorted_users[i]]['plays'])).ljust(playsPad, ' '))
        message += m + "\n"
    message += footer
    return message

def printMessage(message):
    print("Message Received from Author: (" + str(message.author) + ", " + str(message.author.id) + ") with content: " + message.content)

@client.event
async def on_ready():
    print("Logged into discord!")

async def background_loop(guild, channel, url, header, footer, formatString, allowedMaps, delay, topPlayers):
    await client.wait_until_ready()
    while not client.is_closed:
        await client.send_message(channel, createMessage(url, header, formatString, allowedMaps, topPlayers))
        await asyncio.sleep(delay)

if __name__ == "__main__":
    if not os.path.exists("settings.json"):
        with open("settings.json", 'w') as q:
            json.dump(dat, q, indent=4)
    with open("settings.json", "r") as q:
        dat = json.load(q)
    createMessage(dat['GetScoresAPI'], dat['Messages'][0]['Header'], dat['Messages'][0]['Footer'], dat['Messages'][0]['Format'], dat['Messages'][0]['AllowedMaps'], dat['Messages'][0]['TopPlayers'])
    with open("discord.key", "r") as f:
        client.run(f.readline())
        for item in dat['Messages']:
            guild = discord.utils.get(client.guilds, name=item['ServerName'])
            if 'ChannelName' in item.keys() and item['ChannelName']:
                channel = discord.utils.get(guild.channels, name=item['ChannelName'])
            else:
                channel = client.get_channel(item['ChannelID'])
            client.loop.create_task(background_loop(guild, channel, dat['GetScoresAPI'], item['Header'], item['Footer'], item['Format'], item['AllowedMaps'], item['Delay'], item['TopPlayers']))
