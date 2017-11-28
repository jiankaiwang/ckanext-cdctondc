import logging
import os
import urllib
import urlparse
import copy
import urlparse
from urllib import urlencode
import psycopg2
from py2psql import *
from REQUESTMETHOD2 import *
import thread
import threading
import time
import datetime
import urllib2
import json
import ckan.lib.fanstatic_resources as fanstatic_resources
import ckan.model as model
from pylons import config
import ckan.plugins as plugins
import ckan.lib.helpers as h
import re

#
# desc : transform time format
# retn : return time string
#
def transTime(option, getDatetime):
    if option == "date":
        return str(getDatetime)[0:10]
    elif option == "minute":
        return str(getDatetime)[11:19]
    else:
        return str(getDatetime)[0:19]


#
# desc : get psql configuration from production.ini
#
def getPSQLInfo(configName, tablename):
    url = config.get(configName)
    pattern = re.compile('\S+://(\S+):(\S+)@(\S+):(\d+)/(\S+)')
    match = pattern.match(url)
    if match:
        link = pattern.findall(url)[0]
        return {\
            'dbhost':link[2], 'dbport':str(link[3]), \
            'dbname':link[4], 'dbtable':tablename, \
            'dbuser':link[0], 'dbpass':link[1]\
        }
    else:
        pattern = re.compile('\S+://(\S+):(\S+)@(\S+)/(\S+)')
        link = pattern.findall(url)[0]
        return {\
            'dbhost':link[2], 'dbport':str("5432"), \
            'dbname':link[3], 'dbtable':tablename, \
            'dbuser':link[0], 'dbpass':link[1]\
        }

#
# desc : get corresponding action for front html btn and also current state of each action
# retn : { "show" : "" , "clicking" : "", "note" : "" }
# |- show : before clicking, text is note
# |- clicking : after clicking, text is note
#
def syncNDCState(pkg):
    psqlInfo = getPSQLInfo('ckan.cdctondc.psqlUrl','')

    # connect to postgresql
    p2l = py2psql(psqlInfo['dbhost'], psqlInfo['dbport'], psqlInfo['dbname'], "public.ndcsync", psqlInfo['dbuser'], psqlInfo['dbpass'])

    # select conditions
    data = p2l.select({"cdcid":pkg[u"id"]},["state","operation","beginning","progress"],asdict=True)

    # set operation
    retState = {"show" : "" , "clicking" : "", "note" : ""}

    # state = {"none"|"existing"}
    # none : not in ndc databases
    # existing : already in ndc databases
    # len(data) < 1 : not in postgresql dataset (untracking)
    if len(data) < 1 or data[0]["state"] == "none":
        # cond : not existing in ndc, and it is not submitted to NDC yet
        # clicking action : post (create)
        # len(data) < 1 : not in postgresql dataset (untracking)
        if len(data) < 1 or data[0]["operation"] == "none":
            retState["show"] = "submit"
            retState["clicking"] = "post"
            retState["note"] = "First Submit"
        # cond : not existing in ndc, clicking to sync and a success sync
        #        this cond would be transformed to { state : "existing", clicking : "success", note : "" }
        # clicking action : put (update)
        elif data[0]["operation"] == "success":
            retState["show"] = "success"
            retState["clicking"] = "put"
            retState["note"] = "Success in " + transTime("date", data[0]["beginning"])
        # cond : not existing in ndc, clicking to sync and a failure sync, this cond would be more action
        # clicking action : post (create)
        elif data[0]["operation"] == "failure":
            retState["show"] = "failure"
            retState["clicking"] = "post"
            retState["note"] = "Failure in " + transTime("date", data[0]["beginning"])
        # cond : not existing in ndc, clicking to sync and is still in syncing
        # clicking action : no action
        elif data[0]["operation"] == "syncing":
            retState["show"] = "sync"
            retState["clicking"] = "sync"
            retState["note"] = "Syncing (" + data[0]["progress"] + ") "
    elif data[0]["state"] == "existing":
        # cond : existing in ndc, clicking to sync and a success sync
        # clicking action : put (update)
        if data[0]["operation"] == "success":
            retState["show"] = "success"
            retState["clicking"] = "put"
            retState["note"] = "Success in " + transTime("date", data[0]["beginning"])
        # cond : existing in ndc, clicking to sync and a failure sync
        # clicking action : put (update)
        elif data[0]["operation"] == "failure":
            retState["show"] = "failure"
            retState["clicking"] = "put"
            retState["note"] = "Failure in " + transTime("date", data[0]["beginning"])
        # cond : existing in ndc, clicking to sync and is still in syncing
        # clicking action : no action
        elif data[0]["operation"] == "syncing":
            retState["show"] = "sync"
            retState["clicking"] = "sync"
            retState["note"] = "Syncing (" + data[0]["progress"] + ") "
        # cond : existing in ndc, but not submitted first in the local postgresql yet
        elif data[0]["operation"] == "none":
            retState["show"] = "success"
            retState["clicking"] = "put"
            retState["note"] = "Success in " + transTime("date", data[0]["beginning"])
    elif data[0]["state"] == "deleted":
        # cond : re-POST after deleting dataset from NDC
        # clicking action : no action
        if data[0]["operation"] == "syncing":
            retState["show"] = "sync"
            retState["clicking"] = "sync"
            retState["note"] = "Syncing (" + data[0]["progress"] + ") "
        # cond : after doing deleting from NDC
        # clicking action : re-POST
        else:
            retState["show"] = "deleted"
            retState["clicking"] = "post"
            retState["note"] = "Deleted on " + transTime("date", data[0]["beginning"])

    return retState


