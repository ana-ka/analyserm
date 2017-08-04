import ast
import os
import time
from datetime import date, timedelta
import sys
import networkx as nx


os.system("cls")

# function to parse profile files


def parse_profile_data(UID):
    ID = ""
    state = ""
    name = ""
    age = ""
    status = ""
    contacts = []
    guests = []
    sane = True

    id_mismatch = 0
    unexpected_state = 0
    empty_name = 0
    malformed_age = 0
    unexpected_status = 0

    # get a file handle
    try:
        f = open(str(UID) + ".txt", 'r')
    except:
        print "Error: I/O error"
        sys.exit(0)

    # skim through the file
    # print "parsing profile " + str(UID) + "..."
    for line in f:

        # parse the ID line
        if line.startswith("ID:"):
            ID = int(line[line.rfind("\t")+len("\t"):line.rfind("\n")])
            # check if we got what we expected to get - otherwise clean up and run away
            if (UID != ID):
                print("\tError: UID mismatch (seen: " + str(ID) + ", expected: " + str(UID) + ")")
                sys.exit(0)

        # parse the state line
        if line.startswith("state:"):
            state = line[line.rfind("\t")+len("\t"):line.rfind("\n")]
            # check for rogue state strings, default them to invalid and notify the user
            if state not in ("valid", "barred", "deleted", "invalid", "inexistent"):
                print("\tError: unexpected state (" + state + '), defaulting to "invalid"')
                sane = False

        # parse the name line
        if line.startswith("name:"):
            name = line[line.rfind("\t")+len("\t"):line.rfind("\n")]
            # check for rogue name strings and notify the user
            if ((state in ("valid", "deleted")) and (name == "")):
                print("\tError: unexpected name (expected nonempty string for valid and deleted accounts)")

        # parse the age line
        if line.startswith("age:"):
            age = line[line.rfind("\t")+len("\t"):line.rfind("\n")]
            # if we can expect to find a usable age string...
            if state in ("valid") and (age != ""):
                # ...try to parse it to an integer...
                try:
                    age = int(age)
                # ...if we did not succeed, something is wrong. default age to -1 and notify the user
                except ValueError:
                    print('\tError: malformed age string (expected an integer), defaulting to -1')
                    age = int("-1")

        # parse the status line
        if line.startswith("status:"):
            status = line[line.rfind("\t")+len("\t"):line.rfind("\n")]
            # if the account is valid or deleted, we expect to find some sensible status
            if (((state in ("valid", "deleted")) and (status not in ("online", "offline", "invisible")))
                # otherwise, if the account is barred, invalid or inexistent, we do not expect to find a status
                or ((state in ("barred", "invalid", "inexistent")) and (status != ""))):
                # so if either one is the case regarless, we notify the user
                print("\tError: unexpected status string (" + status + "with state: " + state + ")")
                sane = False

        # parse the contacts line
        if line.startswith("contacts:"):
            substring = line[line.rfind("\t")+len("\t"):line.rfind("\n")]
            contacts = ast.literal_eval(substring)

        # parse the guests line
        if line.startswith("guests:"):
            substring = line[line.rfind("\t")+len("\t"):line.rfind("\n")]
            guests = ast.literal_eval(substring)

    # close the file, assemble the profile and return it
    f.close
    profile = state, name, age, status, contacts, guests
    return profile


# populate the profiles-database
profiles = {}
print "Populateing profiles database..."
for UID in range(1, 91401):
    profiles[UID] = parse_profile_data(UID)


# build a guestbook graph
print "Building guests graph..."
guests = nx.DiGraph()
for UID in profiles:
    # check if profile is valid
    if (profiles[UID][0] == "valid"):
        for guest in profiles[UID][5]:
            # check if we have the guest in our database
            if int(guest) in profiles:
                # check if guest is valid
                if (profiles[int(guest)][0] == "valid"):
                    # if all checks passed, add the edge
                    guests.add_edge(int(guest), int(UID))

# write the guestbook-digraph
f = open("rm-guests_noweight.gexf", "w")
nx.write_gexf(guests, f)
f.close


# build a contacts graph
print "Building contacts graph..."
contacts = nx.DiGraph()
for UID in profiles:
    # check if profile is valid
    if (profiles[UID][0] == "valid"):
        for contact in profiles[UID][4]:
            # check if we have the contact in our database
            if int(contact) in profiles:
                # check if contact is valid
                if (profiles[int(contact)][0] == "valid"):
                    # if all checks passed, add the edge
                    contacts.add_edge(int(contact), int(UID))

# write the contacts-digraph
f = open("rm-contacts_noweight.gexf", "w")
nx.write_gexf(contacts, f)
f.close
