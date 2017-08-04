import socks
import socket
import datetime
import networkx as nx
import os
from collections import deque
from decimal import *

os.system("cls")

# proxyconfig
proxyaddr = "127.0.0.1"
proxyport = 9050
socks.set_default_proxy(socks.SOCKS5, proxyaddr, proxyport)
socket.socket = socks.socksocket
import urllib2

# set up
baseurl = "http://www.readmore.de/users/"
# where to start?
userIDs = ["8177"]

# how many guestbooks to look at?
maxIDs = 500
# how often does an ID have to occur for us to actually use the accountname
importance_limit = 5
# the queues we need
queuedIDs = deque()
processedIDs = deque()
# the dicctionary for the ID->accountname mapping
ID_to_name = {}
# the communitygraph
community = nx.MultiDiGraph()


# gets us all guests along with their accountnames
def getEntries(ID):
    ID_to_name = {}
    guests = []
    name = ""
    content = (urllib2.urlopen("http://www.readmore.de/users/" + ID).read())
    content = content.split("\n")
    # check for multipage guestbook
    for idx, line in enumerate(content):
        pass

    for idx, line in enumerate(content):
        if line.startswith('<div class="comment_avatar">'):
            ID = content[idx+1][content[idx+1].find('<a href="http://www.readmore.de/users/')+len('<a href="http://www.readmore.de/users/'):
                                 content[idx+1].find('-')]
            # this is shitty but needed to get real accoutnames
            """content2 = (urllib2.urlopen("http://www.readmore.de/users/" + ID).read())
            for line in content2.split("\n"):
                if line.startswith("<title>Benutzer: "):
                    name = line[line.find("<title>Benutzer: ") + len("<title>Benutzer: "):line.find(" &laquo; readmore.de</title>")]"""
            name = content[idx+1][content[idx+1].find('-')+1:
                                 content[idx+1].rfind('">')]
            ID_to_name[int(ID)] = name
            guests.append(ID)
    return guests, ID_to_name


# writes the graph
def writeCommunityGraph(G, root):
    f = open(root + ".gexf", "w")
    nx.write_gexf(G, f)
    f.close


for userID in userIDs:
    queuedIDs.append(userID)

while ((len(queuedIDs) > 0 and len(processedIDs) < maxIDs)):
    current = queuedIDs.popleft()
    print "\b"*80 + "> Processing guestbook of " + current + ", [" + str(len(processedIDs)) + "/" + str(maxIDs) + "]",
    guests, mapping = getEntries(current)
    ID_to_name.update(mapping)
    for guest in guests:
        if (guest not in processedIDs):
            queuedIDs.append(guest)
            community.add_edge(int(guest), int(current))
    processedIDs.append(current)

print "\n\t>> done"
print "> postprocessing the graph..."
for ID in ID_to_name:
    if (nx.degree(community, int(ID)) < importance_limit):
        ID_to_name[ID] = str(ID)

nx.relabel_nodes(community, ID_to_name, copy=False)
print "\t>> done\n"
root = userIDs.pop()
writeCommunityGraph(community, root)
