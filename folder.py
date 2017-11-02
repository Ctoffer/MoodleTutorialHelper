#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 10:51:47 2017

@author: ctoffer
"""

from os.path import basename
from os.path import splitext
from re import compile as rcompile

from os.path import exists as p_exists
from os.path import join as p_join
from os.path import dirname as p_dirname
from os.path import isdir as p_isdir
from os import getcwd as o_getcwd
from os import makedirs as o_mkdirs
from os import remove as o_remove

from shutil import copyfile as s_copyfile
from shutil import rmtree as s_rmtree

from tarfile import open as taropen
from zipfile import ZipFile
from zipfile import ZIP_DEFLATED
from rarfile import RarFile

from moodle import Moodle, MoodleSubmission
from util import DataTable
from mdc import MetaData
from student import StudentFilter

#==============================================================================

class LocalSubmission:
    
    def __init__(self, subm : MoodleSubmission, path : str):
        self.__subm = subm
        self.__path = path
        
    @property
    def subm(self):
        return self.__subm
    
    @property
    def path(self):
        return self.__path
    
    @path.setter
    def path(self, path):
        self.__path = path
        
    def toDict(self):
        d = self.subm.toDict()
        d['Path'] = self.path
        return d
    
    @staticmethod
    def keys():
        return MoodleSubmission.keys() + ['Path']
    
    @staticmethod
    def fromDict(d : dict):
        return LocalSubmission(MoodleSubmission.fromDict(d), d['Path'])

#==============================================================================

def touchFolder(path):
    if not p_exists(path):
        o_mkdirs(path)

class SubmissionFolder:
    
    __opener = {'tar.gz' : lambda tgzFile: taropen(tgzFile, 'r:gz'),
                 'tar' : lambda   tFile: taropen(tFile, 'r:'),
                 'zip' : lambda   zFile: ZipFile(zFile, 'r'),
                 'rar' : lambda   rFile: RarFile(rFile, 'r')
              }
    
    def __init__(self, root = None, sheetNr = 0):
        if root is None:
            root = o_getcwd()
            
        self.__root = root
        self.__path = p_join(self.__root, "Blatt_%s" % str(sheetNr).zfill(2))
        self.__org = p_join(self.__path, "0_Origin")
        self.__mod = p_join(self.__path, "1_Modificated")
        self.__wor = p_join(self.__path, "1_Working")
        self.__fin = p_join(self.__path, "2_Finished")
        self.__nr = sheetNr
        
        touchFolder(self.__path)
        touchFolder(self.__org)
        touchFolder(self.__mod)
        touchFolder(self.__wor)
        touchFolder(self.__fin)
        
        self.__mdata = MetaData()
        self.__fil = StudentFilter(self.__mdata.getStudents())
        
    #--------------------------------------------------------------------------
    
    def getOriginalSubmissions(self):
        path = p_join(self.__org, "lsubms.table")
        if p_exists(path):
            return DataTable.readFromFile(path, LocalSubmission.fromDict)
        else:
            return None
    
    def getLocalSubmissions(self):
        path = p_join(self.__mod, 'localsubms.table')
        if p_exists(path):
            return DataTable.readFromFile(path, LocalSubmission.fromDict)
        else:
            return None
        
    #--------------------------------------------------------------------------    
    
    def downloadSubsIntoOrigin(self, moodle : Moodle):
        print('SubmissionFolder#downloadSubsIntoOrigin')
        logPath = p_join(self.__org, "log.txt")
        submPath = p_join(self.__org, "lsubms.table")
        
        with open(logPath, 'w+', encoding = 'utf-8') as log:
            print("=" * 30, file = log)
            print("Downloading Submissions into Origin", file = log)
            print('-' * 30, file = log)
            
            # result list of tuples(subm, local url)
            print('Folder->Moodle#downloadAllSubmissions', self.__fil is None)
            lsubms = moodle.downloadAllSubmissions(self.__org, self.__mdata.getMoodleCourse(), self.__nr, filt = self.__fil)
            
            with open(submPath, 'w', encoding = 'utf-8') as fp:
                DataTable(LocalSubmission.keys(), lsubms, to_dict = LocalSubmission.toDict).printToStream(fp)
                
            for lsubm in lsubms:
                subm = lsubm.subm
                print("%s" % subm.name, subm.mail, subm.fileURL, file = log)
                
            print("Finished downloading", file = log)
            print("Downloaded %s submissions" % len(lsubms), file = log)
            print(file = log)
            
            return lsubms
        
    #--------------------------------------------------------------------------
        
    def correctOrigin(self, lsubms):
        logPath = p_join(self.__mod, "log.txt")
        log = open(logPath, 'w+', encoding = 'utf-8')
        print("=" * 30, file = log)
        print("Correct Submissionnames and move into Modified", file = log)
        print('-' * 30, file = log)
        
        ssc = SubmissionSyntaxCorrector(self.__mdata.getTutorLastname(), self.__nr)
        nLsubms = list()
        
        orgCorrect, aFixed, mFixed = 0, 0, 0
        
        rSyn, wSyn = ssc.filterPaths(lsubms)
        orgCorrect = len(rSyn)
        print('Correct Syntax %i' % len(rSyn), 'Wrong Syntax %i' % len(wSyn))
        print('Correct Syntax %i' % len(rSyn), 'Wrong Syntax %i' % len(wSyn), file = log)
        
        # Yay they have the correct syntax
        for lsubm in rSyn:
            npath = p_join(self.__mod, basename(lsubm.path))
            s_copyfile(lsubm.path, npath)
            lsubm.path = npath
            nLsubms.append(lsubm)
        
        print('Start correcting...')
        print('Start correcting...', file = log)
        
        for lsubm in wSyn:
            print("Try autocorrect on %s (%s)" % (basename(lsubm.path), lsubm.subm.name))
            print("Try autocorrect on %s (%s)" % (basename(lsubm.path), lsubm.subm.name), file = log)
            npath, flag = ssc.autocorrect(lsubm.path, self.__mdata.getStudentsByName)
            print(npath, flag)
            print(npath, flag, file = log)
            
            # its fucked up - but maybe we can fix it easily
            if flag and npath != lsubm.path:
                print("Success")
                print("Success", file = log)
                npath = p_join(self.__mod, basename(npath))
                s_copyfile(lsubm.path, npath)
                lsubm.path = npath
                nLsubms.append(lsubm)
                aFixed += 1
                
            # its really hard fucked up
            else:
                print("Failure - need human advice")
                print("Failure - need human advice", file = log)
                npath = p_join(self.__mod, basename(ssc.correct(lsubm)))
                s_copyfile(lsubm.path, npath)
                lsubm.path = npath
                nLsubms.append(lsubm)
                mFixed += 1
                
        print("Original correct:", orgCorrect)
        print("Automatically fixed:", aFixed)
        print("Manually fixed:", mFixed)
        
        print('-' * 30, file = log)
        print("Original correct:", orgCorrect, file = log)
        print("Automatically fixed:", aFixed, file = log)
        print("Manually fixed:", mFixed, file = log)
        print(file = log)
        log.close()
        
        with open(p_join(self.__mod, 'localsubms.table'), 'w', encoding = 'utf-8') as fp:
            DataTable(LocalSubmission.keys(), nLsubms, to_dict=LocalSubmission.toDict).printToStream(stream = fp)
        
        return nLsubms
    
    #--------------------------------------------------------------------------
    
    def __unpack(self, src, dest):
        for extension, opener in SubmissionFolder.__opener.items():
            if src.endswith(extension):
                with opener(src) as locFile:
                    path = p_join(dest, basename(src)[0:-len('.' + extension)])
                    locFile.extractall(path)
                    return path
    
    def unpackIntoWorking(self, lsubms):
        log = open("log.txt", "w+", encoding = "utf-8")
        tids = self.__mdata.getTIDs()
        
        print("=" * 30, file = log)
        print("Unpack into tutorial folders", file = log)
        print('-' * 30, file = log)
        
        for tid in tids:
            touchFolder(p_join(self.__wor, tid))
            
        workingFolders = list()
            
        for lsubm in lsubms:
            students = self.__mdata.getStudentsByName(lsubm.subm.name)
            assert(len(students) == 1)
            student = students[0]
            print("Unpack %s into %s" % (basename(lsubm.path), student.tid))
            print("Unpack %s into %s" % (basename(lsubm.path), student.tid), file = log)
            workingFolders += self.__unpack(lsubm.path, p_join(self.__wor, student.tid))
            
        print("Write working table...", file = log)
        with open(p_join(self.__wor, "working.table"), 'w', encoding = 'utf-8') as fp:
            DataTable(["Path"], workingFolders, to_dict = lambda x : {"Path" : x}).printToStream(stream = fp)
        print("[OK]", file = log)
        print(file = log)
        
        log.close()
        
#==============================================================================

def checkParenExpr(path):
    collect = False
    exprs = []
    expr = ''
        
    i = 0
    while i < len(path):
        c = path[i]
        
        if c == '(':
            collect = True
            i += 1
            continue
                    
        elif c == ')':
            collect = False
            exprs.append(expr)
            expr = ''
                        
        if collect:
            expr += c
        i += 1
                
    for e in exprs:
        path = path.replace(e, e.replace('_', '-'))
    return path

#------------------------------------------------------------------------------

def extractStudentNamesFromPath (path):
        return [x.split('(')[0].replace('-', ' ') for x in basename(path).split('.')[0].split('_')[2:]]

#------------------------------------------------------------------------------

class SubmissionSyntaxCorrector(object):
    
    def __init__ (self, tutLastname, sheetNr):
        self.__tutLastname = tutLastname
        self.__sheetNr = sheetNr
        self.__exts = ['zip', 'tar', 'tar.gz', 'rar']
        
        pat = self.__tutLastname.upper()\
                + '_Blatt' + str(sheetNr).zfill(2)\
                + '_(.+-.+(\(.+-.+\))*)+'\
                + '\.(zip|tar\.gz|tar|rar)'
        
        self.__pattern = rcompile(pat)
    
    #--------------------------------------------------------------------------
    
    def isCorrect (self, path):
        return self.__pattern.match(basename(path))
        
    def isSupportedArchive (self, path):
        return splitext(path)[1][1:] in self.__exts
        
    def filterPaths (self, lsubms):
        # TODO fix cancer
        return ([x for x in lsubms if self.isCorrect(x.path)], [x for x in lsubms if not self.isCorrect(x.path)])
    
    #--------------------------------------------------------------------------
    
    def autocorrect (self, path, find_students_by_name):
        path = basename(path)
        if self.isCorrect(path):
            return (path, True)
        
        # if extension is not supported there is no hope for auto-correct
        extension = splitext(path)[1]
        if extension[1:] not in self.__exts:
            return (path, False)
        
        # remove spaces
        if ' ' in path:
            path = path.replace(' ', '_').replace(',', '_')
            
        parts = checkParenExpr(path[:-len(extension)]).split('_')
        students = []
        namepat = rcompile('(.+-.+(\(.+-.+\))*)+')
        
        for part in parts:
            # a part containing a number -> skip
            if any(char.isdigit() for char in part):
                continue
            
            # caps segment will be ignored
            elif part.isupper():
                continue
            
            # correct name part
            elif namepat.match(part):
                students.append(part)
                
            # part in CamelCase
            elif len([i for i, c in enumerate(part) if c.isupper()]) > 1:
                indi = [i for i, c in enumerate(part) if c.isupper()][1:]
                tmp = []
                for ind in indi:
                    l = part[:ind]
                    r = part[ind:]
                    if l not in tmp:
                        tmp.append(l)
                    if r not in tmp:
                        tmp.append(r)
                        
                name = ' '.join(tmp)
                res = find_students_by_name(name)
                
                if len(res) == 1:
                    students.append(res[0].name.replace(' ', '-'))
                    
                elif len(res) > 1:
                    continue
                
                elif len(res) == 0 and len(name) > 6:
                    return (path, False)
                    
            # try to check if its a known name part
            else:
                res = find_students_by_name(part.capitalize())
                
                if len(res) == 1:
                    tmp = res[0].name.replace(' ', '-')
                    if tmp not in students:
                        students.append(tmp)
                    
                elif len(res) > 1: # name part thats not unambiguously
                    return (path, False)
                
        # no students 
        if len(students) == 0:
            return (path, False)
                
        students = sorted(students, key = lambda x: x.split('-')[0])
        npath = self.__tutLastname.upper() + '_Blatt' + str(self.__sheetNr).zfill(2)
        
        for student in students:
            npath += '_' + student
            
        npath += extension
        
        return (npath, True)
      
    #--------------------------------------------------------------------------
        
    def correct(self, lsubm : LocalSubmission):
        print('Current name:', basename(lsubm.path))
        path = lsubm.path
        
        while True:
            newName = input('Corrected name [.zip if file is not an archive]:')
        
            if self.isCorrect(newName):
                if self.isSupportedArchive(path):                
                    print('[OK]')
                    return p_join(path, newName)
             
                else:
                    print('Create Archive...', end = '')
                    
                    #create a zip archive with the correct name
                    newPath = p_join(p_dirname(path), newName)
                    with ZipFile(newPath, 'w', ZIP_DEFLATED) as zFile:
                        zFile.write(path, basename(path))    
                    lsubm.path = newPath
                    
                    # delete homeless file
                    """
                    if p_isdir(path):
                        s_rmtree(path)
                    else:
                        o_remove(path)
                    """
                    print('[OK]')
                    return newPath
                
            else:
                print('Wrong Syntax - Try again please')
        

#==============================================================================    
