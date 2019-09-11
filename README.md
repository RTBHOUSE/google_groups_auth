# apache_google_groups_auth
Imagine... when you configure web server usually you grant access to your resources only to specific persons. When you have LDAP it is simple, but what you should do if you have only Google Groups? It is possible?
YES, we developed simple extensions like Google IAP, but everything is located on-premiss in your apache configuration. Actually it is possible to grant access to your on-premiss apache to only selected Google Groups. Membership is verified in every request



Our extension are responsible only for Authorization, additionaly you must use  mod_auth_openidc to Authentication (https://github.com/zmartzone/mod_auth_openidc)

In mod_auth_openidc you can configure simple Authorization like domain or specific users, but you can't select google groups. 
Reason is very simple. OpenID connect do not have access to information containing group membership. You only confirm that your client is the email owner.


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

