import aiohttp
import asyncspotify as asp

from typing import Dict, TYPE_CHECKING, Optional, List

from asyncspotify import FullTrack

from data_provider import Setter
from objects.Event import Event
from plugin_api import plugin, run_after_init, poll_job, output_service

from .constants import *

if TYPE_CHECKING:
    from core import Core


def playback_stopped_event(track: Optional[asp.track.FullTrack]):
    return Event(event_type=EVENT_PLAYBACK_STOPPED, event_content=track)


def playback_resumed_event(track: asp.track.FullTrack):
    return Event(event_type=EVENT_PLAYBACK_RESUMED, event_content=track)


def playback_started_event(track: asp.track.FullTrack):
    return Event(event_type=EVENT_PLAYBACK_STARTED, event_content=track)


def track_change_event(track: asp.track.FullTrack):
    return Event(event_type=EVENT_TRACK_CHANGE, event_content=track)


def playback_device_change(device: asp.Device):
    return Event(event_type=EVENT_PLAYBACK_DEVICE_CHANGE, event_content=device)


@plugin("spotify")
class Spotify:
    def __init__(self, core: "Core", config: Dict):
        self.core = core
        self.config = config
        print(config)

        self.client: Optional[asp.Client] = None

        self.me = None
        self.context: Optional[asp.CurrentlyPlayingContext] = None
        self.scopes = asp.Scope.all()
        self.currently_playing: Optional[asp.track.FullTrack] = None
        self.playlists = []
        self.auth = asp.EasyAuthorizationCodeFlow(
            client_id="e4e80f0e27f8414c811c3c654c421103",
            client_secret="76e45ae197ce447aa341da133312b39b",
            scope=self.scopes,
            storage=f"{self.core.location}/config/spotify/secret.json",
        )

        self._devices = None

        self._is_playing = None

        self.is_playing = core.storage.setter_factory("spotify.playing")

        self.track: Setter[asp.FullTrack] = core.storage.setter_factory("spotify.track")
        self.progress: Setter[int] = core.storage.setter_factory("spotify.progress")
        self.artist: Setter[asp.FullArtist] = core.storage.setter_factory(
            "spotify.artist"
        )
        self.devices: Setter[asp.Device] = core.storage.setter_factory(
            "spotify.devices"
        )
        self.playlist_names: Setter[List[str]] = core.storage.setter_factory(
            "spotify.playlists"
        )
        self.volume: Setter[int] = core.storage.setter_factory("spotify.volume")
        self.current_playback_device: Setter[asp.Device] = core.storage.setter_factory(
            "spotify.current_playback_device"
        )
        self.current_context: Setter[
            asp.CurrentlyPlayingContext
        ] = core.storage.setter_factory("spotify.current_context")
        self.audio_features: Setter[asp.AudioFeatures] = core.storage.setter_factory(
            "spotify.track.audio_features"
        )

    @run_after_init
    async def setup(self):
        self.client = asp.Client(self.auth)
        await self.client.authorize()
        self.me = await self.client.get_me()
        self.playlists = await self.client.get_user_playlists(self.me)
        self.playlist_names.value = [playlist.name for playlist in self.playlists]
        await self._update_devices()

    @poll_job(1)
    async def update(self):
        try:
            await self.client.refresh()

            try:
                # getting player fails when no active player is found
                self.context = await self.client.get_player()
                self.current_context.value = self.context

                # setting playback device
                try:
                    if self.context.device.id != self.current_playback_device.value.id:
                        self.current_playback_device.value = self.context.device
                        self.core.bus.dispatch(
                            playback_device_change(self.context.device)
                        )
                except AttributeError:
                    self.current_playback_device.value = self.context.device
                    print(self.current_playback_device.value)
                    self.core.bus.dispatch(playback_device_change(self.context.device))

                # updating track state and dispatching events accordingly
                await self._update_track()
                self.volume.value = self.context.device.volume_percent
                await self._update_devices()
            except Exception as e:
                pass
        except:
            pass

    @output_service("spotify.play", None, None)
    async def play(self, *_):
        """Continues playback"""
        await self.client.player_play()

    @output_service("spotify.pause", None, None)
    async def pause(self, *_):
        """Pauses playback"""
        await self.client.player_pause()

    @output_service("spotify.toggle", None, None)
    async def toggle_playback(self, *_):
        """Toggles playback (pause->play/play->pause)"""
        if self.context.is_playing:
            await self.pause()
        else:
            await self.play()

    @output_service("spotify.next", None, None)
    async def next_song(self, *_):
        """skips to th next song"""
        await self.client.player_next()

    @output_service("spotify.previous", None, None)
    async def previous_song(self, *_):
        """goes back to the previous song"""
        await self.client.player_prev()

    @output_service("spotify.set_shuffle", None, None)
    async def shuffle(self, shuffle: bool, *_):
        """Turns shuffle on or off"""
        await self.client.player_shuffle(shuffle)

    @output_service("spotify.volume.set", None, None)
    async def volume(self, volume: int, *_):
        """set volume"""
        await self.client.player_volume(volume)

    @output_service("spotify.track.seek", None, None)
    async def seek(self, pos: int, *_):
        """go to track position in seconds"""
        await self.client.player_seek(pos * 1000)

    @output_service("spotify.start_playlist", None, None)
    async def play_playlist(self, playlist, _, shuffle=True):
        """play playlist"""
        await self.shuffle(shuffle)
        _id = list(filter(lambda p: p.name == playlist, self.playlists))[0]
        await self.client.player_play(context_uri=f"spotify:playlist:{_id.id}")

    async def play_track(self, track):
        pass

    @output_service("spotify.volume.increase", None, None)
    async def increase_volume(self, amount: int, *_):
        """increases volume (percent)"""
        await self.set_volume(amount, _, relative=True)

    @output_service("spotify.volume.decrease", None, None)
    async def decrease_volume(self, amount: int, *_):
        """decreases volume (percent)"""
        await self.set_volume(-amount, _, relative=True)

    @output_service("spotify.volume.set_relative", None, None)
    async def set_volume(self, target, _, relative=False):
        """changes volume, relative to current volume"""
        if relative:
            target = self.context.device.volume_percent + target
        await self.client.player_volume(target)

    @output_service("spotify.playback.set_device", None, None)
    async def select_device(self, device, *_):
        """switch playback device"""
        device_id = self.devices[device]
        async with aiohttp.ClientSession() as session:
            await session.put(
                "https://api.spotify.com/v1/me/player",
                json={"device_ids": [device_id]},
                headers=self.auth.header,
            )

    async def _update_track(self):
        if self.context.track is None and self.currently_playing is not None:
            self.currently_playing = None
            self.is_playing.value = False
            self.core.bus.dispatch(playback_stopped_event(self.currently_playing))
        elif self.context.track is None and self.currently_playing is None:
            return
        elif (
            self.currently_playing is None
            or getattr(self.currently_playing, "name", "") != self.context.track.name
        ):
            self.currently_playing: Optional[FullTrack] = self.context.track
            self.core.bus.dispatch(track_change_event(self.currently_playing))
            self.is_playing.value = True
            self.track.value = self.currently_playing.name
            self.artist.value = self.currently_playing.artists

            f = await self.currently_playing.audio_features()
            self.audio_features.value = f
            # print(
            #     f'energy: {f.energy}\n',
            #     f'dance: {f.danceability}\n',
            #     f'acousticness: {f.acousticness}\n',
            #     f'valence: {f.valence}\n'
            # )

        if self.context.is_playing != self._is_playing:
            self._is_playing = self.context.is_playing
            if self._is_playing:
                self.is_playing.value = True
                self.core.bus.dispatch(playback_resumed_event(self.currently_playing))
            else:
                self.is_playing.value = False
                self.core.bus.dispatch(playback_stopped_event(self.currently_playing))

        if self.context.track is not None:
            self.progress.value = int(
                self.context.progress.total_seconds()
                / self.context.track.duration.total_seconds()
                * 100
            )

    async def _update_devices(self):
        devices = await self.client.get_devices()
        self._devices = {device.name: device for device in devices}
        self.devices.value = self._devices
