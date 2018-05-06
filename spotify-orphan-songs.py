#!/usr/bin/env python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import sys
import spotipy
import spotipy.util as util

sp = spotipy.Spotify()

scope = 'user-library-read playlist-modify-public'

if len(sys.argv) > 1:
    username = sys.argv[1]
else:
    print("Usage: %s username" % (sys.argv[0],))
    sys.exit()

token = util.prompt_for_user_token(username, scope)

def show_tracks(results):
    for i, item in enumerate(results['items']):
        track = item['track']
        print("   %d %32.32s %s" % (i, track['artists'][0]['name'], track['name']))

if token:
    sp = spotipy.Spotify(auth=token)

    orphan_playlist_id = None

    #
    # Playlist songs
    #

    playlist_songs = set()

    playlists = sp.user_playlists(username)
    for playlist in playlists['items']:
        if playlist['owner']['id'] == username:
            if playlist['name'] != 'Orphan songs':
                print("Scanning", playlist['name'], "-", playlist['tracks']['total'], "songs...")
                results = sp.user_playlist(username, playlist['id'], fields="tracks,next")
                tracks = results['tracks']
                for item in tracks['items']:
                    track = item['track']
                    playlist_songs.add(track['uri'])

                    # More pages ?
                    while(tracks['next']):
                        tracks = sp.next(tracks)
                        for item in tracks['items']:
                            track = item['track']
                            playlist_songs.add(track['uri'])

            else:
                orphan_playlist_id = playlist['id']


    print("Unique songs in playlists:", len(playlist_songs))

    #
    # Library songs
    #

    library_songs = set()

    tracks = sp.current_user_saved_tracks(limit=50)
    print("Scanning library -", tracks['total'], "songs...")

    for item in tracks['items']:
        track = item['track']
        library_songs.add(track['uri'])
        while(tracks['next']):
            tracks = sp.next(tracks)
            for item in tracks['items']:
                track = item['track']
                library_songs.add(track['uri'])

    print("Unique songs in library:", len(library_songs))

    #
    # Difference
    #

    orphan_songs = library_songs.difference(playlist_songs)

    #
    # New playlist
    #

    playlist_name = 'Orphan songs'
    if not orphan_playlist_id:
        print("Creating playlist:", playlist_name)
        playlist = sp.user_playlist_create(username, playlist_name, public=True)
        orphan_playlist_id = playlist['id']
    else:
        print("Updating playlist:", playlist_name)
    
    print(len(orphan_songs), "orphan songs")

    #
    # Add orphans to playlist
    #

    print("Adding/updating tracks in orphan playlist")
    orphan_songs_list = list(orphan_songs)
    for i in range(0, len(orphan_songs_list), 100):
        chunk = orphan_songs_list[i:i + 100]
        if i == 0:
            results = sp.user_playlist_replace_tracks(username, orphan_playlist_id, chunk)
        else:
            results = sp.user_playlist_add_tracks(username, orphan_playlist_id, chunk)

else:
    print("Can't get token for", username)
