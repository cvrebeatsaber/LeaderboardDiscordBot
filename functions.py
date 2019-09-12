# Format functions (all ret string)
import dateutil.tz

# GetRank replacement
def getRank(users, sorted_users, i):
    return str(i + 1)

# GetUserName replacement
def getUserName(users, sorted_users, i):
    return sorted_users[i]

# GetTeam replacement
def getTeam(users, sorted_users, i):
    return users[sorted_users[i]]['team']

# GetMostRecent replacement
def getMostRecent(users, sorted_users, i):
    return users[sorted_users[i]]['mostRecent'].astimezone(dateutil.tz.tzutc()).strftime("%B %d, %H:%M:%S")

# GetAvgAcc replacement
def getAvgAcc(users, sorted_users, i):
    return "%.2f%%" % (100 * users[sorted_users[i]]['AverageAccuracy'])

# GetScore replacement
def getScore(users, sorted_users, i):
    return "%d" % users[sorted_users[i]]['score']

# GetPlays replacement
def getPlays(users, sorted_users, i):
    return "%d" % len(users[sorted_users[i]]['plays'])