#
# def : multithreading POST/PUT/DELETE
#

class ASSEMBLEDATA:

    # -------------------------------------------------------
    # private
    # -------------------------------------------------------
    __pkg = ""
    __categoryCode = "B00"
    __publisherOrgCode = "A21010000I"
    __publisherOID = "2.16.886.101.20003.20065.20021"
    __organization = u'衛生福利部疾病管制署'
    __publisher = u'衛生福利部疾病管制署'
    __license = u'政府資料開放授權條款－第1版'
    __licenseURL = '/license'
    __spatial = u'臺灣'
    __dbID = ''

    #
    # desc : translate content
    #
    def __getLangContent(self, option, value):
        if option == "cost":
            if value == u"free":
                return u'免費'
            else:
                return u'付費'
        elif option == "freq":
            if value == u"day":
                return u'每日'
            elif value == u"month":
                return u'每月'
            elif value == u"year":
                return u'每年'
            elif value == u"once":
                return u'不更新'
            elif value == u"non-scheduled":
                return u'不定期'

    #
    # desc : transform datetime
    #
    def __transformTime(self, option, getStr):
        if option == "issued":
            return datetime.datetime((int)(getStr[0:4]), (int)(getStr[5:7]), (int)(getStr[8:10]))
        elif option == "modified":
            return datetime.datetime((int)(getStr[0:4]), (int)(getStr[5:7]), (int)(getStr[8:10]), (int)(getStr[11:13]), (int)(getStr[14:16]), (int)(getStr[17:19]))

    #
    # desc : find modified or created time from resources
    #
    def __findModifiedTime(self):
        lastModified = ""
        tmpTime = ""
        for items in self.__pkg[u'resources']:
            tmpTime = items['last_modified'] or items['created']
            if tmpTime > lastModified:
                lastModified = tmpTime
        return lastModified

    #
    # desc : prepare tags
    #
    def __prepareTags(self):
        allKeyList = []
        for item in self.__pkg[u'tags']:
            if item[u'display_name'] not in allKeyList:
                allKeyList.append(item[u'display_name'])
        return allKeyList

    #
    # desc : prepare resources
    #
    def __prepareRSC(self):
        allResourceList = []
        tmpRSC = {}
        # for count resources
        index = 1
        for item in self.__pkg[u'resources']:
            # prepare count string YYY
            tmpIndex = str(index)
            for count in range(len(str(index)),3,1):
                tmpIndex = '0' + tmpIndex
            tmpRSC = {\
                    "resourceID": self.__publisherOrgCode + "-" + self.__dbID + "-" + tmpIndex,\
                    "resourceDescription": item[u'description'],\
                    "format": item[u'format'],\
                    "resourceModified": str(self.__transformTime("modified",item[u'last_modified'] or item[u'created'])),\
                    "downloadURL": item[u'url'],\
                    "metadataSourceOfData": "",\
                    "characterSetCode": "UTF-8"
                    }
            allResourceList.append(tmpRSC)
            index += 1

        return allResourceList

    #
    # desc : get id of the package for the identifier
    #
    def __getPKGID(self, dbHost, dbPort, dbDB, dbTB, dbUser, dbPwd, method):
        # connect to postgresql
        p2l = py2psql(dbHost, dbPort, dbDB, dbTB, dbUser, dbPwd)

        tmpID = ""

        if method == "post":

            # select conditions
            #data = p2l.select({"cdcid":self.__pkg[u"id"]},["id"],asdict=True)
            p2l.execsql("select max(ndcid) as crtid from ndcsync;", True, {})

            # set id
            #tmpID = str(data[0]["id"])
            tmpID = str((int)(p2l.status()['data'][0]['crtid'].split('-')[1]) + 1)

        elif method == "put":

            # select conditions
            #data = p2l.select({"cdcid":self.__pkg[u"id"]},["ndcid"],asdict=True)
            p2l.execsql("select ndcid from ndcsync where cdcid = %(cid)s;", True, {'cid' : self.__pkg[u'id']})

            # set id
            #tmpID = str(data[0]["id"])
            tmpID = str((int)(p2l.status()['data'][0]['ndcid'].split('-')[1]))

        # prepare package id string to XXXXXX
        for index in range(len(str(tmpID)),6,1):
            #if index == 5:
            #    tmpID = '9' + tmpID
            #    continue
            tmpID = '0' + tmpID

        return tmpID

    # -------------------------------------------------------
    # public
    # -------------------------------------------------------

    # constructor
    def __init__(self, dbHost, dbPort, dbDB, dbTB, dbUser, dbPwd, getPKG, method):
        # constant
        self.__categoryCode = "B00"
        self.__publisherOrgCode = "A21010000I"
        self.__publisherOID = "2.16.886.101.20003.20065.20021"
        self.__organization = u'衛生福利部疾病管制署'
        self.__publisher = u'衛生福利部疾病管制署'
        self.__license = u'政府資料開放授權條款－第1版'
        self.__licenseURL = '/license'
        self.__spatial = u'臺灣'

        # outer resource
        self.__pkg = getPKG

        # database id, must be after self.__pkg = getPKG
        self.__dbID = self.__getPKGID(dbHost, dbPort, dbDB, dbTB, dbUser, dbPwd, method)            

    # assemble POST or PUT data
    def assemblePOSTOrPUTData(self):
        postOrPUTData = {}
        postOrPUTData = {\
            "categoryCode": self.__categoryCode,\
            "identifier": self.__publisherOrgCode + "-" + self.__dbID,\
            "title": self.__pkg[u'c_title'],\
            "description": self.__pkg[u'cd_notes'],\
            "fieldDescription": self.__pkg[u'cm_notes'].strip(),\
            "type": self.__pkg[u'data_type'],\
            "license": self.__license,\
            "licenseURL": self.__licenseURL,\
            "cost": self.__getLangContent("cost",self.__pkg[u'fee']),\
            "costURL": "",\
            "costLaw": "",\
            "organization": self.__organization,\
            "organizationContactName": self.__pkg[u'author'],\
            "organizationContactPhone": self.__pkg[u'author_phone'],\
            "organizationContactEmail": self.__pkg[u'author_email'],\
            "publisher": self.__publisher,\
            "publisherContactName": self.__pkg[u'author'],\
            "publisherContactPhone": self.__pkg[u'author_phone'],\
            "publisherContactEmail": self.__pkg[u'author_email'],\
            "publisherOID": self.__publisherOID,\
            "publisherOrgCode": self.__publisherOrgCode,\
            "accrualPeriodicity": self.__getLangContent("freq",self.__pkg[u'updated_freq']),\
            "temporalCoverageFrom": "",\
            "temporalCoverageTo": "",\
            "issued": str(self.__transformTime("issued", self.__pkg[u'pub_time'])),\
            "modified": str(self.__transformTime("modified", self.__findModifiedTime())),\
            "spatial": self.__spatial,\
            "language": "",\
            "landingPage": "",\
            "keyword": self.__prepareTags(),\
            "numberOfData": "",\
            "notes": "",\
            "distribution": self.__prepareRSC()\
        }
        return postOrPUTData   

