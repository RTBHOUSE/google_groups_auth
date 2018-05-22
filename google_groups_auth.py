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


#---------------------------------------------------------------------------------
def ask_cache(key):
    try:
        log("cache  -  ask key: " + key)
        client = base.Client(('localhost', 11211))
        response = client.get(key)
    except:
        log("cache  -  problem z memcache, return: None")
        return None

    return response

#---------------------------------------------------------------------------------
def save_cache(key, value):
    try:
        log("cache  -  save key: " + key)
        client = base.Client(('localhost', 11211))
        # 5 min expiration time
        client.set(key, value, 300)
    except:
        log("cache  -  problem z zapisaniem do cache")

#---------------------------------------------------------------------------------
def log(string):
    ''' do poprawy, bardzo slabe logowanie '''

    f = open('/opt/apache/gauth.txt', 'a')
    f.write(time.ctime() + "  -  " + string + "\n")
    f.flush()
    f.close()

#---------------------------------------------------------------------------------
def get_google_token():
    ''' dorobic uzycie aktualnego tokenu, obecnie za kazdym razem jest nowy '''

    log("get google token")
    SCOPES = ['https://www.googleapis.com/auth/admin.directory.group.readonly']
    SERVICE_ACCOUNT_FILE = '/opt/apache/service_account.json'
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES).with_subject('Subject_account@rtbhouse.com')
    directory = googleapiclient.discovery.build('admin', 'directory_v1', credentials=credentials)
    return directory

#---------------------------------------------------------------------------------
def ask_google(key):
    ''' pobranie z google listy grup usera '''

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
    ''' sprawdza cache, albo pyta google api:https://www.googleapis.com/admin/directory/v1/groups/groupKey/hasMember/memberKey '''


    # sklejam usera i grupe na potrzeby unikalnego klucza memcache
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
            #jesli blad to zwracamy no (np nieistniejaca nazwa grupy)
            log("auth  -  error connect to google /hasMember/")
            isMember = False
            
        if isMember is True:
            save_cache(key, "yes")
            return "yes"
        if isMember is False:
            save_cache(key, "no")
            return "no"
        else:
            log("auth  -  error nieosblugiwana odpowiedz z google /hasMember/, return no")
            return "no"

    else:
        return isMember.decode('utf-8')



#---------------------------------------------------------------------------------
def check_access_by_member(user, authgroups_string):
    ''' weryfikuje przynaleznosc do grup, moze to byc rowniez przynaleznosci zagniezdzona '''
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
def check_access(user, authgroups_string):
    ''' deprecated - funcja nie sprawdzala zagniezdzonych przynaleznoci do grup '''

    gr = ask_cache(user)
    
    if gr is None:
        #pobieram z google liste grup
        gr = ask_google(user)
        log("auth  -  " + user + " from google")
        if gr == "empty":
            #problem z googlem, brak w cache, uwalamy dostep
            log("auth  -  " + user + " error while fetching groups from google, access deny")
            return "no"
    else:
        #pobrane z cache w formacie base64 json, nalezy rozkodowac
        log("auth  -  " + user + " from cache")
        gr = json.loads(base64.b64decode(gr).decode('utf-8'))

    
    authgroups = authgroups_string.split(";")
    for authgroup in authgroups:
        if authgroup in gr:
            log("auth  -  " + user + " return yes")
            return "yes"
    
    log("auth  -  " + user + " return no")
    return "no"



#---------------------------------------------------------------------------------
def main():
    request_count = 0
    while True:
        # Poberam linie z stdin (to co apache wysyla)
        request = input()
        request_count += 1
        log("#################   request count: " + str(request_count))
        log("#################   request -  " + request)
        
        # w zaleznosci od poczatku stringa tworze jsona lub sprawdzam uprawnienia
        answer = None
        if request.startswith("json"): 
            args = request.split("#")
            # 0:json  1:nazwa usera
            answer =  get_json(args[1])
            log("json  -  STDOUT  -  " + answer.decode('utf-8'))
            print(answer.decode('utf-8'))
            continue


        if request.startswith("auth"): 
            args = request.split("#")
            # 0:auth  1:nazwa usera  2: authgroups
            if args[2] == "":
                #workaround, pojawiaja sie puste requesty, 
                #!!!! (rozwiazane, SetEnv w apache odpalany jest po rewrite)
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


#---------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
#---------------------------------------------------------------------------------
