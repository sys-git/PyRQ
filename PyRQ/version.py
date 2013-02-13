'''
Created on 20 Sep 2012

@author: francis
'''
import copy

__pyrq_version = (0, 4, 0)
__pyrq_version_string = "0.4.0"
__pyrq_release_date = "2013.02.13"
__pyrq_version_machine = "multiprocessing.queue.free"

def getVersion():
    """
    Get the sw version. Any time the sw changes, this version should be changed to a new unique value.
    Unfortunately there we can only do this manually until we sort out the release system.
    """
    return copy.copy(__pyrq_version)

def getVersionMachine():
    return copy.copy(__pyrq_version_machine)

def getVersionString():
    return copy.copy(__pyrq_version_string)

def getVersionDate():
    return copy.copy(__pyrq_release_date)

def getVersionTuple():
    return (copy.copy(__pyrq_version), copy.copy(__pyrq_version_string), copy.copy(__pyrq_release_date))

def getExtendedVersionTuple():
    return (copy.copy(__pyrq_version), copy.copy(__pyrq_version_string), copy.copy(__pyrq_release_date), copy.copy(__pyrq_version_machine))

def getVersionDisplay():
    return "PyRQ v%(V)s - %(D)s [%(M)s]"%{"V":getVersionString(), "D":getVersionDate(), "M":getVersionMachine()}