#
# desc : check dataset existing in the postgresql server
# retn : 0 (failure) or 1 (success : already existing or creating one)
#
def syncNDCInitDataset(dbHost, dbPort, dbDB, dbTB, dbUser, dbPwd, pkg):
    # connect to postgresql
    p2l = py2psql(dbHost, dbPort, dbDB, dbTB, dbUser, dbPwd)

    # select conditions
    data = p2l.select({"cdcid":pkg[u"id"]},[],asdict=True)

    if len(data) > 0:
        # already exisiting in the local postgresql database
        return 1
    else:
        # not in local postgresql database
        return p2l.insert({ "cdcid" : pkg[u"id"], "state": u"none", "operation": u"none", "beginning": datetime.datetime.now() })


# -----------------------------------------------------------------------------------
# html context
# show = {"success"|"failure"|"sync"|"submit"} would be button style in html page
# clicking =  { "post"|"put"|"sync" }, means the action taken for the next step
#
# POST (create)
#   |- http://data.gov.tw/api/v1/rest/dataset
#   |- Method=POST
#
# PUT (update)
#   |- http://data.gov.tw/api/v1/rest/dataset/{identifier}
#   |- Method=PUT
#   |- example : http://data.gov.tw/api/v1/rest/dataset/A41000000G-000001
#
# DELETE (delete)
#   |- http://data.gov.tw/api/v1/rest/dataset/{identifier}
#   |- Method=DELETE
#   |- example : http://data.gov.tw/api/v1/rest/dataset/A41000000G-000001
#
# postgresql database
# TABLE ndcsync schema
# state = {"none"|"existing"|"deleted"} stands for ndc database
# operation = {"none"|"success"|"failure"|"syncing"} means current updating status
# -----------------------------------------------------------------------------------

