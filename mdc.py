#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 31 15:17:29 2017

@author: ctoffer
"""

import json

from os.path import exists as p_exists
from os.path import join as p_join
from os import getcwd as o_getcwd
from os import makedirs as o_mkdirs

from moodle import MoodleAccount, Moodle, MoodleCourse
from muesli import MuesliAcc, Muesli, Tutorial

from util import ListChoice, DataTable
from student import Student, NameComparator

#==============================================================================

from pip import main as pip_main
from importlib.util import find_spec

def install (module):
    spam_spec = find_spec(module)
    found = spam_spec is not None
    if not found:
        pip_main(['install', module])

#==============================================================================

def createAccount(accountName, to_acc):
    print(accountName.upper())
    print('=' * len(accountName))
    usern = input('Insert loginname: ')
    passw = input('Insert password: ')
    return to_acc(usern, passw)

def createAccounts(accPath):
    toMu = lambda u, p : MuesliAcc(u, p)
    toMo = lambda u, p : MoodleAccount(u, p)
    accNames = {'MÜSLI': toMu, 'MOODLE' : toMo}
    accs = {}
        
    for name, to_acc in accNames.items():
        print('=' * 40)
        accs[name] = createAccount(name, to_acc = to_acc)
        print('=' * 40)
        print()
            
    with open(accPath, 'w', encoding = 'utf-8') as fp:
        json.dump({k:v.toDict() for k,v in accs.items()}, fp = fp, indent = 4)
    
def getAccount(accPath, accName, from_js):
    with open(accPath, 'r', encoding = 'utf-8') as fp:
        return from_js(json.dumps(json.load(fp)[accName]))
    
#------------------------------------------------------------------------------

def createTutorData(tutDataPath):
    d = dict()
    d['Firstname'] = input("Insert ur first name:")
    d['Lastname'] = input("Insert ur last name:")
    
    with open(tutDataPath, 'w', encoding = 'utf-8') as fp:
        json.dump(d, fp = fp, indent = 4)
    
#------------------------------------------------------------------------------

def syncMuesliData(accPath, tutPath, stuPath):
    legacy = input("List legacy tutorials? [Y|n]") == 'Y'
            
    mAcc = getAccount(accPath, "MÜSLI", MuesliAcc.fromJsonString)
    with Muesli(acc = mAcc) as muesli:
        tuts = muesli.getAllTutorials(legacy)
        selected = []
        
        for tut in tuts:
            print("Want to sync from this tutorial: ")
            print(tut.day, tut.time, tut.subject, '(%s)' % tut.room)
            if input("Type [Y/n]") == 'Y':
                selected.append(tut)
        
        # write tutorial information
        cols = ["Subject", "Day", "Time", "Tutor", "Room", "State", "URL"]
        d = DataTable(cols, selected, to_dict = lambda tut : tut.toDict())
        with open(tutPath, 'w', encoding = 'utf-8') as fp:
            d.printToStream(stream = fp)
                    
        # write students information
        students = muesli.getAllStudents(selected)
        stuTab = DataTable(Student.keys(), students , to_dict = Student.to_dict)
        with open(stuPath, 'w', encoding = 'utf-8') as fp:
            stuTab.printToStream(stream = fp)
            
    return
            
#------------------------------------------------------------------------------

def navigateMoodle(accPath, coursePath):
    legacy = input('Wanna selected from old semester? [Y|n]') == 'Y'
    
    mAcc = getAccount(accPath, "MOODLE", MoodleAccount.fromJsonString)
    with Moodle(acc = mAcc) as moodle:
        semesterURL = None
        
        if legacy:
            semsters = moodle.listSemesters()
            exName = lambda tup : tup[0]
            semesterURL = ListChoice(semsters).choose("Semester", selector = exName)[1]
            
        facs = moodle.getAllFacilities(semesterURL=semesterURL)
        facChoice = ListChoice(facs)
        fac = facChoice.choose("Facilities", selector = lambda x : x.name)
        
        print("\nSearch for subfacilites of '%s'" % fac.name)
        subFacs = moodle.getAllSubFacilites(fac)
        sFacChoice = ListChoice(subFacs)
        subFac = sFacChoice.choose("Subfacilites", selector = lambda x : x.name)
        
        print("\nSearch for courses of '%s'" % subFac.name)
        courses = moodle.getAllCourses(subFac)
        courseChoice = ListChoice(courses)
        course = courseChoice.choose("Courses", selector = lambda x : x.name)
        
        with open(coursePath, 'w', encoding = 'utf-8') as fp:
            json.dump(course.toDict(), fp = fp, indent = 4)
        

#==============================================================================

if __name__ == '__main__':
    print("Installing additional modules...", end = '')
    install('bs4')
    install('requests')
    install('zipfile')
    install('rarfile')
    install('tarfile')
    print("[OK]")
    
    root = o_getcwd()
    metaDataPath = p_join(root, "MetaData")
    
    if not p_exists(metaDataPath):
        print("Create MetaData")
        o_mkdirs(metaDataPath)
        
    #----------------------------------------------------------------------
    
    accPath = p_join(metaDataPath, "accounts.json")
    if not p_exists(accPath):
        print("Create accounts")
        createAccounts(accPath)
    else:
        print("Accounts already present")
        
    #----------------------------------------------------------------------
    
    tutDataPath = p_join(metaDataPath, "tutordata.json")
    if not p_exists(tutDataPath):
        print("Create tutor data")
        createTutorData(tutDataPath)
    else:
        print("Tutor data already present")
    
    #----------------------------------------------------------------------
        
    tutPath = p_join(metaDataPath, "tutorials.table")
    stuPath = p_join(metaDataPath, "students.table")
        
    if not p_exists(tutPath):        
        print("Select tutoials to sync - connecting to MUESLI")
        syncMuesliData(accPath, tutPath, stuPath)
    else:
        print("Tutorials and students already present")
            
    #----------------------------------------------------------------------
        
    coursePath = p_join(metaDataPath, "course.json")
    if not p_exists(coursePath):
        print("Navigate in Moodle")
        navigateMoodle(accPath, coursePath)
    else:
        print("Moodle data already present")
            
    #----------------------------------------------------------------------
    
    print()
    print("=" * 40)
    print("Configuration completed. U can now use the other scripts.\n" \
          + "Have a nice day \\(^-^)/")
    
    print("=" * 40)
                    
#==============================================================================

class MetaData:
    
    def __init__(self, root = None):
        if root is None:
            root = o_getcwd()
            
        self.__root = root
        self.__mdataPath = p_join(root, "MetaData")
        self.__name_cmp = NameComparator()
   
    #--------------------------------------------------------------------------
     
    def getAccount(self, accName, from_dict):
        accPath = p_join(self.__mdataPath, "accounts.json")
        with open(accPath, 'r', encoding = 'utf-8') as fp:
            return from_dict(json.load(fp)[accName])
        
    def getMuesliAcc(self):
        return self.getAccount('MÜSLI', MuesliAcc.fromDict)
    
    def getMoodleAcc(self):
        return self.getAccount('MOODLE', MoodleAccount.fromDict)
    
    def getTutorLastname(self):
        tutData = p_join(self.__mdataPath, "tutordata.json")
        with open(tutData, 'r', encoding = 'utf-8') as fp:
            return json.load(fp)['Lastname']
    
    #--------------------------------------------------------------------------
    
    def getSyncedTutorials(self):
        tutPath = p_join(self.__mdataPath, "tutorials.table")
        return DataTable.readFromFile(tutPath, Tutorial.fromDict)
    
    def getTIDs(self):
        tuts = self.getSyncedTutorials()
        return list(set([tut.day + "_" + tut.time.replace(":", "-") for tut in tuts]))
    
    #--------------------------------------------------------------------------
    
    def getMoodleCourse(self):
        coursePath = p_join(self.__mdataPath, "course.json")
        with open(coursePath, 'r', encoding = 'utf-8') as fp:
            return MoodleCourse.fromDict(json.load(fp))
    
    #--------------------------------------------------------------------------
    
    def getStudents(self, fil = lambda x : x):
        studPath = p_join(self.__mdataPath, "students.table")
        studs = DataTable.readFromFile(studPath, Student.fromDict)
        return list(filter(fil, studs))
    
    def getStudentsOf(self, tut : Tutorial):
        fil = lambda x : x.day == tut.day and x.time == tut.time
        return self.getStudents(fil = fil)
    
    def getStudentsByName(self, name : str):
        return self.getStudents(fil = lambda x : self.__name_cmp(name, x.name))
    
    def getStudentByMail(self, mail):
        return self.getStudents(fil = lambda x : x.mail == mail)[0]
    
    #--------------------------------------------------------------------------
        
        
