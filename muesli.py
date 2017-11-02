# -*- coding: utf-8 -*-
"""
Created on Sun Oct 22 16:01:37 2017

@author: chris
"""

import json
from bs4 import BeautifulSoup
import re
import requests
import sys

from copy import deepcopy

from student import Student
from util import Cipher

#==============================================================================

class MuesliAcc:
    
    def __init__ (self, mail, passw):
        self.__mail = mail
        self.__passw = passw
        
    @property
    def mail(self):
        return self.__mail
    
    @property
    def passw(self):
        return self.__passw
    
    def toDict(self, key : str = "mymueslikey"):
        with Cipher(key) as c:
            d = dict()
            d['ID'] = Cipher.invert(key)
            d['Usern'] = c.encode(self.__mail)
            d['Passw'] = c.encode(self.__passw)
            return d

    @staticmethod
    def fromDict(d : dict):
        with Cipher(Cipher.invert(d['ID'])) as c:
            return MuesliAcc(c.decode(d['Usern']), c.decode(d['Passw']))
    
    @staticmethod
    def fromJsonString(jsonStr):
        return MuesliAcc.fromDict(json.loads(jsonStr))
    
    @staticmethod
    def fromJsonFp(fp):
        return MuesliAcc.fromDict(json.load(fp))
        
#==============================================================================
        
class Tutorial:
    
    def __init__(self, subject, day, time, room = 'Unknown'\
                 , url = None, tutor = None, state = 'OWNED'):
        self.__attrs = dict()
        self.__attrs['Day']     = day
        self.__attrs['Time']    = time
        self.__attrs['Room'] = room
        self.__attrs['URL']     = url
        self.__attrs['Subject'] = subject
        self.__attrs['Tutor'] = tutor
        self.__attrs['State'] = state
        
    #--------------------------------------------------------------------------
    
    @property
    def day(self):
        return self.__attrs['Day']
    
    @property
    def time(self):
        return self.__attrs['Time']
    
    @property
    def room(self):
        return self.__attrs['Room']
    
    @property
    def url(self):
        return self.__attrs['URL']
    
    @url.setter
    def url(self, url):
        self.__attrs['URL'] = url
    
    @property
    def subject(self):
        return self.__attrs['Subject']
    
    @property
    def tutor(self):
        return self.__attrs['Tutor']
    
    @property
    def state(self):
        return self.__attrs['State']
    
    #--------------------------------------------------------------------------  
    
    def toJsonString(self):
        return json.dumps(self.__attrs, sort_keys = True, indent = 4)
    
    def toJsonFile(self, fname):
        with open(fname, 'r', encoding = 'UTF-8') as fp:
            json.dump(fp, self.__attrs)
            
    def toDict(self):
        return deepcopy(self.__attrs)
    
    #--------------------------------------------------------------------------
    
    @staticmethod
    def fromDict(d : dict):
        return Tutorial(d['Subject'], d['Day'], d['Time'], d['Room']\
                        , d['URL'], d['Tutor'], d['State'])
        
        
#==============================================================================

class Muesli:
    
    def __init__ (self, acc : MuesliAcc):
        self.__acc = acc
        self.baseURL = 'https://muesli.mathi.uni-heidelberg.de'
        self.session = None
        self.curURL = None
    
    #--------------------------------------------------------------------------
    
    def login (self):
        print('MÜSLI - login()')
        self.session = requests.Session()
        website = self.baseURL + "/user/login"
        r = self.session.post(website, data = dict(email = self.__acc.mail, password = self.__acc.passw))
        if r.url == website or r.status_code != requests.codes.ok:
            raise RuntimeError('Login failed! - Check ur internet connection, username and password')
        self.curURL = str(r.url)

    def logout (self):
        print('MÜSLI - logout')
        website = self.baseURL + '/user/logout'
        resultWeb = "https://muesli.mathi.uni-heidelberg.de/"
        r = self.session.post(website)
        self.session.close()
        self.session = None

        if r.url != resultWeb or r.status_code != requests.codes.ok:
            raise RuntimeError('Logout Failed - Session was closed!')
    
    #--------------------------------------------------------------------------
    
    def __enter__ (self):
        self.login()
        return self
        
    def __exit__ (self, type, value, traceback):
        self.logout()
        
    #--------------------------------------------------------------------------
    
    def __extractTutorialInfo (self, tutoralLink):
        r = self.session.post(tutoralLink)
        soup = BeautifulSoup(r.text, 'html.parser')
        headers = soup.findAll("h2")
        pattern = re.compile("Übungsgruppe .*")

        result = {}
        days = {"Mo" : "Montag",
                "Di" : "Dienstag",
                "Mi" : "Mittwoch",
                "Do" : "Donnerstag",
                "Fr" : "Freitag",
                "Sa" : "Samstag",
                "So" : "Sonntag"}

        """
            The header looks like:
                
            Übungsgruppe zur 
              Vorlesung Einführung in die praktische Informatik
             am Mo 16:00 (SR B128, Mathematikon B, Berliner Straße 43)
        """

        result["Tutor"] = soup.find("p").text.split(':')[1].strip()

        for header in headers:
            if pattern.match(header.text):
                words = header.text.split(' ')
                for i in range(0, len(words)):
                    if "Vorlesung" == words[i]:
                        result["Subject"] = ' '.join(words[i + 1:]).split('\n')[0]

                    elif "am" == words[i]:
                        result["Day"] = days[words[i + 1]]
                        result["Time"] = words[i + 2]

                    elif re.compile("\(.*SR.*").match(words[i]):
                        result["Place"] = ' '.join(words[i:]).strip()[1:-1]

        return Tutorial(result["Subject"], result["Day"], result["Time"] \
                            , result.get("Place", "Unkown Location")       \
                            , url=tutoralLink                              \
                            , tutor=result["Tutor"])
    
    def getAllTutorials(self, show_all = False):
        startURL = 'https://muesli.mathi.uni-heidelberg.de/start'
        if show_all:
            r = self.session.post(startURL + '?show_all=1')
        else:
            r = self.session.post(startURL)
        
        soup = BeautifulSoup(r.text, 'html.parser')
        anchors = soup.findAll("a", href=re.compile("/tutorial/view/\d*"), title=False)
        result = [self.baseURL + anchors[i].get("href") for i in range(0, len(anchors))]

        return list(map(self.__extractTutorialInfo, result))
    
    #--------------------------------------------------------------------------
    
    def __getAllStudents(self, tut : Tutorial):
        r = self.session.post(tut.url)
        soup = BeautifulSoup(r.text, 'html.parser')
        tables = soup.findAll("table", attrs={"class":"colored"})
        students = []

        if len(tables) != 1:
            raise RuntimeError("On", tut.url
                               , "there where", len(tables)
                               , "colored tables (1 expected)!")

        def extractMail(col):
            return col.find('a')['href'][len('mailto:'):]
        
        def toStudent(cols):
            return Student(cols[0].text, extractMail(cols[0]), cols[1].text \
                           , tut.day, tut.time, tut.tutor)
        
        grid = map(lambda row : row.findAll('td'), tables[0].findAll('tr'))
        students = [toStudent(cols) for cols in grid if len(cols) > 0]

        return sorted(students, key=lambda x: x.name)
    
    def getAllStudents(self, tut):
        if isinstance(tut, list):
            res = []
            for t in tut:
                res.extend(self.getAllStudents(t))
            return res
        
        elif isinstance(tut, Tutorial):
            return self.__getAllStudents(tut)
        
        else:
            raise RuntimeError("Need a 'list of Tutorials' or a 'Tutorial'")

    #--------------------------------------------------------------------------
        
#==============================================================================

