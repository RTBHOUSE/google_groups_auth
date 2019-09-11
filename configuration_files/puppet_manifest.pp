class google_groups_auth() {
  tag 'ggroups'

#create directory
  file { '/opt/google_groups_auth':
    ensure => 'directory',
    owner  => 'root',
    group  => 'www-data',
    mode   => '0755',
  }

#log directory

  file { '/opt/google_groups_auth/log':
    ensure => 'directory',
    owner  => 'root',
    group  => 'www-data',
    mode   => '0755',
  }

  file { '/opt/google_groups_auth/apache':
    ensure => 'directory',
    owner  => 'root',
    group  => 'www-data',
    mode   => '0755',
  }



# copy files
 file { '/opt/google_groups_auth/config.json':
     ensure  => present,
     mode    => '0640',
     owner   => 'root',
     group   => 'www-data',
     source  => "puppet:///modules/google_groups_auth/config.json",
 }

 file { '/opt/google_groups_auth/rtbauth_service_account.json':
     ensure  => present,
     mode    => '0640',
     owner   => 'root',
     group   => 'www-data',
     source  => "puppet:///modules/google_groups_auth/rtbauth_service_account.json",
 }

 file { '/opt/google_groups_auth/GoogleGroupsAuth.bin':
     ensure  => present,
     mode    => '0750',
     owner   => 'root',
     group   => 'www-data',
     source  => "puppet:///modules/google_groups_auth/GoogleGroupsAuth.bin",
 }

 file { '/opt/google_groups_auth/apache/google-groups-auth.conf.exampleApacheConf':
     ensure  => present,
     mode    => '0640',
     owner   => 'root',
     group   => 'www-data',
     source  => "puppet:///modules/google_groups_auth/google-groups-auth.conf.exampleApacheConf",
 }



}
