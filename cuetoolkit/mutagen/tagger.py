from mutagen import flac, id3, oggopus, oggvorbis, mp3, MutagenError


class Tagger:
    def __init__(self):
        self.active_class = None
        self.active_action = None

    def prepare(self, media_type):
        choice = {'flac': (flac.FLAC, self._write_vorbis_comment),
                  'ogg': (oggvorbis.OggVorbis, self._write_vorbis_comment),
                  'opus': (oggopus.OggOpus, self._write_vorbis_comment),
                  'mp3': (mp3.MP3, self._write_id3v2_tag)}
        self.active_class, self.active_action = choice[media_type]

    def _write_vorbis_comment(self, file_name, step, obj):
        song = self.active_class(file_name)
        song.delete(file_name)
        song['artist'] = obj.artist[step]
        song['album'] = obj.album
        if obj.genre and not obj.tgenre:
            song['genre'] = obj.genre
        elif obj.tgenre:
            song['genre'] = obj.tgenre[step]
        song['title'] = obj.title[step]
        song['tracknumber'] = str(int(obj.track[step]))
        song['tracktotal'] = str(int(obj.track[-1]))
        if obj.year and not obj.tdate:
            song['date'] = obj.year
        elif obj.tdate:
            song['date'] = obj.tdate[step]
        song['comment'] = obj.comment
        song.save(file_name)

    def _write_id3v2_tag(self, file_name, step, obj):
        song = self.active_class(file_name)
        song.delete()
        song['TPE1'] = id3.TPE1(encoding=3, text=[obj.artist[step]])
        song['TALB'] = id3.TALB(encoding=3, text=[obj.album])
        if obj.genre and not obj.tgenre:
            song['TCON'] = id3.TCON(encoding=3, text=[obj.genre])
        elif obj.tgenre:
            song['TCON'] = id3.TCON(encoding=3, text=[obj.tgenre[step]])
        song['TIT2'] = id3.TIT2(encoding=3, text=[obj.title[step]])
        number = '{0}/{1}'.format(int(obj.track[step]), int(obj.track[-1]))
        song['TRCK'] = id3.TRCK(encoding=3, text=[number])
        if obj.year and not obj.tdate:
            song['TDRC'] = id3.TDRC(encoding=3, text=[obj.year])
        elif obj.tdate:
            song['TDRC'] = id3.TDRC(encoding=3, text=[obj.tdate[step]])
        song['COMM::XXX'] = id3.COMM(
            encoding=3, lang='XXX', desc='', text=[obj.comment])
        song.save(file_name)

    def write_meta(self, file_name, step, obj):
        try:
            self.active_action(file_name, step, obj)
        except (OSError, MutagenError):
            print('warning:{} - metadata cannot be written'.format(file_name))
