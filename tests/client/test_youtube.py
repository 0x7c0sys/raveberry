import os

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse

from django.test import TransactionTestCase
from django.test import Client

import json
import time

from tests import util
from tests.mixins import ConnectionHandlerMixin


class YoutubeTests(ConnectionHandlerMixin, TransactionTestCase):

    def setUp(self):
        self.client = Client()
        util.admin_login(self.client)

        # reduce number of downloaded songs for the test
        self.client.post(reverse('set_max_playlist_items'), {'value': '5'})

        # clear test cache; ensure that it's the test directory
        if os.path.split(os.path.dirname(settings.SONGS_CACHE_DIR))[1] == 'test_cache':
            for member in os.listdir(settings.SONGS_CACHE_DIR):
                member_path = os.path.join(settings.SONGS_CACHE_DIR, member)
                if os.path.isfile(member_path):
                    os.remove(member_path)

    def tearDown(self):
        self.client.login(username='admin', password='admin')

        # restore player state
        self.client.post(reverse('set_autoplay'), {'value': 'false'})
        self._poll_musiq_state(lambda state: not state['autoplay'])

        # ensure that the player is not waiting for a song to finish
        self.client.post(reverse('remove_all'))
        self._poll_musiq_state(lambda state: len(state['song_queue']) == 0)
        self.client.post(reverse('skip_song'))
        self._poll_musiq_state(lambda state: not state['current_song'])

    def _poll_musiq_state(self, break_condition, timeout=10):
        timeout *= 10
        counter = 0
        while counter < timeout:
            state = json.loads(self.client.get(reverse('musiq_state')).content)
            if break_condition(state):
                break
            time.sleep(0.1)
            counter += 1
        else:
            self.fail('enqueue timeout')
        return state

    def _poll_current_song(self):
        state = self._poll_musiq_state(lambda state: state['current_song'])
        current_song = state['current_song']
        return current_song

    def test_query(self):
        self.client.post(reverse('request_music'), {'query': 'Eskimo Callboy MC Thunder', 'playlist': 'false', 'platform': 'youtube'})
        current_song = self._poll_current_song()
        self.assertEqual(current_song['external_url'], 'https://www.youtube.com/watch?v=wobbf3lb2nk')
        self.assertEqual(current_song['artist'], 'Eskimo Callboy')
        self.assertEqual(current_song['title'], 'MC Thunder')
        self.assertEqual(current_song['duration'], 267)

    def test_url(self):
        self.client.post(reverse('request_music'), {'query': 'https://www.youtube.com/watch?v=UNaYpBpRJOY', 'playlist': 'false', 'platform': 'youtube'})
        state = self._poll_musiq_state(lambda state: state['current_song'])
        current_song = state['current_song']
        self.assertEqual(current_song['external_url'], 'https://www.youtube.com/watch?v=UNaYpBpRJOY')
        self.assertEqual(current_song['artist'], 'Bring Me the Horizon')
        self.assertEqual(current_song['title'], 'Avalanche')
        self.assertEqual(current_song['duration'], 275)

    def test_playlist(self):
        self.client.post(reverse('request_music'), {'query': 'https://www.youtube.com/playlist?list=PLiS9Gj9LFFFxFrsk9vKmMWAd4TCrOgYd3', 'playlist': 'true', 'platform': 'youtube'})
        state = self._poll_musiq_state(lambda state: len(state['song_queue']) == 2 and all(song['confirmed'] for song in state['song_queue']), timeout=60)
        self.assertEqual(state['current_song']['external_url'], 'https://www.youtube.com/watch?v=LGamaKv0zNg')
        self.assertEqual(state['song_queue'][0]['external_url'], 'https://www.youtube.com/watch?v=eiCimeZi3-g')
        self.assertEqual(state['song_queue'][1]['external_url'], 'https://www.youtube.com/watch?v=CaY36kVk-cU')

    def test_autoplay(self):
        self.client.post(reverse('request_music'), {'query': 'https://www.youtube.com/watch?v=w8KQmps-Sog', 'playlist': 'false', 'platform': 'youtube'})
        self._poll_current_song()
        self.client.post(reverse('set_autoplay'), {'value': 'true'})
        # make sure a song was downloaded into the queue
        state = self._poll_musiq_state(lambda state: len(state['song_queue']) == 1 and state['song_queue'][0]['confirmed'])
        old_id = state['song_queue'][0]['id']

        self.client.post(reverse('skip_song'))
        # make sure another song is enqueued
        self._poll_musiq_state(lambda state: len(state['song_queue']) == 1 and state['song_queue'][0]['confirmed'] and state['song_queue'][0]['id'] != old_id)

    def test_radio(self):
        self.client.post(reverse('request_music'), {'query': 'https://www.youtube.com/watch?v=w8KQmps-Sog', 'playlist': 'false', 'platform': 'youtube'})
        self._poll_current_song()
        self.client.post(reverse('request_radio'))
        # ensure that 5 songs are enqueued
        self._poll_musiq_state(lambda state: len(state['song_queue']) == 5 and all(song['confirmed'] for song in state['song_queue']), timeout=60)