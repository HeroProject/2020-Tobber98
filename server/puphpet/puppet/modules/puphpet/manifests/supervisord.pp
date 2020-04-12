# This depends on
#   ajcrowe/supervisord: https://github.com/ajcrowe/puppet-supervisord

class puphpet::supervisord {

  include ::puphpet::python::pip

  Exec['Install pip']
  -> Class['Supervisord::Install']

  if ! defined(Class['supervisord']) {
    class { '::supervisord':
      install_pip => false,
      require     => Class['puphpet::firewall::post'],
    }
  }

}
