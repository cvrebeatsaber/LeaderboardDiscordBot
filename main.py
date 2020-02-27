import discord
import json
import os
import asyncio
import discord.utils
import requests
import datetime
import dateutil.parser
from functions import *

READY_STATUS = "Discord Bot now online!"

client = discord.Client()
dat = {
    "GetScoresAPI": "https://cvrescores.herokuapp.com/api/scores?access_token=iuzIoEccueRwNpUf1spQfnIA5Y4IVMZcoCcy0U5YLmNEv6bQ0RXfydx86ZR9EUj0",
    "Delay": 3600,
    "Messages": [
        {
            "ServerName": "BOT",
            "ChannelID": None,
            "ChannelName": "general",
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

savedScoreMessages = {}
guilds = []

def createPlay(item):
    return {
        "mapName": item['mapName'],
        "difficulty": item['difficulty'],
        "levelId": item['levelId'],
        "score": item['score'],
        "accuracy": item['accuracy'],
        "time": item['time'],
        "averageCut": item['stats']['averageCutScore'] if 'stats' in item.keys() and 'averageCutScore' in item['stats'].keys() else -1,
    }

def createMessage(url, messageArg):
    allowedMaps = messageArg['AllowedMaps']
    playerCount = messageArg['TopPlayers']
    header = messageArg['Header']
    footer = messageArg['Footer']
    formatStr = messageArg['Format']

    data = requests.get(url=url).json()
    with open("data.json", 'w') as f:
        json.dump(data, f)
    users = {}
    for item in data:
        mapAllowed = False
        for m in allowedMaps.keys():
            if item['levelId'].startswith(m) and item['difficulty'] == allowedMaps[m]:
                mapAllowed = True
                break
        if mapAllowed:
            if item['username'] not in users.keys():
                users[item['username']] = {
                    "team": item['team'] if "team" in item.keys() else "",
                    "plays": [
                        createPlay(item)
                    ]
                }
            else:
                # Double check that only the best map scores are calculated
                replacedPlay = 0
                for existingItem in users[item['username']]['plays']:
                    if existingItem['mapName'] == item['mapName'] and existingItem['levelId'] in item['levelId'] and existingItem['difficulty'] == item['difficulty']:
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
    with open("users.json", 'w') as f:
        json.dump(users, f)
    if len(users) == 0:
        # No users have completed any scores for accepted maps!
        message = "```\nNo users have completed any scores for any qualifier maps!\nQualifier map IDs:\n"
        message += "\n".join(allowedMaps) + "```"
        return [message]
    for user in users.keys():
        users[user]['score'] = sum([s['score'] for s in users[user]['plays']])
        users[user]['mostRecent'] = max([dateutil.parser.parse(q['time']) for q in users[user]['plays']])
        users[user]['AverageAccuracy'] = sum([s['accuracy'] for s in users[user]['plays']]) / float(len(users[user]['plays']))
    sorted_users = sorted(users, key=lambda u: -users[u]['score'])
    print("Dumping sorted users to JSON!")
    with open("sorted_users.json", 'w') as f:
        json.dump(sorted_users, f)
    count = min(playerCount, len(sorted_users))

    tableHeader = formatStr

    for item in messageArg['FormatConversion']:
        if item['PadOption'] == "Normal":
            item['Pad'] = max(max([len(item['Function'](users, sorted_users, i)) for i in range(count)]), len(item['Replacement']))
            if item['Name'] == "Rank":
                item['Pad'] = max(len(str(count)), len("Rank"))
            tableHeader = tableHeader.replace(item['Replacement'], item['Replacement'].ljust(item['Pad'], ' '))
    message = header + tableHeader + "\n"
    mes = []
    for i in range(count):
        m = formatStr
        for item in messageArg['FormatConversion']:
            v = item['Function'](users, sorted_users, i)
            if item['PadOption'] == "Normal":
                v = v.ljust(item['Pad'], ' ')
            m = m.replace(item['Replacement'], v)
        if len(message) + len(m) + 4 > 1000:
            mes.append(message + "\n```")
            message = "```"
        message += m + "\n"

    message += footer
    message += "\n" + messageArg["SpecialMessage"]
    mes.append(message)
    return mes

@client.event
async def on_ready():
    print("Logged into discord!")

@client.event
async def on_message(message):
    try:
        print(str(message.author.id) + ": " + str(message.content))
    except:
        print("message content unprintable!")
    if str(message.author.id) in ids:
        # sudo
        if message.content.startswith("killNow"):
            # Kill
            # for m in savedScoreMessages.values():
            #     await m.delete()
            try:
                await message.delete()
            except:
                # Perms
                pass
            print("Killing self!")
            await client.logout()
        elif message.content.startswith("goNow"):
            # Go now
            try:
                await message.delete()
            except:
                # Perms
                pass
            await sendNow()

async def getChannel(item):
    guild = discord.utils.get(guilds, name=item['ServerName'])
    if not guild:
        return None
    chns = await guild.fetch_channels()
    if item['ChannelName']:
        return discord.utils.get(chns, name=item['ChannelName'])
    else:
        return client.get_channel(item['ChannelID'])

async def sendNow():
    for item in dat['Messages']:
        channel = await getChannel(item)
        if not channel:
            continue
        if channel.id in savedScoreMessages.keys():
            # Get message
            print("Deleteing: " + str(len(savedScoreMessages[channel.id])) + " messages!")
            for di in range(len(savedScoreMessages[channel.id])):
                try:
                    await savedScoreMessages[channel.id][0].delete()
                    del(savedScoreMessages[channel.id][0])
                except discord.errors.NotFound:
                    del(savedScoreMessages[channel.id][0])
        for q in createMessage(dat['GetScoresAPI'], item):
            msg = await channel.send(q)
            if channel.id not in savedScoreMessages.keys():
                savedScoreMessages[channel.id] = []
            savedScoreMessages[channel.id].append(msg)

async def checkExistingMessages():
    for item in dat['Messages']:
        channel = await getChannel(item)
        if not channel:
            continue
        async for message in channel.history():
            if message.author == client.user:
                if channel.id not in savedScoreMessages.keys():
                    savedScoreMessages[channel.id] = []
                savedScoreMessages[channel.id].append(message)
        
async def background_loop():
    global guilds
    print("Entering background loop!")
    await client.wait_until_ready()
    guilds = await client.fetch_guilds().flatten()
    await asyncio.sleep(2)
    print("Got guilds")
    while True:
        print("Checking existing messages")
        await checkExistingMessages()
        print("Batch sending messages: " + str(len(dat['Messages'])))
        await sendNow()
        await asyncio.sleep(dat['Delay'])
    print("EXITING FOR SOME REASON!")

if __name__ == "__main__":
    if not os.path.exists("settings.json"):
        with open("settings.json", 'w') as q:
            json.dump(dat, q, indent=4)
    with open("settings.json", "r") as q:
        dat = json.load(q)
    for item in dat['Messages']:
        for f in item['FormatConversion']:
            if f['Name'] == "Rank":
                f['Function'] = getRank
            elif f['Name'] == "UserName":
                f['Function'] = getUserName
            elif f['Name'] == "Team":
                f['Function'] = getTeam
            elif f['Name'] == "Most Recently Played":
                f['Function'] = getMostRecent
            elif f['Name'] == "Average Accuracy":
                f['Function'] = getAvgAcc
            elif f['Name'] == "Score":
                f['Function'] = getScore
            elif f['Name'] == "Plays":
                f['Function'] = getPlays
            else:
                raise Exception("Unsupported format for object: " + str(f))
    # createMessage(dat['GetScoresAPI'], dat['Messages'][0]['Header'], dat['Messages'][0]['Footer'], dat['Messages'][0]['Format'], dat['Messages'][0]['AllowedMaps'], dat['Messages'][0]['TopPlayers'])
    if os.path.exists("powerUsers"):
        with open("powerUsers", "r") as q:
            ids = [item.strip() for item in q.readlines()]
    with open("discord.key", "r") as f:
        client.loop.create_task(background_loop())
        client.run(f.readline())
