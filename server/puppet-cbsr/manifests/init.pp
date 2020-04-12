class cbsr (
) inherits cbsr::params {
  $path = ['/usr/bin','/usr/sbin','/bin','/sbin']

  class {'cbsr::install': } ->
  class {'cbsr::config': } ~>
  class {'cbsr::service': } ->
  Class['cbsr']
}