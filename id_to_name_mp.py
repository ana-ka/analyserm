import os
import time
from datetime import date, timedelta
import threading
import sys

import socks
import socket

import gzip
from StringIO import StringIO

from collections import deque

os.system("cls")

#  setup the networkstuff to use our local tor-proxy
proxyaddr = "127.0.0.1"
proxyport = 9050
socks.set_default_proxy(socks.SOCKS5, proxyaddr, proxyport)
#  monkeypatch socket
socket.socket = socks.socksocket
import urllib2

baseurl = "http://www.readmore.de/users/"
#  userIDs = [4157, 8177, 12627, 14900, 91000, 92000, 7650, 27035]

id_to_name = {}
queue = deque(range(92000))
lock = threading.Lock()


#  function to cope with guestbooks
#  takes a UID and the number of guestbookpages, returns a list of guests
def guestbook_handler(UID, username, number_of_guest_pages):
    guests = []
    for guest_page in range(1, number_of_guest_pages+1):
        #  try to retrieve the page
        success = False
        retrieved = ""
        content = ""
        while (not success):
            try:
                #  assemble the request
                request = urllib2.Request(baseurl + str(UID) + "-" + username.lower() + "&comment_page=" + str(guest_page) + "# comments")
                #  tell the site that we understand gzip
                request.add_header('Accept-encoding', 'gzip')
                #  see what we get
                response = urllib2.urlopen(request)
                #  check if we indeed have to deal with gzip
                if response.info().get('Content-Encoding') == 'gzip':
                    buf = StringIO(response.read())
                    f = gzip.GzipFile(fileobj=buf)
                    content = f.read()
                success = True
            # catch nasty excetions
            except (KeyboardInterrupt):
                raise
            except:
                print "\b" * 80 + "Error retrieving guest_page " + str(UID),
                print sys.exc_info()[0]
                time.sleep(30)

        # finally slice the content into lines
        content = content.split("\n")
        for idx, line in enumerate(content):
            if line.startswith('<div class="comment_avatar">'):
                ID = content[idx+1][content[idx+1].find('<a href="http://www.readmore.de/users/')+len('<a href="http://www.readmore.de/users/'):content[idx+1].find('-')]
                guests.append(ID)

    return guests


