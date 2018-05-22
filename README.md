# google_groups_auth
Apache auth based on google groups.

## INSTALL


## In Google
  * create project
  * create service account and download json
  * add permission to api "https://www.googleapis.com/auth/admin.directory.group.readonly" for service account


## In your system (ubuntu example)
  * apt-get install python3-setuptools
  * easy_install3 pip
  * pip3 install google-api-python-client google-auth-httplib2 google-auth pymemcache
  * apt install memcached

## deploy configuration

  * deploy python script google_groups_auth.py (for example: /opt/google_groups_auth/google_groups_auth.py)
  * deploy json file
  * deploy apache configuration 

