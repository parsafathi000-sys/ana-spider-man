# Spider Panel — music folder

Drop your audio files here and the panel will play one every time the
console opens (toggle in Settings -> "Background Music").

Supported formats: .mp3 .ogg .wav .m4a .webm .aac .flac

This folder is served at /musics and listed by GET /api/settings
(the `music` object returns the file list + current settings). The
Settings page exposes: Music on/off, Volume, Random track, and a
specific Selected track.

Demo tracks (generated, royalty-free, loopable ambient pads):
  spider_ambient_a_minor.wav
  spider_drift_neon.wav
  spider_night_pad.wav

Replace them with your own — keep the .wav/.mp3 extension and they
will appear in the Selected-track dropdown automatically.
