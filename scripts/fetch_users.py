
import os
import json

import pyworkflow.object as pwobj
import pyworkflow.utils as pwutils

from model.datasource.booking import BookingManager
from config import *



if __name__ == "__main__":
    # Assume the data folder is in the same place as this script
    dataFolder = os.path.join(os.path.dirname(__file__), '../data')
    # Load username and password for booked system
    t = pwutils.Timer()

    t.tic()
    bMan = BookingManager()
    bookedUserFn = getDataFile(BOOKED_LOGIN_USER)
    uJson = bMan.fetchUsersJson(bookedUserFn)
    bookedUsersListFn = getDataFile(BOOKED_USERS_LIST)
    with open(bookedUsersListFn, 'w') as usersFile:
        json.dump(uJson, usersFile, indent=2)

    t.toc()

    print 'Users: ', len(uJson['users'])

    # Fetch orders from the Portal
    # pMan = PortalManager('data/portal-api.json')
    #
    # accountsJson = pMan.fetchAccountsJson()
    # print "Accounts: ", len(accountsJson['items'])
    # accountsFile = open('data/test-portal-accounts.json', 'w')
    # json.dump(accountsJson, accountsFile, indent=2)
    # accountsFile.close()