#
# desc : define in helper function
# getStatus = SYNCNDC("127.0.0.1", "5432", "ckan_default", "public.ndcsync", "ckan_default", "ckan", pkg, "http://data.gov.tw/api/v1/rest/dataset", "check")
# retn :
#  |- retState = {"show" : "failure" , "clicking" : "", "note" : ""}
#    |- show : button show (not clicking)
#    |- clicking : button show (after clicking)
#    |- note : text on the button
# multiprocessing method:
#  |- { "post"|"put"|"sync"|"deleted" }
#
def testNDC(fileName, text):
    with open(fileName,"a") as fout:
        fout.write(text + "\n")

def SYNCNDC(dbHost, dbPort, dbDB, dbTB, dbUser, dbPwd, getPKG, tgtSrc, tgtMtd, *args):

    # dbHost : postgresql server host
    # dbPort : postgresql server port
    # dbDB : postgresql server database
    # dbTB : postgresql server table
    # dbUser : postgresql server user
    # dbPwd : postgresql server password
    # getPKG : source package
    # tgtSrc : target source url
    # tgtMtd : target operaiton method, {"check", "delete"}
    # |- check : auto-check
    # |- delete : delete operation

    # first of all : initialize postgresql database
    status = syncNDCInitDataset(dbHost, dbPort, dbDB, dbTB, dbUser, dbPwd, getPKG)
    if status == 0:
        # initial database went error, this would be preferred to do another try in the next time
        return;

    # POST Data preparation
    if tgtMtd == "delete":

        try:

            # object to record each steps for syncing with NDC
            p2l = py2psql(dbHost, dbPort, dbDB, dbTB, dbUser, dbPwd)

            # write current state to NDC table in postgresql db server
            p2l.update({\
                "operation" : u"syncing".lower(), \
                "progress" : u"50%", \
                u"beginning" : datetime.datetime.now()\
                },{"cdcid" : getPKG[u'id']})

            # start delete from NDC
            ndcid = p2l.select({"cdcid": getPKG[u'id']},["ndcid"],asdict=True)
            delFromNDC = SENDREQUEST(\
                tgtSrc + "/" + ndcid[0][u'ndcid'], \
                {"Authorization" : config.get("ckan.cdctondc.apikey")}, \
                {},\
                "DELETE"\
            )
            #time.sleep(60)

            if json.loads(delFromNDC.response()["response"])['success']:
            #if True:
                # success POST
                # write state to postgresql db server
                p2l.update({\
                    "operation" : u"success".lower(), \
                    "state" : u"deleted", \
                    "code" : str(delFromNDC.response()["response"]), \
                    "progress" : u"100%", \
                    u"ending" : datetime.datetime.now()\
                    },{"cdcid" : getPKG[u'id'], "ndcid" : ndcid[0][u'ndcid']})

            else:
                # failure POST
                p2l.update({\
                    "operation" : u"failure".lower(), \
                    "code" : str(delFromNDC.response()["response"]), \
                    "progress" : u"100%", \
                    u"ending" : datetime.datetime.now()\
                    },{"cdcid" : getPKG[u'id'], "ndcid" : ndcid[0][u'ndcid']})

        except:
            p2l.update({\
                "operation" : u"failure".lower(), \
                "code" : u'unexcepted failure in delete', \
                "progress" : u"100%", \
                u"ending" : datetime.datetime.now()\
                },{"cdcid" : getPKG[u'id'], "ndcid" : ndcid[0][u'ndcid']})

    elif tgtMtd == "check":

        # get current state
        getStatue = syncNDCState(getPKG)

        # object to record each steps for syncing with NDC
        p2l = py2psql(dbHost, dbPort, dbDB, dbTB, dbUser, dbPwd)

        # take action based on clicking
        if getStatue["clicking"] == "post":

            try:

                # get post json data
                postData = ASSEMBLEDATA(dbHost, dbPort, dbDB, dbTB, dbUser, dbPwd, getPKG, "post")

                # write current state to NDC table in postgresql db server
                p2l.update({\
                    "operation" : u"syncing".lower(), \
                    "progress" : u"50%", \
                    u"beginning" : datetime.datetime.now()\
                    },{"cdcid" : getPKG[u'id']})

                # start post to NDC
                post2NDC = SENDREQUEST(\
                    tgtSrc, \
                    {"Authorization" : config.get("ckan.cdctondc.apikey")}, \
                    postData.assemblePOSTOrPUTData(),\
                    "POST"\
                )
                #time.sleep(3)

                # debug
                #p2l.update({\
                    #"operation" : u"failure".lower(), \
                    #"ndcid" : postData.assemblePOSTOrPUTData()["identifier"], \
                    #"ndcid" : u'', \
                    #"code" : post2NDC.response()["response"], \
                    #"progress" : u"100%", \
                    #u"ending" : datetime.datetime.now()\
                    #},{"cdcid" : getPKG[u'id']})

                #if u'error' not in json.loads(post2NDC.response()["response"]) or u'錯誤' not in json.loads(post2NDC.response()["response"]) or json.loads(post2NDC.response()["response"])['success']:
                if json.loads(post2NDC.response()["response"])['success']:
                    # success POST
                    # write state to postgresql db server
                    p2l.update({\
                        "operation" : u"success".lower(), \
                        #"ndcid" : postData.assemblePOSTOrPUTData()["identifier"], \
                        "ndcid" : json.loads(post2NDC.response()["response"])['result']['identifier'], \
                        "state" : u"existing", \
                        "code" : str(post2NDC.response()["response"]), \
                        "progress" : u"100%", \
                        u"ending" : datetime.datetime.now()\
                        },{"cdcid" : getPKG[u'id']})

                else:
                    # failure POST
                    p2l.update({\
                        "operation" : u"failure".lower(), \
                        #"ndcid" : postData.assemblePOSTOrPUTData()["identifier"], \
                        "ndcid" : json.loads(post2NDC.response()["response"])['error']['identifier'], \
                        "code" : str(post2NDC.response()["response"]), \
                        "progress" : u"100%", \
                        u"ending" : datetime.datetime.now()\
                        },{"cdcid" : getPKG[u'id']})
            except:
                # failure POST
                p2l.update({\
                    "operation" : u"failure".lower(), \
                    #"ndcid" : postData.assemblePOSTOrPUTData()["identifier"], \
                    "ndcid" : u'', \
                    "code" : u'unexcepted failure in POST', \
                    "progress" : u"100%", \
                    u"ending" : datetime.datetime.now()\
                    },{"cdcid" : getPKG[u'id']})   

        elif getStatue["clicking"] == "put":

            try:
                # get put json data
                putData = ASSEMBLEDATA(dbHost, dbPort, dbDB, dbTB, dbUser, dbPwd, getPKG, "put")

                # write current state to NDC table in postgresql db server
                p2l.update({\
                    "operation" : u"syncing".lower(), \
                    "progress" : u"50%", \
                    u"beginning" : datetime.datetime.now()\
                    },{"cdcid" : getPKG[u'id']})

                # start put to NDC
                ndcid = p2l.select({"cdcid": getPKG[u'id']},["ndcid"],asdict=True)
                p2l.update({\
                    "operation" : u"syncing".lower(), \
                    "code" : u'prepare to NDC', \
                    "progress" : u"100%", \
                    u"ending" : datetime.datetime.now()\
                    },{"cdcid" : getPKG[u'id'], "ndcid" : ndcid[0][u'ndcid']})

                with open("/tmp/ndcsync.txt","w") as fout:
                    fout.write(json.dumps(putData.assemblePOSTOrPUTData()))

                put2NDC = SENDREQUEST(\
                    tgtSrc + "/" + ndcid[0][u'ndcid'], \
                    {"Authorization" : config.get("ckan.cdctondc.apikey")}, \
                    putData.assemblePOSTOrPUTData(),\
                    "PUT"\
                )

                #time.sleep(60)
                p2l.update({\
                    "operation" : u"syncing".lower(), \
                    "code" : u'syncing finishs execution, ready to write state', \
                    "progress" : u"100%", \
                    u"ending" : datetime.datetime.now()\
                    },{"cdcid" : getPKG[u'id'], "ndcid" : ndcid[0][u'ndcid']})

                if json.loads(put2NDC.response()["response"])['success']:
                #if True:
                    # success PUT
                    # write state to postgresql db server
                    p2l.update({\
                        "operation" : u"success".lower(), \
                        "state" : u"existing", \
                        "code" : str(put2NDC.response()["response"]), \
                        "progress" : u"100%", \
                        "ending" : datetime.datetime.now()\
                        },{"cdcid" : getPKG[u'id'], "ndcid" : ndcid[0][u'ndcid']})
                else:
                    # failure PUT
                    p2l.update({\
                        "operation" : u"failure".lower(), \
                        "code" : str(put2NDC.response()["response"]), \
                        "progress" : u"100%", \
                        "ending" : datetime.datetime.now()\
                        },{"cdcid" : getPKG[u'id'], "ndcid" : ndcid[0][u'ndcid']})

            except:
                # failure PUT
                p2l.update({\
                    "operation" : u"failure".lower(), \
                    "code" : u'PUT uncepted error', \
                    "progress" : u"100%", \
                    u"ending" : datetime.datetime.now()\
                    },{"cdcid" : getPKG[u'id'], "ndcid" : ndcid[0][u'ndcid']})
        else:
            # getStatue["clicking"] == "sync"
            # this state is in syncing
            # there is not necessary to take any further actions
            return

    # remove from locked object
    link.acquire()
    execThread.remove(getPKG[u'id'])
    link.release()

