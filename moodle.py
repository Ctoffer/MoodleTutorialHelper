#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 28 16:02:40 2017

Module with everything about Moodle, including:
    MoodleAccount      - data storage for username and passw
    MoodleSubmission   - data storage class for a submission
    Moodle             - access to some date
    
    MoodleFacility     - Contains MetaData like id, name, url
    MoodleSubFacility  - Contains MetaDate like Fac and all Courses
    MoodleCourse       - Contains MetaData like Fac, SubFac and a direct link
    
    MoodleCI           - Console Interface

    MoodleCourse#__prepareFilterOnSite -> modify the pattern of the folder

@author: ctoffer
"""

from bs4 import BeautifulSoup
from re import compile as rcompile
from os.path import join as pjoin
from os.path import exists as pexists
from os import makedirs as omakedirs
from requests import Session
import requests

from util import Cipher
import json

#==============================================================================

class MoodleAccount:
    
    def __init__(self, usern, passw):
        self.__usern = usern
        self.__passw = passw
        
    @property
    def username(self):
        return self.__usern
    
    @property
    def password(self):
        return self.__passw
    
    def toDict(self, key : str = "key_moodle"):
        with Cipher(key) as c:
            d = dict()
            d['ID'] = Cipher.invert(key)
            d['Usern'] = c.encode(self.__usern)
            d['Passw'] = c.encode(self.__passw)
            return d
    
    @staticmethod
    def fromDict(d : dict):
        with Cipher(Cipher.invert(d['ID'])) as c:
            return MoodleAccount(c.decode(d['Usern']), c.decode(d['Passw']))
    
    @staticmethod
    def fromJsonString(jsonStr):
        return MoodleAccount.fromDict(json.loads(jsonStr))
    
    @staticmethod
    def fromJsonFp(fp):
        return MoodleAccount.fromDict(json.load(fp))
    
#==============================================================================

class MoodleSubmission:
    
    def  __init__(self, name, mail, submState, overdue, fileURL, fileName):
        self.__name = name
        self.__mail = mail
        self.__submState = submState
        self.__overdue = overdue
        self.__fURL = fileURL
        self.__fName = fileName
        
    @property
    def name(self):
        return self.__name
    
    @property
    def mail(self):
        return self.__mail
    
    @property
    def submState(self):
        return self.__submState
    
    @property
    def overdue(self):
        return self.__overdue
    
    @property
    def fileURL(self):
        return self.__fURL
    
    @property
    def fileName(self):
        return self.__fName
    
    def __str__(self):
        return str((self.name, self.mail, self.submState, self.overdue, self.fileURL, self.fileName))
    
    #==========================================================================
    
    def toDict(self):
        d = dict()
        d['Name'] = self.__name
        d['Mail'] = self.__mail
        d['SubmState'] = self.__submState
        d['Overdue'] = self.__overdue
        d['FileURL'] = self.__fURL
        d['FileName'] = self.__fName
        return d
    
    @staticmethod
    def fromDict(d : dict):
        return MoodleSubmission(d['Name'], d['Mail'], d['SubmState'],         \
                                d['Overdue'], d['FileURL'], d['FileName'])
    
    @staticmethod
    def keys():
        return ['Name', 'Mail', 'SubmState', 'Overdue', 'FileURL', 'FileName']
    
    #==========================================================================
    
    def download(self, session, dest):
        print('Downloading submission of %s in %s...' % (self.name, pjoin(dest, self.fileName)), end = '', flush = True)
        r = session.get(self.fileURL, stream = True)
            
        if r.status_code == requests.codes.ok:
            if not pexists(dest):
                omakedirs(dest)
            
            archivePath = pjoin(dest, self.fileName)
                
            with open(archivePath, 'wb') as f:
                for chunk in r.iter_content(chunk_size = 128):
                    f.write(chunk)
            print('[OK]')
        else:
            print('Error @ %s - %s' % (self.name, self.fileURL))
        return archivePath
                
        

#==============================================================================

class MoodleFacility:
    
    def __init__ (self, iD, name, url):
        self.__iD = iD
        self.__name = name
        self.__url = url
        self.__subFacs = None
        
    @property
    def iD(self):
        return self.__iD
    
    @property
    def name(self):
        return self.__name
    
    @property
    def url(self):
        return self.__url
    
    #--------------------------------------------------------------------------
    
    def toDict(self):
        d = dict()
        d['ID'] = self.__iD
        d['Name'] = self.__name
        d['URL'] = self.__url
        return d
    
    @staticmethod
    def fromDict(d : dict):
        return MoodleFacility(d['ID'], d['Name'], d['URL'])
    
    #--------------------------------------------------------------------------
    
    def getSubFacs(self, session = None):
        if self.__subFacs is None:
            # create the list if not present
            r = session.get(self.__url)
        
            url = 'https://elearning2\.uni-heidelberg\.de/course/' \
                    + 'index\.php\?categoryid=\d+$'
        
            soup = BeautifulSoup(r.text, 'html.parser')
            rows = soup.findAll('a', href = rcompile(url), attrs = {'itemprop' : False})
        
            get_id = lambda row : row['href'].split('?categoryid=')[1]
            toSubFac = lambda row : MoodleSubFacility(self, get_id(row), row.text, row['href'])
            
            self.__subFacs = [toSubFac(row) for row in rows]
        
        return self.__subFacs

#==============================================================================

class MoodleSubFacility:
     
    def __init__(self, facility : MoodleFacility, iD, name, url):
        self.__fac = facility
        self.__iD = iD
        self.__name = name
        self.__url = url
        self.__courses = None
     
    @property
    def facility(self):
        return self.__fac
        
    @property
    def iD(self):
        return self.__iD
    
    @property
    def name(self):
        return self.__name
    
    @property
    def url(self):
        return self.__url
    
    #--------------------------------------------------------------------------
    
    def toDict(self):
        d = dict()
        d['ID'] = self.__iD
        d['Name'] = self.__name
        d['Facility'] = self.__fac.toDict()
        d['URL'] = self.__url
        return d
    
    @staticmethod
    def fromDict(d : dict):
        fac = MoodleFacility.fromDict(d['Facility'])
        return MoodleSubFacility(fac, d['ID'], d['Name'], d['URL'])
    
    #--------------------------------------------------------------------------
    
    def getCourses(self, session = None):
        if self.__courses is None:
            # create the list of courses
            r = session.get(self.__url)
        
            soup = BeautifulSoup(r.text, 'html.parser')
            elem = soup.find('div', attrs={'class':'course_category_tree clearfix '})
            url = 'https://elearning2\.uni-heidelberg\.de/course/' \
                    + 'view\.php\?id=\d+'
            rows = elem.findAll('a', href = rcompile(url))
        
            self.__courses = [MoodleCourse(self, row.text, row['href']) for row in rows]
        return self.__courses

#==============================================================================

class MoodleCourse:
    
    def __init__(self, subFac : MoodleSubFacility, name, url):
        self.__sFac = subFac
        self.__name = name
        self.__url = url
        
    @property
    def subFacility(self):
        return self.__sFac
    
    @property
    def name(self):
        return self.__name
    
    @property
    def url(self):
        return self.__url
    
    #--------------------------------------------------------------------------
    
    def toDict(self):
        d = dict()
        d['Name'] = self.__name
        d['URL'] = self.__url
        d['SubFacility'] = self.__sFac.toDict()
        return d
    
    @staticmethod
    def fromDict(d : dict):
        sFac = MoodleSubFacility.fromDict(d['SubFacility'])
        return MoodleCourse(sFac, d['Name'], d['URL'])
    
    #--------------------------------------------------------------------------
    
    def __prepareFilterOnSite(self, session, sesskey, sheetNr):
        subMissionURL = None
        r = session.get(self.__url)
        
        soup = BeautifulSoup(r.text, 'html.parser')
        anchors = soup.findAll('a', onclick = True, href = True)

        text = 'Übungsblatt %i Aufgabe' % sheetNr
        fil = lambda x: [a for a in x if text == a.text][0]
       
        sheetLink = fil(anchors)['href']
        
        if sheetLink == None:
            raise ValueError('The exercise sheet was not found')

        btnAs = BeautifulSoup(session.get(sheetLink).text, 'html.parser').findAll('a', href=True, attrs={'class':'btn'}, text='Alle Abgaben anzeigen')
        if len(btnAs) == 1:
            subMissionURL = btnAs[0]['href']
            
        elif len(btnAs) < 1:
            raise ValueError('No btn found!')
            
        else:
            raise ValueError('Too much btns found!')
        
        soup = BeautifulSoup(session.get(subMissionURL).text, 'html.parser')
        classAttrs = soup.find('body').attrs['class']
        formData = {}
        for attr in classAttrs:
            if 'context-' in attr:
                formData['contextid'] = attr.split('-')[1]
            elif 'cmid-' in attr:
                formData['id'] = attr.split('-')[1]
                
  
        # href contains a link where the userid is  a subsequence of
        # split the href at '?'. right side contains userid (uid)
        # pattern of uidElem = id=<num>
        uidElem = soup.find('a', href = True, attrs = {'class':'icon menu-action', 'role':'menuitem', 'data-title':'profile,moodle'})
        
        formData['userid'] = uidElem['href'].split('?')[1].split('=')[1]
        formData['action'] = 'saveoptions'
        formData['sesskey'] = sesskey
        formData['_qf__mod_assign_grading_options_form'] = '1'
        formData['mform_isexpanded_id_general'] = '0'
        formData['perpage'] = '-1'
        formData['downloadasfolders'] = '1'
        
        session.post(subMissionURL, data = formData)
        return subMissionURL
    
    def __getSubmissions(self, url, session, studFilter = None):
        data = []
        soup = BeautifulSoup(session.get(url).text , 'html.parser')
        print(url)
        table = soup.findAll('table', attrs={'class':'flexible generaltable generalbox'})[0]
        rows = table.findChildren('tr')
    
        # Row structure
        # Cell 0: CheckBox 
        # Cell 1: Picture
        # Cell 2: Name                   <<<
        # Cell 3: E-Mail
        # Cell 4: State                  <<<
        # Cell 5: Grade
        # Cell 6: Edit
        # Cell 7: Last Modified
        # Cell 8: Filelink               <<<
        # Cell 9 - 13: Feedbackstuff
        
        for row in rows:
            name = row.find('td', attrs={'class':'cell c2'})
            if name != None:
                name = name.find('a').text
            else:
                continue
            
            mail = row.find('td', attrs={'class':'cell c3 email'})
            if mail != None:
                mail = mail.text
            
            date = row.find('td', attrs={'class':'cell c4'})
            if date == None:
                continue
            
            oDue = date.find('div', attrs={'class':'overduesubmission'})
            if oDue != None:
                oDue = oDue.text
            else:
                lSub = date.find('div', attrs={'class':'latesubmission'})
                oDue = '' if lSub is None else lSub.text
                
            subState = date.find('div').text
            
            submFile = row.find('td', attrs={'class':'cell c8'})
            if submFile == None:
                continue

            submFileAnchor = submFile.find('a', href=True)
            if submFileAnchor == None:
                continue
            submFileLink = submFileAnchor['href']
            submFileName = submFileAnchor.text
            
            # name, mail, submissionState, overdue, fileLink, fileName
            subm = MoodleSubmission(name, mail, subState, oDue, submFileLink, submFileName)
            data.append(subm)

        print('Found a total of %i submissions' % len(data))
#        input('' + str(studFilter is None))

        return data if studFilter is None else studFilter.filterList(data)
        
    
    def getAllSubmissions(self, session, sesskey, sheetNr, studFilter = None):
        print('MoodleCourse#getAllSubmissions', studFilter is None)
        session.get(self.__url)
        url = self.__prepareFilterOnSite(session, sesskey, sheetNr)
        
        return self.__getSubmissions(url, session, studFilter)
    
    
#==============================================================================

class Moodle:

    __baseURL = 'https://elearning2.uni-heidelberg.de'
    
    def __init__(self, acc : MoodleAccount):
        self.__acc = acc
        self.__session = None
        self.__sesskey = None
    
    #--------------------------------------------------------------------------
    
    def login (self):
        self.__session = Session()
        website = Moodle.__baseURL + "/login/index.php"
        print('login', website)
        r = self.__session.post(website, data = dict(username = self.__acc.username, password = self.__acc.password))
        
        if r.url == website or r.status_code != requests.codes.ok:
            raise RuntimeError('Login failed! - Check ur internet connection, username and password')
            
        soup = BeautifulSoup(self.__session.get(r.url).text, 'html.parser')
        start = soup.text.find('sesskey')
        # "sesskey":"adsasnin", - pattern
        self.__sesskey = soup.text[start - 1:].split(',')[0].split(':')[1][1:-1]
        
    def logout (self):
        print('Moodle - logout()')
       
        website = Moodle.__baseURL + '/login/logout.php?sesskey=%s' % self.__sesskey
        r = self.__session.post(website)
        
        self.__session.close()
        self.__session = None
        self.__sesskey = None
        
        if r.status_code != requests.codes.ok:
            raise RuntimeError('Logout Failed - Session was closed!')
    
    #--------------------------------------------------------------------------
    
    def __enter__ (self):
        self.login()
        return self
    
    def __exit__ (self, type, value, traceback):
        self.logout()
    
    #--------------------------------------------------------------------------
    
    def listSemesters(self):
        legacy = 'https://elearning2.uni-heidelberg.de/course/index.php'
        soup = BeautifulSoup(self.__session.post(legacy).text, 'html.parser')
        
        url = 'https://elearning2\.uni-heidelberg\.de/course/' \
                + 'index.php\?categoryid=\d+'
        rows = soup.findAll('a', href = rcompile(url))
        
        return [(row.text, row['href'])for row in rows]
        
    
    def getAllFacilities(self, semesterURL = None):
        soup = BeautifulSoup(self.__session.post(semesterURL or Moodle.__baseURL).text, 'html.parser')
        url = 'https://elearning2\.uni-heidelberg\.de/course/' \
                + 'index.php\?categoryid=\d+'
        rows = soup.findAll('a', href = rcompile(url))
        
        get_id = lambda row : row['href'].split('?categoryid=')[1]
        toFac = lambda row : MoodleFacility(get_id(row), row.text, row['href'])
        
        return [toFac(row) for row in rows]
    
    def getAllSubFacilites(self, fac : MoodleFacility):
        return fac.getSubFacs(self.__session)
    
    def getAllCourses(self, sFac : MoodleSubFacility):
        return sFac.getCourses(session = self.__session)
    
    def getAllSubmissions(self, course : MoodleCourse, sheetNr, filt):
        print("Moodle#getAllSubmissions", filt is None)
        return course.getAllSubmissions(self.__session, self.__sesskey, sheetNr, filt)
    
    def downloadAllSubmissions(self, dest, course : MoodleCourse, sheetNr, filt, key = lambda sm : sm.name):
        print("Moodle#downloadAllSubmissions", filt is None)
        subms = self.getAllSubmissions(course, sheetNr, filt)
        input('Filtered: ' + str(len(subms)))
        subms.sort(key = key)
        return [(subm, subm.download(self.__session, dest)) for subm in subms]
        
    def downloadSubmission(self, dest, subm : MoodleSubmission):
        return subm.download(self.__session, dest)

#==============================================================================
        

