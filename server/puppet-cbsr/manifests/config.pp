class cbsr::config inherits cbsr {
  file { '/etc/ssl/certs/private.pem':
    ensure    =>  file,
    source    =>  'puppet:///modules/cbsr/private.pem',
    mode      =>  '0644'
  }
  
  file { '/etc/redis.conf':
    notify    =>  Service['redis'],
    ensure    =>  file,
    source    =>  'puppet:///modules/cbsr/conf/redis.conf',
    owner     =>  'redis',
    mode      =>  '0600'
  }
  file { '/home/vagrant/redis-cli.sh':
    ensure    =>  file,
    source    =>  'puppet:///modules/cbsr/redis-cli.sh',
    mode      =>  '0700',
    require   =>  File['/etc/redis.conf']
  }
  file { '/root/redis-cli.sh':
    ensure    =>  file,
    source    =>  'puppet:///modules/cbsr/redis-cli.sh',
    mode      =>  '0700',
    require   =>  File['/etc/redis.conf']
  }
  
  file { '/etc/httpd':
    ensure    =>  directory,
    owner     =>  'apache',
    mode      =>  '0550',
    require   =>  File['/etc/ssl/certs/private.pem']
  }
  file { '/etc/httpd/conf/httpd.conf':
    notify    =>  Service['httpd'],
    ensure    =>  file,
    source    =>  'puppet:///modules/cbsr/conf/httpd.conf',
    require   =>  File['/etc/httpd']
  }
  file { '/etc/httpd/conf.d/autoindex.conf':
    notify    =>  Service['httpd'],
    ensure    =>  absent,
    require   =>  File['/etc/httpd']
  }
  file { '/etc/httpd/conf.d/userdir.conf':
    notify    =>  Service['httpd'],
    ensure    =>  absent,
    require   =>  File['/etc/httpd/conf.d/autoindex.conf']
  }
  file { '/etc/httpd/conf.d/php.conf':
    notify    =>  Service['httpd'],
    ensure    =>  absent,
    require   =>  File['/etc/httpd/conf.d/userdir.conf']
  }
  file { '/etc/httpd/conf.d/php-fpm.conf':
    notify    =>  Service['httpd'],
    ensure    =>  absent,
    require   =>  File['/etc/httpd/conf.d/php.conf']
  }
  file { '/etc/httpd/conf.d/welcome.conf':
    notify    =>  Service['httpd'],
    ensure    =>  absent,
    require   =>  File['/etc/httpd/conf.d/php-fpm.conf']
  }
  file { '/etc/httpd/conf.d/ssl.conf':
    notify    =>  Service['httpd'],
    ensure    =>  file,
    source    =>  'puppet:///modules/cbsr/conf/ssl.conf',
    require   =>  File['/etc/httpd/conf.d/welcome.conf']
  }
  file { '/etc/httpd/conf.modules.d/01-cgi.conf':
    notify    =>  Service['httpd'],
    ensure    =>  absent,
    require   =>  File['/etc/httpd/conf.d/ssl.conf']
  }
  file { '/etc/httpd/conf.modules.d/00-dav.conf':
    notify    =>  Service['httpd'],
    ensure    =>  absent,
    require   =>  File['/etc/httpd/conf.modules.d/01-cgi.conf']
  }
  file { '/etc/httpd/conf.modules.d/00-lua.conf':
    notify    =>  Service['httpd'],
    ensure    =>  absent,
    require   =>  File['/etc/httpd/conf.modules.d/00-dav.conf']
  }
  file { '/etc/httpd/conf.modules.d/00-base.conf':
    notify    =>  Service['httpd'],
    ensure    =>  file,
    source    =>  'puppet:///modules/cbsr/conf/00-base.conf',
    require   =>  File['/etc/httpd/conf.modules.d/00-lua.conf']
  }
  file { '/etc/httpd/conf.modules.d/00-mpm.conf':
    notify    =>  Service['httpd'],
    ensure    =>  file,
    source    =>  'puppet:///modules/cbsr/conf/00-mpm.conf',
    require   =>  File['/etc/httpd/conf.modules.d/00-base.conf']
  }
  file { '/etc/httpd/conf.modules.d/00-proxy.conf':
    notify    =>  Service['httpd'],
    ensure    =>  file,
    source    =>  'puppet:///modules/cbsr/conf/00-proxy.conf',
    require   =>  File['/etc/httpd/conf.modules.d/00-mpm.conf']
  }
  file { '/etc/php.ini':
    notify    =>  Service['httpd'],
    ensure    =>  file,
    source    =>  'puppet:///modules/cbsr/conf/php.ini',
    require   =>  File['/etc/httpd/conf.modules.d/00-proxy.conf']
  }
  file { '/etc/php.d/20-intl.ini':
    notify    =>  Service['httpd'],
    ensure    =>  file,
    content   =>  'extension=intl.so',
    require   =>  File['/etc/php.ini']
  }
  file { '/etc/php.d/20-mbstring.ini':
    notify    =>  Service['httpd'],
    ensure    =>  file,
    source    =>  'puppet:///modules/cbsr/conf/mbstring.ini',
    require   =>  File['/etc/php.d/20-intl.ini']
  }
  file { '/etc/php.d/10-opcache.ini':
    notify    =>  Service['httpd'],
    ensure    =>  file,
    source    =>  'puppet:///modules/cbsr/conf/opcache.ini',
    require   =>  File['/etc/php.d/20-mbstring.ini']
  }
  file { '/etc/php.d/20-curl.ini':
    notify    =>  Service['httpd'],
    ensure    =>  present,
    content   =>  'extension=curl.so',
    require   =>  File['/etc/php.d/10-opcache.ini'],
  }
  file { '/etc/php.d/20-dom.ini':
    notify    =>  Service['httpd'],
    ensure    =>  present,
    content   =>  'extension=dom.so',
    require   =>  File['/etc/php.d/20-curl.ini'],
  }
  file { '/etc/php.d/20-fileinfo.ini':
    notify    =>  Service['httpd'],
    ensure    =>  present,
    content   =>  'extension=fileinfo.so',
    require   =>  File['/etc/php.d/20-dom.ini'],
  }
  file { '/etc/php.d/20-gd.ini':
    notify    =>  Service['httpd'],
    ensure    =>  present,
    content   =>  'extension=gd.so',
    require   =>  File['/etc/php.d/20-fileinfo.ini'],
  }
  file { '/etc/php.d/20-phar.ini':
    notify    =>  Service['httpd'],
    ensure    =>  present,
    content   =>  'extension=phar.so',
    require   =>  File['/etc/php.d/20-gd.ini'],
  }
  file { '/etc/php.d/20-posix.ini':
    notify    =>  Service['httpd'],
    ensure    =>  absent,
    require   =>  File['/etc/php.d/20-phar.ini'],
  }
  file { '/etc/php.d/40-igbinary.ini':
    notify    =>  Service['httpd'],
    ensure    =>  present,
    content   =>  'extension=igbinary.so',
    require   =>  File['/etc/php.d/20-posix.ini'],
  }
  file { '/etc/php.d/40-msgpack.ini':
    notify    =>  Service['httpd'],
    ensure    =>  present,
    content   =>  'extension=msgpack.so',
    require   =>  File['/etc/php.d/40-igbinary.ini'],
  }
  file { '/etc/php.d/20-json.ini':
    notify    =>  Service['httpd'],
    ensure    =>  present,
    content   =>  'extension=json.so',
    require   =>  File['/etc/php.d/40-msgpack.ini'],
  }
  file { '/etc/php.d/20-exif.ini':
    notify    =>  Service['httpd'],
    ensure    =>  present,
    content   =>  'extension=exif.so',
    require   =>  File['/etc/php.d/20-json.ini'],
  }
  file { '/etc/php.d/20-bcmath.ini':
    notify    =>  Service['httpd'],
    ensure    =>  present,
    content   =>  'extension=bcmath.so',
    require   =>  File['/etc/php.d/20-exif.ini'],
  }
  file { '/etc/php.d/20-bz2.ini':
    notify    =>  Service['httpd'],
    ensure    =>  present,
    content   =>  'extension=bz2.so',
    require   =>  File['/etc/php.d/20-bcmath.ini'],
  }
  file { '/etc/php.d/20-calendar.ini':
    notify    =>  Service['httpd'],
    ensure    =>  absent,
    require   =>  File['/etc/php.d/20-bz2.ini'],
  }
  file { '/etc/php.d/20-ctype.ini':
    notify    =>  Service['httpd'],
    ensure    =>  present,
    content   =>  'extension=ctype.so',
    require   =>  File['/etc/php.d/20-calendar.ini'],
  }
  file { '/etc/php.d/20-ftp.ini':
    notify    =>  Service['httpd'],
    ensure    =>  absent,
    require   =>  File['/etc/php.d/20-ctype.ini'],
  }
  file { '/etc/php.d/50-redis.ini':
    notify    =>  Service['httpd'],
    ensure    =>  present,
    content   =>  'extension=redis.so',
    require   =>  File['/etc/php.d/20-ftp.ini'],
  }
  file { '/etc/php.d/20-gettext.ini':
    notify    =>  Service['httpd'],
    ensure    =>  absent,
    require   =>  File['/etc/php.d/20-ftp.ini'],
  }
  file { '/etc/php.d/20-iconv.ini':
    notify    =>  Service['httpd'],
    ensure    =>  present,
    content   =>  'extension=iconv.so',
    require   =>  File['/etc/php.d/20-gettext.ini'],
  }
  file { '/etc/php.d/20-sysvmsg.ini':
    notify    =>  Service['httpd'],
    ensure    =>  absent,
    require   =>  File['/etc/php.d/20-iconv.ini'],
  }
  file { '/etc/php.d/20-sysvsem.ini':
    notify    =>  Service['httpd'],
    ensure    =>  absent,
    require   =>  File['/etc/php.d/20-sysvmsg.ini'],
  }
  file { '/etc/php.d/20-sysvshm.ini':
    notify    =>  Service['httpd'],
    ensure    =>  absent,
    require   =>  File['/etc/php.d/20-sysvsem.ini'],
  }
  file { '/etc/php.d/20-shmop.ini':
    notify    =>  Service['httpd'],
    ensure    =>  absent,
    require   =>  File['/etc/php.d/20-sysvshm.ini'],
  }
  file { '/etc/php.d/20-pdo.ini':
    notify    =>  Service['httpd'],
    ensure    =>  absent,
    require   =>  File['/etc/php.d/20-shmop.ini'],
  }
  file { '/etc/php.d/30-pdo_sqlite.ini':
    notify    =>  Service['httpd'],
    ensure    =>  absent,
    require   =>  File['/etc/php.d/20-shmop.ini'],
  }
  file { '/etc/php.d/20-sqlite3.ini':
    notify    =>  Service['httpd'],
    ensure    =>  absent,
    require   =>  File['/etc/php.d/30-pdo_sqlite.ini'],
  }
  file { '/etc/php.d/20-sockets.ini':
    notify    =>  Service['httpd'],
    ensure    =>  present,
    content   =>  'extension=sockets.so',
    require   =>  File['/etc/php.d/20-sqlite3.ini'],
  }
  file { '/etc/php.d/20-tokenizer.ini':
    notify    =>  Service['httpd'],
    ensure    =>  present,
    content   =>  'extension=tokenizer.so',
    require   =>  File['/etc/php.d/20-sockets.ini'],
  }
  file { '/etc/php.d/20-simplexml.ini':
    notify    =>  Service['httpd'],
    ensure    =>  present,
    content   =>  'extension=simplexml.so',
    require   =>  File['/etc/php.d/20-tokenizer.ini'],
  }
  file { '/etc/php.d/20-xml.ini':
    notify    =>  Service['httpd'],
    ensure    =>  present,
    content   =>  'extension=xml.so',
    require   =>  File['/etc/php.d/20-simplexml.ini'],
  }
  file { '/etc/php.d/20-xmlwriter.ini':
    notify    =>  Service['httpd'],
    ensure    =>  present,
    content   =>  'extension=xmlwriter.so',
    require   =>  File['/etc/php.d/20-xml.ini'],
  }
  file { '/etc/php.d/30-xmlreader.ini':
    notify    =>  Service['httpd'],
    ensure    =>  present,
    content   =>  'extension=xmlreader.so',
    require   =>  File['/etc/php.d/20-xmlwriter.ini'],
  }
  file { '/etc/php.d/20-xsl.ini':
    notify    =>  Service['httpd'],
    ensure    =>  absent,
    require   =>  File['/etc/php.d/30-xmlreader.ini'],
  }
  file { '/etc/php.d/30-wddx.ini':
    notify    =>  Service['httpd'],
    ensure    =>  absent,
    require   =>  File['/etc/php.d/20-xsl.ini'],
  }
  file { '/etc/php.d/40-zip.ini':
    notify    =>  Service['httpd'],
    ensure    =>  present,
    content   =>  'extension=zip.so',
    require   =>  File['/etc/php.d/30-wddx.ini'],
  }
  file { '/etc/php-fpm.conf':
    notify    =>  Service['php-fpm'],
    ensure    =>  file,
    source    =>  'puppet:///modules/cbsr/conf/php-fpm.conf',
    require   =>  File['/etc/php.d/40-zip.ini']
  }
  file { '/etc/php-fpm.d/www.conf':
    notify    =>  Service['php-fpm'],
    ensure    =>  file,
    source    =>  'puppet:///modules/cbsr/conf/www.conf',
    require   =>  File['/etc/php-fpm.conf']
  }
  
  file { '/etc/sudoers.d/apache':
    ensure    =>  file,
    content   =>  '%apache ALL=(ALL) NOPASSWD: ALL',
    require   =>  File['/etc/httpd']
  }
  exec { 'composer-install':
    environment => ['COMPOSER_HOME=/var/composer'],
    path        =>  $path,
    cwd         =>  '/var/www/html',
    command     =>  'composer install --no-plugins --no-dev --no-suggest --no-progress --prefer-dist --optimize-autoloader',
    timeout     =>  0,
    require     =>  File['/etc/php.ini']
  }
  
  exec { 'systemctl':
    path      =>  $path,
    command   =>  'systemctl daemon-reload'
  }
  file { '/etc/motd.d/cockpit':
    ensure    =>  absent
  }
}