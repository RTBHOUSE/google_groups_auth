# Apache authorization based on Google Group membership 
Imagine... when you configure web server usually you grant access to your resources only to specific persons. When you have LDAP it is simple, but what you should do if you have only Google Groups? It is possible?
YES, we developed simple extensions like Google IAP, but everything is located on-premiss in your apache configuration. Actually it is possible to grant access to your on-premiss apache to only selected Google Groups. Membership is verified in every request



Our extension are responsible only for Authorization, additionaly you must use  mod_auth_openidc to Authentication (https://github.com/zmartzone/mod_auth_openidc)

In mod_auth_openidc you can configure simple Authorization like domain or specific users, but you can't select google groups. 
Reason is very simple. OpenID connect do not have access to information containing group membership. You only confirm that your client is the email owner.


## How it works


When you authenticate using mod_auth_openidc (after a click on consent screen) your apache is aware that you are you. But information about group membership is absent. We should do the next step. Apache should have one service account to asking Google if the user are in group. If answer is positive access is granted, otherwise you show forbidden screen. 
Asking Google realizes by using external program developed in Golang. Apache can run external program using rewrite engine. More specifically RewriteMap (https://httpd.apache.org/docs/2.4/rewrite/rewritemap.html)

Golang extension return simple answer yes or no, all logic is created in rewrite rules. For example if rewrite map don't return "yes" we should forbid the request (3 line):

```
1)  RewriteRule .* - [E=ifaccess:${gauthgroup:auth#%{REMOTE_USER}#%{ENV:authgroups}}]    # see manual verification to understood this syntax
2)  RewriteCond %{ENV:ifaccess} !^yes$ [NC]                                              # condition
3)  RewriteRule ^ - [F,L]                                                                # forbidden
```

# Manual verification
You can check if Google service account is properly configured by manual runing Golang binary. 
The program acceprs data on stdin in specific format depending on the function selected. (See Addicional funcions)

  * 1. Authorization

  When you want to check group membership you shou sent to stdin:

```
auth#<user>#<google_group>

for example:
./google_auth.bin 
auth#marcin.kowalczuk@rtbhouse.com#myexamplegroup@rtbhouse.com
yes
```

  * 2. Fetch group list 

Fetching all group attached to user. It can be saved in header and forwarded to your app. In some needs it want be very usefull. For example if your application has internal authorizaton then you can simply parse header for check all user group membership.

```
json#<user>

for example:
./google_auth.bin 
json#marcin.kowalczuk@rtbhouse.com
["myexamplegroup@rtbhouse.com","second-group@rtbhouse.com"]
```

This information can be base64 encoded. See configuration file


# Configuration file




# Addicional funcions
Header googlegroups contain list of all user groups (base64). It is usefull for additional authorization on the app side.
## INSTALL


### In Google
  * Create project and service account: https://developers.google.com/identity/protocols/OAuth2ServiceAccount and make sure to download the json file.
  * Under "APIs & Auth", choose APIs.
  * Click on Admin SDK and then Enable API.
  * Follow the steps on https://developers.google.com/admin-sdk/directory/v1/guides/delegation#delegate_domain-wide_authority_to_your_service_account and give the client id from step 2 the following oauth scopes:
	https://www.googleapis.com/auth/admin.directory.group.readonly
	https://www.googleapis.com/auth/admin.directory.user.readonly
  * Follow the steps on https://support.google.com/a/answer/60757 to enable Admin API access.
  * Create or choose an existing administrative email address on the Gmail domain. This email will be impersonated by this script to make calls to the Admin SDK.


### In your system (ubuntu example) - Python Edition
  * apt-get install python3-setuptools
  * easy_install3 pip
  * pip3 install google-api-python-client google-auth-httplib2 google-auth pymemcache
  * apt install memcached

### In your system (ubuntu example) - Go Edition
  * You must compile Go source code (go version > 1.6)
  * apt install golang
  * go get github.com/patrickmn/go-cache
  * go get -u google.golang.org/api/admin/directory/v1
  * go get -u golang.org/x/oauth2/...
  
  * go build googe_groups_auth.go


### deploy configuration

  * deploy python script google_groups_auth.py (for example: /opt/google_groups_auth/google_groups_auth.py) or Go binary.
  * deploy json file
  * deploy apache configuration 

