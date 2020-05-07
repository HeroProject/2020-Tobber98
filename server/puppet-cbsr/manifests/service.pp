class cbsr::service inherits cbsr {
  service { 'disable-thp':
    enable      =>  true,
    ensure      =>  running
  }
  service { 'NetworkManager':
    enable      =>  true,
    ensure      =>  running
  }
  service { 'chronyd':
    enable      =>  true,
    ensure      =>  running
  }
  
  service { 'redis':
    enable      =>  true,
    ensure      =>  running
  }
  service { 'httpd':
    enable      =>  true,
    ensure      =>  running
  }
  service { 'php-fpm':
    enable      =>  true,
    ensure      =>  running
  }
  
  service { 'audio_dialogflow':
    enable      =>  false
  }
  service { 'audio_google':
    enable      =>  false
  }
  service { 'video_facerecognition':
    enable      =>  false
  }
  service { 'video_peopledetection':
    enable      =>  false
  }
  service { 'video_emotion':
    enable      =>  false
  }
  service { 'websearch':
    enable      =>  false
  }
  service { 'webserver':
    enable      =>  false
  }
  service { 'stream_video':
    enable      =>  false
  }
  service { 'robot_memory':
    enable      =>  false
  }
}