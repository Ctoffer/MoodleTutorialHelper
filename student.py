#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 29 14:32:18 2017

@author: ctoffer
"""

#==============================================================================

class Student:
    
    def __init__(self, name, mail, subject, day, time, tutor, state = 'INTERNAL'):
        self.__name = name
        self.__mail = mail
        self.__subj = subject
        self.__day = day
        self.__time = time
        self.__tutor = tutor
        self.__state = state
        
    @property
    def name(self):
        return self.__name
    
    @property
    def mail(self):
        return self.__mail
    
    @property
    def subject(self):
        return self.__subj
    
    @property
    def state(self):
        return self.__state
    
    @property
    def day(self):
        return self.__day
    
    @property
    def time(self):
        return self.__time
    
    @property
    def tid(self):
        return self.__day + "_" + self.__time.replace(":", "-")
    
    @property
    def tutor(self):
        return self.__tutor
    
    def __str__(self):
        return str((self.__name, self.__mail, self.__subj, self.__state       \
                    , self.__date, self.__time, self.__tutor))
    
    def toDict(self):
        res = dict()
        
        res['Name']  = self.__name
        res['Mail']  = self.__mail
        res['Subject']  = self.__subj
        res['State'] = self.__state
        res['Day'] = self.__day
        res['Time'] = self.__time
        res['Tutor'] = self.__tutor
        
        return res
    
    @staticmethod
    def to_dict(stud):
        return stud.toDict()
    
    @staticmethod
    def keys():
        return ['Name', 'Mail', 'Subject', 'State', 'Day', 'Time', 'Tutor']
    
    @staticmethod
    def fromDict(dic : dict):
        return Student(dic['Name'], dic['Mail'], dic['Subject'], dic['Day']  \
                       , dic['Time'], dic['State'], dic['Tutor'])
        
#==============================================================================

class NameComparator:
    
    def __init__(self):
        self.__escape = lambda x: x.replace('Ö', 'Oe').replace('Ä', 'Ae') \
                        .replace('Ü', 'Ue').replace('ö', 'oe') \
                        .replace('ä', 'ae').replace('ü', 'ue') \
                        .replace('ß', 'ss').capitalize()
        
    
    def __call__(self, name1 : str, name2 : str):
        return self.__compareNames(name1, name2)
    
    def __escapeName(self, name : str):
        return self.__escape(name)

    
    def __compareNames(self, name1 : str, name2 : str):
        mod = lambda x : x.strip().split(' ')
        return self.__compareNameParts(mod(name1), mod(name2))
    
    def __compareNameParts(self, nameParts1, nameParts2):
        return self.__cmpNameParts([self.__escapeName(x) for x in nameParts1], 
                        [self.__escapeName(x) for x in nameParts2])
        
    def __cmpNameParts(self, left, right):
        if len(left) > len(right):
            return self.__cmpNameParts(right, left)
    
        count = 0
    
        for l in left:
            for r in right:
                if l == '' or r == '':
                    continue
                if l in r or r in l:
                    count += 1
            
        return len(left) == count # minimum match first and last name


#==============================================================================

#i = 0

class StudentFilter:
    
    def __init__(self, refList : list):
        self.__refList = refList
        self.__nCmp = NameComparator()
        
    def matches(self, name, mail = None):
        #global i
        #print('StudentFilter#matches', i)
        #i += 1
        for student in self.__refList:
            if mail is not None and mail == student.mail:
                return (student, True)
            
            elif self.__nCmp(student.name, name):
                return (student, True)
            
        return (None, False)
    
    def filterList(self, data : list):
        print('StudentFilter#filterList')
        return [subm for subm in data if self.matches(subm.name, subm.mail)[1]]
    
#==============================================================================
