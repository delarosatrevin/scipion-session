"""
This module contains classes and utility functions to deal with users
that can book the microscope and can start a session.
"""

import re
import datetime as dt
import json
import requests

import pyworkflow.utils as pwutis

from base import DataObject, parseCsv
from datasource.booking import BookingManager


CEM_REGEX = re.compile("(cem\d{5})")


class Reservation(DataObject):
    # List of attributes that will be set as UString
    ATTR_STR = ['username', 'resource', 'title', 'begin', 'end', 'reference',
                'userId', 'resourceId']

    def __init__(self, **kwargs):
        DataObject.__init__(self, **kwargs)
        # Lets check if this reservation is for a national project
        # by parsing the title and checking for a cemXXXXX code
        # both cem and CEM will be recognized
        t = self.title.get().lower()
        m = CEM_REGEX.search(t)
        self.cemCode = None if m is None else m.groups()[0]
        self._beginDate = self._getDate('begin')
        self._endDate = self._getDate('end')

    def _getDate(self, attrName):
        value = self.getAttributeValue(attrName)
        # Sample datetime: 2017-06-06T21:00:00+0000
        date, time = value.strip().split('T')
        year, month, day = date.split('-')
        hour = time.split(':')[0]
        return dt.datetime(year=int(year), month=int(month), day=int(day),
                           hour=int(hour))

    def beginDate(self):
        return self._beginDate

    def endDate(self):
        return self._endDate

    def getDuration(self):
        return self.endDate() - self.beginDate()

    def getTotalDays(self):
        """ Check the number of days (even partial) of the reservation. """
        d = self.getDuration()
        return d.days + (1 if d.seconds//3600 > 0 else 0)

    def _getDay(self, date):
        """ Return the datime without hour. """
        return dt.datetime(year=date.year, month=date.month, day=date.day)

    def isActiveToday(self):
        return self.isActiveOnDay(dt.datetime.now())

    def isActiveOnDay(self, date):
        day = self._getDay(date)
        return (self._getDay(self.beginDate()) <= day and
                self._getDay(self.endDate()) >= day)

    def isActiveOnMonth(self, month):
        return self.beginDate().month == month or self.endDate().month == month

    def startsOnDay(self, date):
        day = self._getDay(date)
        return self._getDay(self.beginDate()) == day

    def startsToday(self):
        return self.startsOnDay(dt.datetime.now())

    def getCemCode(self):
        return self.cemCode

    def isNationalFacility(self):
        return self.getCemCode() is not None


def loadReservations(userJsonFn, reservationsJsonFn, fromDate, toDate):
    """ Load reservation list either from the booking system or from a
    local json file with cached data.
    Params:
        userJsonFn: user credentials to login into the booking system
        reservationsJsonFile: local file to use in case the reservations can
        not be load from the booking system.
        fromDate-toDate: date range to retrieve reservations
    """
    try:
        bMan = BookingManager()
        print "Loading reservations from booking system..."

        t = pwutis.Timer()
        t.tic()
        reservationsJson = bMan.fetchReservationsJson(userJsonFn,
                                                      fromDate, toDate)
        if reservationsJson is None:
            raise Exception("Could not fetch data from the booking system.")
        t.toc()
        with open(reservationsJsonFn, 'w') as reservationsFile:
            json.dump(reservationsJson, reservationsFile)
    except Exception, ex:
        print "Error: ", ex
        print "Trying to load reservations from file:", reservationsJsonFn
        jsonFile = open(reservationsJsonFn)
        reservationsJson = json.load(jsonFile)
        jsonFile.close()

    return loadReservationsFromJson(reservationsJson)


def loadReservationsFromFile(reservationsJsonFile):
    """ Load a list of order objects from a given json file.
        """
    dataFile = open(reservationsJsonFile)
    reservations = loadReservationsFromJson(json.load(dataFile))
    dataFile.close()
    return reservations


def loadReservationsFromJson(dataJson):
    reservations = []

    for item in dataJson['reservations']:
        # Remove weird code form the name part
        username = '%s %s' % (item['firstName'], item['lastName'])
        reservations.append(Reservation(username=username,
                                        resource=item['resourceName'],
                                        resourceId=item['resourceId'],
                                        title=item['title'],
                                        begin=item['startDate'],
                                        end=item['endDate'],
                                        reference=item['referenceNumber'],
                                        userId=item['userId']
                                        ))
    return reservations
