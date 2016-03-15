'''
Created on Aug 19, 2014

@author: roehrig
'''

import os

class FileListBuilder(object):
    '''
    This class build a list of files from a directory.
    '''

    def __init__(self):
        '''
        Constructor
        '''
        
        self.fileList = []
        
        return
    
    def CreateNewFileList(self, path, filter=None):
        '''
        path - a complete directory path
        filter - a file extension that can be used to select only
                 certain types of files
                 
        This creates a list of all files in a directory.  It filter is not
        None, then the list only contains those files that have the
        desired file extension. The list is returned.
        '''
        self.fileList = []
        try:
            dirList = os.listdir(path)
            
            for fileItem in dirList:
                fileName = os.path.join(path, fileItem)
                if (os.path.isfile(fileName)):
                    if (not filter == None):
                        if fileName.endswith(filter):
                            info = os.stat(fileName)
                            fileSize = info.st_size
                            self.fileList.append((os.path.split(fileName)[1], fileSize))
                    else:
                        info = os.stat(fileName)
                        fileSize = info.st_size
                        self.fileList.append((os.path.split(fileName)[1], fileSize))

        except OSError:
            return None
            
        return self.fileList
    
    def CreateNewSortedFileList(self, path, filter=None):
        '''
        path - a complete directory path
        filter - a file extension that can be used to select only
                 certain types of files
                 
        This creates a list of all files in a directory.  It filter is not
        None, then the list only contains those files that have the
        desired file extension.  The list returned after being sorted
        alphabetically.
        '''
        self.fileList = []
        try :
            dirList = os.listdir(path)
        
        
            for fileItem in dirList:
                fileName = os.path.join(path, fileItem)
                if (os.path.isfile(fileName)):
                    if (not filter == None):
                        if fileName.endswith(filter):
                            info = os.stat(fileName)
                            fileSize = info.st_size
                            self.fileList.append((os.path.split(fileName)[1], fileSize))
                    else:
                        info = os.stat(fileName)
                        fileSize = info.st_size
                        self.fileList.append((os.path.split(fileName)[1], fileSize))
                    
        except OSError:
            return None

        self.fileList.sort(cmp=None, key=lambda fileName: fileName[0])

        return self.fileList