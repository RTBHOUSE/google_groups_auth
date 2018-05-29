#!/usr/bin/python3

# ============================== SUMMARY =====================================
#
# Program : google_groups_auth.py
# Version : 0.1 ( first beta )
# Date    : May 22, 2018
# Author  : Marcin Kowalczuk - marcin.kowalczuk(at)rtbhouse.com
# Licence : GPL - summary below, full text at http://www.fsf.org/licenses/gpl.txt
#

import sys
import time
import json
import base64
from google.oauth2 import service_account
import googleapiclient.discovery
from pymemcache.client import base
import config_file as config


#---------------------------------------------------------------------------------
def ask_cache(key):
    try:
        log("cache  -  ask key: " + key)
        client = base.Client((config.MemcacheServer, config.MemcachePort))
        response = client.get(key)
    except:
        log("cache  -  problem with memcache, return: None")
        return None

    return response

#---------------------------------------------------------------------------------
def save_cache(key, value):
    try:
        log("cache  -  save key: " + key)
        client = base.Client((config.MemcacheServer, config.MemcachePort))
        # 5 min expiration time
        client.set(key, value, config.MemcacheExpireTime)
    except:
        log("cache  -  problem with saving cache")

#---------------------------------------------------------------------------------
def log(string):
    ''' to improve, very poor logging '''

    f.write(time.ctime() + "  -  " + string + "\n")
    f.flush()

#---------------------------------------------------------------------------------
def get_google_token():
    ''' to improve: use existing token, at the moment we always create new '''

    log("get google token")
    credentials = service_account.Credentials.from_service_account_file(config.ServiceAccountFile, scopes=config.GoogleScopes).with_subject(config.SubjectAccount)
    directory = googleapiclient.discovery.build('admin', 'directory_v1', credentials=credentials)
    return directory

#---------------------------------------------------------------------------------
def ask_google(key):
    ''' fetching user google groups '''

    try:
        directory = get_google_token()
        results = directory.groups().list(userKey=key).execute()
        grupy = json.loads(json.dumps(results))
        email_list = [element['email'] for element in grupy['groups']]
    except:
        email_list = "empty"
        return(email_list)
    
    return(email_list)

#---------------------------------------------------------------------------------
def get_json(user):

    gr = ask_cache(user) 
    if gr is None:
        gr = ask_google(user)
        log("json  -  " + user + " from google")
        save_cache(user, base64.b64encode(json.dumps(gr).encode('utf-8')))
        return base64.b64encode(json.dumps(gr).encode('utf-8'))
    else:
        log("json  -  " + user + " from cache fetched")
        return gr


#---------------------------------------------------------------------------------
def hasMember(user, group):
    ''' checks cache and (if nessesary) ask google api:https://www.googleapis.com/admin/directory/v1/groups/groupKey/hasMember/memberKey '''


    # join user and group to creating uniq key for memcache
    key = user + "#" + group
    isMember = ask_cache(key)
    if isMember is None:
        #ask goole
        try:
            log("auth  -  connect to google /hasMember/")
            directory = get_google_token()
            results = directory.members().hasMember(groupKey=group, memberKey=user).execute()
            isMember = json.loads(json.dumps(results))['isMember']
        except:
            # if error return no (for example group don't exist )
            log("auth  -  error connect to google /hasMember/")
            isMember = False
            
        if isMember is True:
            save_cache(key, "yes")
            return "yes"
        if isMember is False:
            save_cache(key, "no")
            return "no"
        else:
            log("auth  -  error, unsupported google answer /hasMember/, return no")
            return "no"

    else:
        return isMember.decode('utf-8')



#---------------------------------------------------------------------------------
def check_access_by_member(user, authgroups_string):
    ''' Checks whether the given user is a member of the group. Membership can be direct or nested. '''
    authgroups = authgroups_string.split(";")

    # for authgroups member user membership
    for authgroup in authgroups:
        if hasMember(user, authgroup) == "yes":
            log("auth  -  isMember " + user + "->" + authgroup + " -> return yes")
            return "yes"
        else:
            log("auth  -  isMember " + user + "->" + authgroup +" -> no")
            

    log("auth  -  isMember " + user + "->" + authgroup +" -> return no")
    return "no"


#---------------------------------------------------------------------------------
def main():
    request_count = 0
    global f
    f = open(config.LogFile, 'a')  
    while True:
        # Fetch one line from stdin
        request = input()
        request_count += 1
        log("#################   request count: " + str(request_count))
        log("#################   request -  " + request)
        
        # select script function: fetch user grups or checks permissions
        answer = None
        if request.startswith("json"): 
            args = request.split("#")
            # 0:json  1:user
            answer =  get_json(args[1])
            if not config.isBase64Encrypt:
                   answer =  base64.b64decode(answer)
            log("json  -  STDOUT  -  " + answer.decode('utf-8'))
            print(answer.decode('utf-8'))
            continue


        if request.startswith("auth"): 
            args = request.split("#")
            # 0:auth  1:user  2: authgroups
            if args[2] == "":
                #workaround, some requests are empty, 
                #!!!! (resolved, can't use SetEnv in apache conf)
                answer = "think"
                log("auth  -  STDOUT  -  " + args[1]  + " ...think.....")
                print(answer)
                continue
            else:
                #answer =  check_access(args[1], args[2])
                answer =  check_access_by_member(args[1], args[2])
                log("auth  -  STDOUT  -  " + answer)
                print(answer)
                continue

        if answer == None: 
            log("error  -  bad request, STDOUT: NULL")
            print("NULL")

    f.close()
#---------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
#---------------------------------------------------------------------------------
