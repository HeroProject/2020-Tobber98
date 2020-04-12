"""
Tablet module to communicate with Pepper's tablet.
Only used as an import.
"""
import threading
from sys import exit as sys_exit

import qi

from naoqi import ALProxy


# pylint: disable=too-many-instance-attributes
# Eight attributes is fine here.
class Tablet(object):
    """The main Tablet class"""
    PAN_CENTER = 0.0
    FULL_VOLUME = 1.0

    def __init__(self, server_ip, server_port, ip='127.0.0.1', port=9559):
        self.robot_ip = ip
        self.port = port
        self.server_ip = server_ip
        self.server_port = server_port
        self.session = qi.Session()
        self.connect()
        if self.is_connected():
            self.service = self.session.service('ALTabletService')
            self.service.resetTablet()
            self.service.enableWifi()

            self._audio = ALProxy('ALAudioPlayer', self.robot_ip, self.port)
            self._audio.setPanorama(self.PAN_CENTER)  # start with pan at center
            self._audio.stopAll()
            self._audio_thread = None
            self.set_volume(self.FULL_VOLUME)

    def _play_audio_thread(self, url):
        try:
            self._audio.playWebStream(url, self._audio.getMasterVolume(), self.PAN_CENTER)
        except RuntimeError, exception:
            print 'Exception: ', exception
            print 'Invalid url ', url

    def connect(self):
        """Connect a session to the TCP endpoint"""
        try:
            self.session.connect('tcp://' + self.robot_ip + ':' + str(self.port))
        except RuntimeError:
            print 'Cannot connect to Naoqi at {}:{}.'.format(self.robot_ip, self.port)
            print 'Please check your script arguments.'
            sys_exit(1)

    def disconnect(self):
        """Disconnect the session"""
        self.session.close()

    def is_connected(self):
        """Check if the session is connected"""
        return self.session.isConnected()

    @staticmethod
    def settings():
        """Open the tablet settings GUI"""
        # There is no API call for this so the qicli utility has to be used
        # directly.
        from os import system
        system('qicli call ALTabletService._openSettings')

    def url_for(self, resource, res_type):
        """Create a URL for a static resource"""
        if not resource.startswith('http'):
            resource = 'http://{}:{}/{}/{}'.format(self.server_ip, self.server_port, res_type, resource)
        return resource

    def set_volume(self, value):
        """Set the tablet's master volume"""
        if not self.is_connected():
            self.connect()

        if not 0 <= value <= 1:
            raise ValueError('volume must be between 0 and 100%')
        self._audio.setMasterVolume(value)

    def audio_is_playing(self):
        """Check if there is audio playing"""
        try:
            return self._audio_thread.is_alive()
        except AttributeError:
            return self._audio_thread is not None

    def play_audio(self, url):
        """Play audio through the robot's speakers"""
        if not self.audio_is_playing():
            url = self.url_for(url, 'audio')
            self._audio_thread = threading.Thread(target=self._play_audio_thread, args=(url,))
            self._audio_thread.daemon = True
            self._audio_thread.start()

    def stop_audio(self):
        """Stop any currently playing audio"""
        if self.audio_is_playing():
            self._audio.stopAll()
            self._audio_thread.join()
            self._audio_thread = None

    def open_url(self, url=''):
        """
        Show the browser and load the supplied URL. If no URL is passed to
        the function, the last shown URL is loaded.
        """
        if not self.is_connected():
            self.connect()

        if not url:
            self.service.showWebview()
        else:
            self.service.showWebview(url)

    def show_image(self, url, bg_color='#FFFFFF'):
        """Load an image from a given URL"""
        if not self.is_connected():
            self.connect()

        if not url:
            print 'Image URL cannot be empty.'
        else:
            url = self.url_for(url, 'img')

            self.service.setBackgroundColor(bg_color)
            self.service.showImage(url)
            print 'Showing ', url

    def play_video(self, url):
        """Play video on the tablet"""
        if not self.is_connected():
            self.connect()

        if not url:
            print 'Video URL cannot be empty.'
        else:
            url = self.url_for(url, 'video')

            self.service.playVideo(url)
            print 'Playing ', url

    def reload(self):
        """Reload the current page"""
        if not self.is_connected():
            self.connect()

        # 'True' means to bypass local cache
        self.service.reloadPage(True)

    def hide(self):
        """Hide the web browser"""
        if not self.is_connected():
            self.connect()
        self.service.hide()
        print 'Hiding view'


# If the script is running directly
if __name__ == '__main__':
    # Lazy import, argparse only needed if running as main
    import argparse

    # Create the main parser
    PARSER = argparse.ArgumentParser(prog='tablet.py')
    PARSER.add_argument('--server-ip', dest='server_ip')
    PARSER.add_argument('--server-port', dest='server_port')
    PARSER.add_argument('--ip', dest='ip', default='127.0.0.1')
    PARSER.add_argument('--port', dest='port', default=9559)

    # Create a subparser for each function, store result in the 'command'
    # property
    SUBPARSERS = PARSER.add_subparsers(title='commands', dest='command')

    PARSER_WEB = SUBPARSERS.add_parser('web')
    PARSER_WEB.add_argument('url', type=str, default='', nargs='?')

    PARSER_HIDE = SUBPARSERS.add_parser('hide')

    PARSER_IMAGE = SUBPARSERS.add_parser('image')
    PARSER_IMAGE.add_argument('url', type=str, default='')

    PARSER_SETTINGS = SUBPARSERS.add_parser('settings')
    PARSER_RELOAD = SUBPARSERS.add_parser('reload')

    # Actually parse command-line arguments
    ARGS = PARSER.parse_args()

    TAB = Tablet(ARGS.server_ip, ARGS.server_port, ARGS.ip, ARGS.port)

    # React to the command that was entered
    if ARGS.command == 'web':
        TAB.open_url(ARGS.url)
    elif ARGS.command == 'hide':
        TAB.hide()
    elif ARGS.command == 'image':
        TAB.show_image(ARGS.url)
    elif ARGS.command == 'settings':
        TAB.settings()
    elif ARGS.command == 'reload':
        TAB.reload()

    # Disconnect the session to avoid connection
    # issues with future sessions.
    TAB.disconnect()