# function to parse a profile page
# takes a UID, returns a profile
def parse_profile(UID):

    # try to retrieve the page
    success = False
    retrieved = ""
    content = ""
    while (not success):
        try:

            # assemble the request
            request = urllib2.Request(baseurl + str(UID))
            # tell the site that we understand gzip
            request.add_header('Accept-encoding', 'gzip')
            # see what we get
            response = urllib2.urlopen(request)
            # check if we indeed have to deal with gzip
            if response.info().get('Content-Encoding') == 'gzip':
                buf = StringIO(response.read())
                f = gzip.GzipFile(fileobj=buf)
                content = f.read()
            # add our timesamp
            retrieved = (time.strftime("%d") + "." + time.strftime("%m") + "." + time.strftime("%Y") +
            " " + time.strftime("%H") + ":" + time.strftime("%M") + ":" + time.strftime("%S"))
            success = True
        # catch nasty excetions
        except (KeyboardInterrupt):
            raise
        except:
            print "\b" * 80 + "Error retrieving profile " + str(UID),
            time.sleep(30)

    # finally slice the content into lines
    original_content = content
    content = content.split("\n")

    # the things we look for
    account_state = ""
    username = ""
    age = ""
    status = ""
    status_set = False
    last_online = ""
    registered_since = ""
    reg_set = False
    last_update = ""
    update_set = False

    comments = 0
    forum_entries = 0
    contacts = []
    guests = []

    # parse the damn html-code...the ugly way
    for idx, line in enumerate(content):

        # get the username
        if line.startswith("<title>Benutzer: "):
            username = line[line.find("<title>Benutzer: ") + len("<title>Benutzer: "):line.find(" &laquo; readmore.de</title>")]

            # check account state based on username
            if (username == ""):
                account_state = "invalid"
                continue
            if (username == "Account deleted"):
                account_state = "deleted"
                continue
            else:
                account_state = "valid"
                continue
        if line.startswith("Der ausgew&auml;hlte Account wurde von einem Admin gesperrt."):
            account_state = "barred"
            continue
        if line.startswith("Dieses Profil existiert nicht oder wurde gel&ouml;scht."):
            account_state = "inexistent"
            continue

        # get the age
        if line.startswith("Name: <span>"):
            age = line[line.find("<br/>	Alter: <span>") + len("<br/>	Alter: <span>"):line.find(" Jahre</span><br/>")]
            continue
        if line.startswith("Alter: <span>"):
            age = line[line.find("Alter: <span>") + len("Alter: <span>"):line.find(" Jahre</span><br/>")]
            continue

        # get the status
        if (line.startswith("Status: ") and not status_set):
            status = line[line.find("<span>")+len("<span>"):line.find("</span>")]
            status_set = True
            # user is online...easy task
            if status.startswith("online"):
                status = "online"
                last_online = retrieved[:-3]
                continue
            # user is invisible...also quite easy
            if status.startswith("unsichtbar"):
                status = "invisible"
                last_online = "unknown"
                continue
            else:
                # user is offline...in which case we have to cope with the last online date...meh
                status = "offline"
                lo_string = line[line.find("(zuletzt online <strong>")+len("(zuletzt online <strong>"):line.find("</strong>,")]
                # no last online date recorded (old accounts?)
                if (lo_string == ""):
                    last_online = "unknown"
                    continue
                # last seen today. get todays date, append recorded time
                if (lo_string == "heute"):
                    lo_date = time.strftime("%d") + "." + time.strftime("%m") + "." + time.strftime("%Y")
                    lo_time = line[line.find("</strong>, ")+len("</strong>, "):line.find(" Uhr)</span>")]
                    last_online = lo_date + " " + lo_time
                    continue
                # last seen yesterday. compute yesterdays date, append recorded time
                if (lo_string == "gestern"):
                    yesterday = date.today() - timedelta(1)
                    lo_date = yesterday.strftime("%d") + "." + yesterday.strftime("%m") + "." + yesterday.strftime("%Y")
                    lo_time = line[line.find("</strong>, ")+len("</strong>, "):line.find(" Uhr)</span>")]
                    last_online = lo_date + " " + lo_time
                    continue
                else:
                    # last seen at any other time. parse the date as is
                    if (username != "Account deleted"):
                        if ("zuletzt online") in line:
                            lo_date = line[line.find("(zuletzt online ")+len("(zuletzt online "):line.find(", ")]
                            lo_time = line[line.find(", ")+len(", "):line.find(" Uhr")]
                            last_online = lo_date + " " + lo_time
                        else:
                            last_online = "unknown"
                            continue

        # get the registrationdate
        if (line.startswith("Registriert seit: ") and not reg_set):
            registered_since = line[line.find("<span>")+len("<span>"):line.find("</span>")]
            reg_set = True

        # get the last_update date
        if (line.startswith("Letztes Profilupdate: ") and not update_set):
            last_update = line[line.find("<span>")+len("<span>"):line.find("</span>")]
            profileupdate_set = True

        # get the total comment count
        if line.startswith('<hr/>	<h3 class="mod">Kommentare '):
            comments = line[line.find("<span>(")+len("<span>("):line.find(" insgesamt")]

        # get the total number of forum entries
        if line.startswith('<hr/>	<h3 class="mod">Forenbeitr'):
            forum_entries = line[line.find("<span>(")+len("<span>("):line.find(" insgesamt")]

    # find the contact section
    if (account_state not in ["barred", "inexistent"]):
        contact_start = original_content[original_content.find('<h3 class="mod">Kontakte</h3>') + len('<h3 class="mod">Kontakte</h3>'):]
        contact_section = contact_start[:contact_start.find("</ul>")]
        contact_section = contact_section.split("\n")
        # get the contacts
        for idx, line in enumerate(contact_section):
            if ("http://www.readmore.de/users/" in line):
                contact_id = line[line.rfind("http://www.readmore.de/users/")+len("http://www.readmore.de/users/"):]
                contact_id = contact_id[:contact_id.find("-")]
                contacts.append(contact_id)

    # find the guestbook section
    if (account_state not in ["barred", "inexistent"]):
        number_of_guest_pages = 1
        guest_page_counter = original_content[original_content.find('<h3>G&auml;stebuch</h3>') + len('<h3>G&auml;stebuch</h3>'):
                                           original_content.find('<a name="post_comment"></a>')]
        # find the number of comment pages
        # check if there is any comment-section at all
        if (guest_page_counter != ""):
            # determine the number of guestpages
            guest_page_counter = guest_page_counter.split("\n")
            for line in guest_page_counter:
                if ('<li class=""><a href="/users/' + str(UID) + "-" + username.lower() + '&comment_page=') in line:
                    number = line[line.find('<li class=""><a href="/users/' + str(UID) + "-" + username.lower() + '&comment_page=') +
                                  + len('<li class=""><a href="/users/' + str(UID) + "-" + username.lower() + '&comment_page=')
                                  :line.find('# comments"')]
                    if (number > number_of_guest_pages):
                                  number_of_guest_pages = int(number)
            guests = guestbook_handler(UID, username, number_of_guest_pages)

    # assemble the profile and return it
    profile = account_state, username, age, status, last_online, registered_since, last_update, comments, forum_entries, contacts, guests, retrieved
    return profile


# write recorded profiledate for the specified UID
def write_profile(UID):
    f = open(str(UID) + ".txt", "w")
    f.write("ID:\t\t" + str(UID) + "\n")
    f.write("state:\t\t" + profiles[UID][0] + "\n")
    f.write("name:\t\t" + profiles[UID][1] + "\n")
    f.write("age:\t\t" + profiles[UID][2] + "\n")
    f.write("status:\t\t" + profiles[UID][3] + "\n")
    f.write("last online\t" + profiles[UID][4] + "\n")
    f.write("created:\t" + profiles[UID][5] + "\n")
    f.write("updated:\t" + profiles[UID][6] + "\n")
    f.write("comments:\t" + str(profiles[UID][7]) + "\n")
    f.write("forum entries:\t" + str(profiles[UID][8]) + "\n")
    f.write("contacts:\t" + str(profiles[UID][9]) + "\n")
    f.write("guests:\t\t" + str(profiles[UID][10]) + "\n")
    f.write("data acquired:\t" + profiles[UID][11] + "\n")
    f.close


profiles = {}
# for UID in userIDs:
for UID in range(1, 92000):
    profiles[UID] = parse_profile(UID)
    print "ID:\t\t" + str(UID)
    print "state:\t\t" + profiles[UID][0]
    print "name:\t\t" + profiles[UID][1]
    print "specified age:\t" + profiles[UID][2]
    print "status:\t\t" + profiles[UID][3]
    print "last online:\t" + profiles[UID][4]
    print "created:\t" + profiles[UID][5]
    print "updated:\t" + profiles[UID][6]
    print "comments:\t" + str(profiles[UID][7])
    print "forum entries:\t" + str(profiles[UID][8])
    print "contacts:\t" + str(profiles[UID][9])
    print "guests:\t\t" + str(profiles[UID][10])
    print "data acquired:\t" + profiles[UID][11]
    print "\n"
    write_profile(UID)
