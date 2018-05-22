# google_groups_auth
Apache auth based on google groups.

## INSTALL


== google ==
  * utworzenie projektu
  * utworzenie konta serwisowego, pobranie json'a
  * nadanie uprawnien dla konta serwisowego do api "https://www.googleapis.com/auth/admin.directory.group.readonly"


== instalacja zależności w ubuntu ==
  * apt-get install python3-setuptools
  * easy_install3 pip
  * pip3 install google-api-python-client google-auth-httplib2 google-auth pymemcache
  * apt install memcached

== instalacja skryptu python ==

  * wgranie skryptu google_groups_auth.py do np /opt/google_groups_auth/google_groups_auth.py
  * wgranie pliku json konta serwisowego do powyższego katalogu np /opt/google_groups_auth/

