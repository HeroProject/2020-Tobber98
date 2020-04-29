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
  file { '/etc/selinux/config':
    ensure      =>  file,
    content     =>  "SELINUX=disabled\n",
    require     =>  Exec['sysctl']
  }
  file { '/etc/systemd/system/disable-thp.service':
    notify      =>  Service['disable-thp'],
    ensure      =>  file,
    source      =>  'puppet:///modules/cbsr/services/disable-thp',
    require     =>  File['/etc/selinux/config']
  }

  package { 'dnf-utils':
    ensure      =>  present,
    require     =>  File['/etc/systemd/system/disable-thp.service']
  }
  package { 'redhat-rpm-config':
    ensure      =>  present,
    require     =>  Package['dnf-utils']
  }
  package { 'epel-release':
    ensure      =>  present,
    provider    =>  rpm,
    source      =>  'https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm',
    require     =>  Package['redhat-rpm-config']
  }
  package { 'remi-release':
    ensure      =>  present,
    provider    =>  rpm,
    source      =>  'https://rpms.remirepo.net/enterprise/remi-release-8.rpm',
    require     =>  Package['epel-release']
  }
  exec { 'dnf-enable':
    path        =>  $path,
    command     =>  'dnf config-manager --enable remi remi-test remi-modular-test',
    timeout     =>  0,
    require     =>  Package['remi-release']
  }
  exec { 'dnf-modules':
    path        =>  $path,
    command     =>  'dnf -y module reset php redis && dnf -y module enable php:remi-7.4 redis:remi-6.0',
    timeout     =>  0,
    require     =>  Exec['dnf-enable']
  }
  exec { 'dnf-update':
    path        =>  $path,
    command     =>  'dnf -y update',
    timeout     =>  0,
    require     =>  Exec['dnf-modules']
  }
  
  package { 'at':
    ensure      =>  present,
    require     =>  Exec['dnf-update']
  }
  package { 'chrony':
    ensure      =>  present,
    require     =>  Package['at']
  }
  package { 'psmisc':
    ensure      =>  present,
    require     =>  Package['chrony']
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
  
  package { 'redis':
    provider    => 'dnfmodule',
    ensure      =>  'remi-6.0',
    require     =>  Package['sshpass']
  }
  package { 'java-1.8.0-openjdk-devel':
    ensure      =>  present,
    require     =>  Package['sshpass']
  }
  
  package { 'httpd':
    ensure      =>  present,
    require     =>  Package['redis']
  }
  package { 'mod_ssl':
    ensure      =>  present,
    require     =>  Package['httpd']
  }
  package { 'php':
    provider    => 'dnfmodule',
    ensure      =>  'remi-7.4',
    require     =>  Package['httpd']
  }
  package { 'php-gd':
    ensure      =>  present,
    require     =>  Package['php']
  }
  package { 'php-intl':
    ensure      =>  present,
    require     =>  Package['php']
  }
  package { 'php-bcmath':
    ensure      =>  present,
    require     =>  Package['php']
  }
  package { 'php-zip':
    ensure      =>  present,
    require     =>  Package['php']
  }
  package { 'php-opcache':
    ensure      =>  present,
    require     =>  Package['php']
  }
  package { 'php-pecl-redis5':
    ensure      =>  present,
    require     =>  Package['php']
  }
  exec { 'get-composer':
    environment => ['COMPOSER_HOME=/var/composer'],
    path        =>  $path,
    cwd         =>  '/tmp',
    command     =>  'curl -sS https://getcomposer.org/installer | php && mv composer.phar /usr/bin/composer && chmod 0755 /usr/bin/composer',
    timeout     =>  0,
    onlyif      =>  'test ! -f /usr/bin/composer',
    require     =>  Package['php']
  }
  exec { 'composer-selfupdate':
    environment => ['COMPOSER_HOME=/var/composer'],
    path        =>  $path,
    command     =>  'composer self-update',
    timeout     =>  0,
    require     =>  Exec['get-composer']
  }
  
  package { 'python2-devel':
    ensure      =>  present,
    require     =>  Package['sshpass']
  }
  exec { 'update-pip':
    path        =>  $path,
    command     =>  'pip2 install --upgrade pip',
    timeout     =>  0,
    require     =>  Package['python2-devel']
  }
  exec { 'pip-install':
    path        =>  $path,
    command     =>  'pip2 install --upgrade redis hiredis google-cloud-speech opencv-python-headless numpy imutils Pillow face_recognition keras tensorflow statistics pandas',
    timeout     =>  0,
    require     =>  Package['python2-devel']
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