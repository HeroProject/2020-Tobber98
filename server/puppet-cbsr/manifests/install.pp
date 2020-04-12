class cbsr::install inherits cbsr {
  file { '/etc/sysconfig/clock':
    ensure      =>  file,
    content     =>  'ZONE="Europe/Amsterdam"'
  }
  exec { 'set-time':
    path        =>  $path,
    command     =>  'ln -sf /usr/share/zoneinfo/Europe/Amsterdam /etc/localtime',
    require     =>  File['/etc/sysconfig/clock']
  }
  file { '/etc/sysctl.conf':
    ensure      =>  file,
    source      =>  'puppet:///modules/cbsr/conf/sysctl',
    require     =>  Exec['set-time']
  }
  exec { 'sysctl':
    path        =>  $path,
    command     =>  'sysctl -p > /dev/null',
    require     =>  File['/etc/sysctl.conf']
  }
  file { '/etc/systemd/system/disable-thp.service':
    notify      =>  Service['disable-thp'],
    ensure      =>  file,
    source      =>  'puppet:///modules/cbsr/services/disable-thp',
    require     =>  Exec['sysctl']
  }
  package { 'iptables-services':
    ensure      =>  present,
    require     =>  File['/etc/systemd/system/disable-thp.service']
  }
  exec { 'iptables':
    path        =>  $path,
    command     =>  'systemctl disable firewalld && systemctl enable iptables',
    require     =>  Package['iptables-services']
  }

  package { 'yum-plugin-fastestmirror':
    ensure      =>  present,
    require     =>  Exec['iptables']
  }
  package { 'yum-utils':
    ensure      =>  present,
    require     =>  Package['yum-plugin-fastestmirror']
  }
  package { 'epel-release':
    ensure      =>  present,
    provider    =>  rpm,
    source      =>  'https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm',
    require     =>  Package['yum-utils']
  }
  package { 'ius-release':
    ensure      =>  present,
    provider    =>  rpm,
    source      =>  'https://repo.ius.io/ius-release-el7.rpm',
    require     =>  Package['epel-release']
  }
  exec { 'yum-update':
    path        =>  $path,
    command     =>  'yum -y update',
    timeout     =>  0,
    require     =>  Package['ius-release']
  }
  
  package { 'at':
    ensure      =>  present,
    require     =>  Exec['yum-update']
  }
  package { 'ntp':
    ensure      =>  present,
    require     =>  Package['at']
  }
  package { 'psmisc':
    ensure      =>  present,
    require     =>  Package['ntp']
  }
  package { 'wget':
    ensure      =>  present,
    require     =>  Package['psmisc']
  }
  package { 'cmake':
    ensure      =>  present,
    require     =>  Package['wget']
  }
  package { 'sshpass':
    ensure      =>  present,
    require     =>  Package['cmake']
  }
  
  package { 'python-devel':
    ensure      =>  present,
    require     =>  Package['sshpass']
  }
  package { 'java-1.8.0-openjdk-devel':
    ensure      =>  present,
    require     =>  Package['sshpass']
  }
  package { 'redis5':
    ensure      =>  present,
    require     =>  Package['sshpass']
  }
  
  package { 'httpd24u':
    ensure      =>  present,
    require     =>  Package['redis5']
  }
  package { 'php73-cli':
    ensure      =>  present,
    require     =>  Package['httpd24u']
  }
  package { 'php73-fpm-httpd':
    ensure      =>  present,
    require     =>  Package['php73-cli']
  }
  package { 'php73-gd':
    ensure      =>  present,
    require     =>  Package['php73-cli']
  }
  package { 'php73-json':
    ensure      =>  present,
    require     =>  Package['php73-cli']
  }
  package { 'php73-xml':
    ensure      =>  present,
    require     =>  Package['php73-cli']
  }
  package { 'php73-intl':
    ensure      =>  present,
    require     =>  Package['php73-cli']
  }
  package { 'php73-mbstring':
    ensure      =>  present,
    require     =>  Package['php73-cli']
  }
  package { 'php73-bcmath':
    ensure      =>  present,
    require     =>  Package['php73-cli']
  }
  package { 'php73-opcache':
    ensure      =>  present,
    require     =>  Package['php73-cli']
  }
  package { 'php73-pecl-redis':
    ensure      =>  present,
    require     =>  Package['php73-cli']
  }
  exec { 'get-composer':
    environment => ['COMPOSER_HOME=/var/composer'],
    path        =>  $path,
    cwd         =>  '/tmp',
    command     =>  'curl -sS https://getcomposer.org/installer | php && mv composer.phar /usr/bin/composer && chmod 0755 /usr/bin/composer',
    timeout     =>  0,
    onlyif      =>  'test ! -f /usr/bin/composer',
    require     =>  Package['php73-cli']
  }
  exec { 'composer-selfupdate':
    environment => ['COMPOSER_HOME=/var/composer'],
    path        =>  $path,
    command     =>  'composer self-update',
    timeout     =>  0,
    require     =>  Exec['get-composer']
  }
  
  exec { 'pip-install':
    path        =>  $path,
    command     =>  'pip install --ignore-installed redis hiredis google-cloud-speech opencv-python-headless numpy imutils Pillow face_recognition keras tensorflow statistics pandas --upgrade',
    timeout     =>  0,
    require     =>  Package['python-devel']
  }
  file { '/etc/systemd/system/audio_dialogflow.service':
    notify      =>  Service['audio_dialogflow'],
    ensure      =>  file,
    source      =>  'puppet:///modules/cbsr/services/audio_dialogflow',
    require     =>  Package['java-1.8.0-openjdk-devel']
  }
  file { '/etc/systemd/system/audio_google.service':
    notify      =>  Service['audio_google'],
    ensure      =>  file,
    source      =>  'puppet:///modules/cbsr/services/audio_google',
    require     =>  Exec['pip-install']
  }
  file { '/etc/systemd/system/video_facerecognition.service':
    notify      =>  Service['video_facerecognition'],
    ensure      =>  file,
    source      =>  'puppet:///modules/cbsr/services/video_facerecognition',
    require     =>  Exec['pip-install']
  }
  file { '/etc/systemd/system/video_peopledetection.service':
    notify      =>  Service['video_peopledetection'],
    ensure      =>  file,
    source      =>  'puppet:///modules/cbsr/services/video_peopledetection',
    require     =>  Exec['pip-install']
  }
  file { '/etc/systemd/system/video_emotion.service':
    notify      =>  Service['video_emotion'],
    ensure      =>  file,
    source      =>  'puppet:///modules/cbsr/services/video_emotion',
    require     =>  Exec['pip-install']
  }
  file { '/etc/systemd/system/websearch.service':
    notify      =>  Service['websearch'],
    ensure      =>  file,
    source      =>  'puppet:///modules/cbsr/services/websearch',
    require     =>  Exec['pip-install']
  }
  file { '/etc/systemd/system/webserver.service':
    notify      =>  Service['webserver'],
    ensure      =>  file,
    source      =>  'puppet:///modules/cbsr/services/webserver',
    require     =>  Package['java-1.8.0-openjdk-devel']
  }
  file { '/etc/systemd/system/stream_video.service':
    notify      =>  Service['stream_video'],
    ensure      =>  file,
    source      =>  'puppet:///modules/cbsr/services/stream_video',
    require     =>  Package['java-1.8.0-openjdk-devel']
  }
}