# Apache authorization based on Google Group membership 
When you configure web server usually you grant access to your resources only to specific persons. If you have LDAP it is simple, but what you should do if you have only Google Groups? It is possible?
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

# Functions

  * Authorization - main function checking group membership

  * Fetch group list - fetching list of all user groups. It can be saved in the header and forwarded to your app. In some needs, it wants to be very useful. For example, if your application has internal authorizaton then you can simply parse header for checking all user group membership.


# Manual verification

You can check if Google service account is properly configured by manual running Golang binary. The program accepts data on stdin in a specific format depending on the function selected. (See functions)

  * Authorization

When you want to check group membership you should sent to stdin:

```
auth#<user>#<google_group>

for example:
./google_auth.bin 
auth#marcin.kowalczuk@rtbhouse.com#myexamplegroup@rtbhouse.com
yes
```

  * Fetch group list 

```
json#<user>

for example:
./google_auth.bin 
json#marcin.kowalczuk@rtbhouse.com
["myexamplegroup@rtbhouse.com","second-group@rtbhouse.com"]
```

This information can be base64 encoded. See configuration file


# Performance 
It seems that this configuration may be very slow because every request must be verified in google by asking it via API.
Don't worry, the only first request is verified, and result is saved to internal cache for 5 min (github.com/patrickmn/go-cache)

```
	// Create a cache with a default expiration time of 5 minutes, and which
	// purges expired items every 10 minutes
	c := cache.New(5*time.Minute, 10*time.Minute)
```

On internal stress tests, we achieved several thousand req/s using a typical VM (4 CPU, 4GB RAM).



# Configuration

## In Google

First of all you need perform some actions on Google side. 

  * Create project and service account: https://developers.google.com/identity/protocols/OAuth2ServiceAccount and make sure to download the json file.
  * Under "APIs & Auth", choose APIs.
  * Click on Admin SDK and then Enable API.
  * Follow the steps on https://developers.google.com/admin-sdk/directory/v1/guides/delegation#delegate_domain-wide_authority_to_your_service_account and give the client id from step 2 the following oauth scopes:
	https://www.googleapis.com/auth/admin.directory.group.readonly
	https://www.googleapis.com/auth/admin.directory.user.readonly
  * Follow the steps on https://support.google.com/a/answer/60757 to enable Admin API access.
  * Create or choose an existing administrative email address on the Gmail domain. This email will be impersonated by this script to make calls to the Admin SDK.

  * Create clientID in you project (for mod_auth_openidc)
    APIs & Services -> Credentials -> Create credentials -> OAuth client ID -> Web application

## In your system (ubuntu example) - Go Edition
### Compile binary
  * You must compile Go source code (go version > 1.6) 
  * apt install golang
  * go get github.com/patrickmn/go-cache
  * go get -u google.golang.org/api/admin/directory/v1
  * go get -u golang.org/x/oauth2/...
  * go build googe_groups_auth.go


### Install Apache and mod_auth_openidc

```
apt install apache2 libapache2-mod-auth-openidc
a2enmod auth_openidc 
a2enmod headers
a2enmod rewrite
a2enmod ssl

cp -a /opt/google_groups_auth/google-groups-auth.conf.exampleApacheConf  /etc/apache2/sites-available/001-google-groups-auth.conf
a2ensite 001-google-groups-auth.conf
```


Add Authorised JavaScript origins and Authorised redirect URIs in you google project.
APIs & Services -> Credentials -> OAuth2.0 clients IDs -> and select your clientID

### Deploy Apache configuration

  * see puppet_manifest.pp - it describes how the puppet can automatize deploying our extension
  * deploy binary google_groups_auth.bin (for example: /opt/google_groups_auth/google_groups_auth.bin)
  * deploy account.json and config.json fles to the same directory as google_groups_auth.bin
  * deploy apache configuration. Example virtual host configuration you can see in configuration_files/google-groups-auth.conf.exampleApacheConf

### config.json

Example configuration:

```
{
	"GoogleScope": "https://www.googleapis.com/auth/admin.directory.group.readonly",
	"ServiceAccountFile": "account.json",
	"SubjectAccount": "your_Subject_Account",
	"LogFile": "gauthGo.log",
	"Base64Encrypt": false
}
```

GoogleScope - describes connecting permissions to google
ServiceAccountFile - path to you service account json key
SubjectAccount - administrative account, this email will be impersonated by this script to make calls to the Admin SDK.
LogFile - many usefull information
Base64Encrypt - determine if list of user group should be encrypted by base64 or no. 

### LOG example

```
2019/09/11 10:09:07 ############# request:  1  ################
2019/09/11 10:09:07 JSON  - fetch json, user: marcin.kowalczuk@rtbhouse.com
2019/09/11 10:09:07 CACHE - ask for JSON key: marcin.kowalczuk@rtbhouse.com
2019/09/11 10:09:07 CACHE - Do not found json for user marcin.kowalczuk@rtbhouse.com
2019/09/11 10:09:07 JSON  - connect to google
2019/09/11 10:09:08 CACHE - save JSON to cache - key: marcin.kowalczuk@rtbhouse.com
2019/09/11 10:09:08 JSON  - STDOUT: ["myexamplegroup@rtbhouse.com","second-group@rtbhouse.com"] 
2019/09/11 10:09:54 ############# request:  2  ################
2019/09/11 10:09:54 AUTH  - checking auth, user:( marcin.kowalczuk@rtbhouse.com ) groups: myexamplegroup@rtbhouse.com
2019/09/11 10:09:54 CACHE - ask for AUTH key: marcin.kowalczuk@rtbhouse.com#myexamplegroup@rtbhouse.com
2019/09/11 10:09:54 CACHE - Do not found key: marcin.kowalczuk@rtbhouse.com#myexamplegroup@rtbhouse.com in cache
2019/09/11 10:09:54 AUTH  - connect to google /has/Member
2019/09/11 10:09:54 CACHE - save response to cache - key: marcin.kowalczuk@rtbhouse.com#myexamplegrouprtbhouse.com
2019/09/11 10:09:54 AUTH  -  marcin.kowalczuk@rtbhouse.com isMember myexamplegroup@rtbhouse.com ? ...... return yes
2019/09/11 10:09:54 AUTH  - STDOUT:  yes
2019/09/11 10:12:56 ############# request:  3  ################
2019/09/11 10:12:56 JSON  - fetch json, user: marcin.kowalczuk@rtbhouse.com
2019/09/11 10:12:56 CACHE - ask for JSON key: marcin.kowalczuk@rtbhouse.com
2019/09/11 10:12:56 CACHE - Found JSON key: marcin.kowalczuk@rtbhouse.com in cache
2019/09/11 10:12:56 JSON  - STDOUT:  ["myexamplegroup@rtbhouse.com","second-group@rtbhouse.com"] 

```
