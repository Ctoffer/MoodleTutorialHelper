#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 30 13:09:17 2017

@author: ctoffer
"""

import sys

"""
    +====+==========+
    | ID | Name     |
    +====+==========+
    | 01 | Jürgen   |
    +----+----------+
    | 02 | Johannes |
    +----+----------+
"""
class DataTable:
    
    """
        Header is a list of the names of the table columns
        Data is a list of dicts, where each dict contains all headers as keys
    """
    def __init__(self, header : list, data, to_dict = lambda x : x):
        self.__header = header
        self.__data   = list(map(to_dict, data))
        
    def __findMax(self, ind):
        
        maxs = [len(colName) for colName in self.__header]
        
        for row in self.__data:
            for key in self.__header:
                if maxs[ind[key]] < len(row[key]):
                    maxs[ind[key]] = len(row[key])
        
        return maxs
        
    def printToStream(self, stream = sys.stdout):
        ind = {colName : i for i, colName in enumerate(self.__header)}
        print(ind)
        maxs = self.__findMax(ind)
        print(maxs)
        
        pad = lambda s, p = ' ' : p + s + p
        
        div  = pad('+'.join([(v + 2) * '-' for v in maxs]), '+') + '\n'
        hDiv = pad('+'.join([(v + 2) * '=' for v in maxs]), '+') + '\n'
        
        trafo = lambda row : sorted(row.items(), key = lambda t : ind[t[0]])
        rjust = lambda k,v : pad(v.rjust(maxs[ind[k]]))
        norm  = lambda row : [rjust(k,v) for k,v in trafo(row)]
        toRow = lambda row : pad('|'.join(norm(row)), '|') + '\n'
        
        stream.write(hDiv)
        stream.write(toRow({v : v for v in self.__header}))
        stream.write(hDiv)
        
        for row in self.__data:
            stream.write(toRow(row))
            stream.write(div)
            
    @staticmethod
    def readFromString(table : str, from_dict = lambda x : x):
        rows = [v for i, v in enumerate(table.split('\n')) if i % 2 == 1]
        toCols = lambda row : [s.strip() for s in row.split('|')]
        keys = toCols(rows[0])
        
        grid = [{k : v for k, v in zip(keys, toCols(row)) if k != ''} for row in rows[1:]]
        grid = filter(lambda x : len(x) > 0, grid)
        
        return list(map(from_dict, grid))
        
    @staticmethod
    def readFromFile(fname, from_dict = lambda x : x):
        with open(fname, 'r', encoding = 'utf-8') as fp:
            return DataTable.readFromString(fp.read(), from_dict = from_dict)
      
#==============================================================================
    
class Cipher:
    
    def __init__(self, key):
        self.__key = key
    
    #--------------------------------------------------------------------------
    
    def __enter__ (self):
        return self
    
    def __exit__ (self, type, value, traceback):
        pass
    
    #--------------------------------------------------------------------------
    
    def encode(self, string):
        encoded_chars = []
        
        for i in range(len(string)):
            key_c = self.__key[i % len(self.__key)]
            encoded_c = chr(ord(string[i]) + ord(key_c) % 256)
            encoded_chars.append(encoded_c)
        encoded_string = "".join(encoded_chars)
        
        return encoded_string

    def decode(self, string):
        encoded_chars = []
        
        for i in range(len(string)):
            key_c = self.__key[i % len(self.__key)]
            encoded_c = chr(ord(string[i]) - ord(key_c) % 256)
            encoded_chars.append(encoded_c)
        encoded_string = "".join(encoded_chars)
        
        return encoded_string
    
    @staticmethod
    def invert(string):
        return ''.join([chr(255 - ord(c)) for c in string])
    
    #--------------------------------------------------------------------------
    
#==============================================================================

class ListChoice:
    
    def __init__(self, li : list):
        self.__list = li
        self.__len = len(li)
        
    def choose(self, title, selector = lambda x : x):
        print(title)
        print('-' * len(title))
        for i, v in enumerate(self.__list):
            print(str(i).rjust(len(str(self.__len))), selector(v))
            
        index = int(input("Choose an element by it's index (enter -1 to cancel): "))
        while index >= self.__len:
            print('-' * 40)
            print("The index %s is not in the list" % index)
            print("Please try again")
        
            index = int(input("Choose an element by it's index (enter -1 to cancel): "))
        
        if index == -1:
            return None
        else:
            return self.__list[index]
        
#==============================================================================