#
# desc : activate syncing to NDC by clicking
# clicking beginning from here
# exam : actSYNC2NDC("127.0.0.1", "5432", "ckan_default", "public.ndcsync", "ckan_default", "ckan", pkg, "http://data.gov.tw/api/v1/rest/dataset", "check")
#
execThread = []
link = threading.Lock()
def actSYNC2NDC(getPKG, tgtMtd):
    #thread.start_new_thread(SYNCNDC, (dbHost, dbPort, dbDB, dbTB, dbUser, dbPwd, getPKG, tgtSrc, tgtMtd))
    #SYNCNDC(dbHost, dbPort, dbDB, dbTB, dbUser, dbPwd, getPKG, tgtSrc, tgtMtd)
    global execThread, link
    link.acquire()

    tgtSrc = config.get("ckan.cdctondc.apiUrl")
    psqlInfo = getPSQLInfo('ckan.cdctondc.psqlUrl','')

    if getPKG['id'] not in execThread:
        execThread.append(getPKG['id'])
        t = threading.Thread(target=SYNCNDC, args=(psqlInfo['dbhost'], psqlInfo['dbport'], psqlInfo['dbname'], "public.ndcsync", psqlInfo['dbuser'], psqlInfo['dbpass'], getPKG, tgtSrc, tgtMtd))
        t.start()

    link.release()     

