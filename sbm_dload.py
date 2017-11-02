#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 09:19:29 2017

@author: ctoffer
"""

from mdc import MetaData
from moodle import Moodle
from student import StudentFilter

from folder import SubmissionFolder

if __name__ == '__main__':
    md = MetaData()
    
    sheetNr = int(input("Sheet number: "))

    s = SubmissionFolder(sheetNr = sheetNr)
    osubms = s.getOriginalSubmissions()
    lsubms = s.getLocalSubmissions()
    
    if osubms is None:
        with Moodle(acc = md.getMoodleAcc()) as moodle:
            print("Download from Moodle")
            osubms = s.downloadSubsIntoOrigin(moodle)
    else:
        print("Local originals present")
        
    #--------------------------------------------------------------------------
        
    if lsubms is None:
        print("Correct from Origin")
        lsubms = s.correctOrigin(osubms)
    else:
        print("Corrected archives present")
    
    #--------------------------------------------------------------------------
    
    s.unpackIntoWorking(lsubms)
            
        
        
