#!/usr/bin/env python3
# -*- mode: python -*-

"""
Downloaded from https://github.com/Deconimus/quicktime-parser
"""


# This program is free software. It comes without any warranty, to the extent
# permitted by applicable law. You can redistribute it and/or modify it under
# the terms of the Do What The Fuck You Want To Public License, Version 2, as
# published by Sam Hocevar. See http://sam.zoy.org/wtfpl/COPYING for more
# details.

# Some useful resources:
# - http://atomicparsley.sourceforge.net/mpeg-4files.html
# - http://developer.apple.com/library/mac/#documentation/QuickTime/
#       QTFF/QTFFChap2/qtff2.html
# - http://www.sno.phy.queensu.ca/~phil/exiftool/TagNames/QuickTime.html

import datetime
import os.path
import struct
import time

NAMES = {  # not used for anything, but just documents a short blurb
    # about what these things mean
    "vmhd": "video information media header",
    "mvhd": 'movie header',
    "tkhd": 'track header',
    # The media header atom specifies the characteristics of a media,
    # including time scale and duration
    "mdhd": 'media header',
    "smhd": 'sound media information header',
    # The handler reference atom specifies the media handler component that is
    # to be used to interpret the media's data
    "hdlr": 'handler reference',

    # The sample description atom contains a table of sample descriptions
    "stsd": "sample description",
    "stts": "time-to-sample",  # Time-to-sample atoms store duration
    # information for a media's samples, providing a mapping from a time in a
    # media to the corresponding data sample
    # The sample-to-chunk atom contains a table that maps samples to chunks
    "stsc": "sample-to-chunk",
    "stco": 'chunk offset',  # Chunk offset atoms identify the location of
    # each chunk of data
    "stsz": 'sample size',  # You use sample size atoms to specify the size of
    # each sample
    # The composition offset atom contains a sample-by-sample mapping of the
    # decode-to-presentation time
    "ctts": 'composition offset',
    "stss": "sync sample",  # The sync sample atom identifies the key frames
}

CONTAINER_ATOMS = ["moov", "trak", "mdia", "minf", "dinf", "stbl"]
# undocumented atoms or redundant for metadata
_IGNORE_ATOMS = ["iods", "mdat"]
_ATOMS = {
    "pnot": (12, "I2x4s2x",
             ("Modification time", "Atom type"),
             (0,)),
    "vmhd": (12, "4xH6x",
             ("graphics mode",),
             ()),
    "mvhd": (100, "4x5IH10x36x7I",
             ("Creation time", "Modification time",
              "Time Scale",
              'Duration',
              'Preferred rate',
              'Preferred volume',
              'preview time',
              'preview duration',
              'poster time',
              'selection time',
              'selection duration',
              'current time',
              'next track id'
              ),
             (4, 8)),
    "tkhd": (84, "4x2I72x",
             ("Creation time", "Modification time"),
             (4, 8)),
    "mdhd": (24, "B3x4I2H",  # 3x is "flags"
             ("Version", "Creation time", "Modification time",
              "Time Scale", "Duration", "Language", "Quality"),
             (4, 8)),  # positions where dates are so we can modify them
    "smhd": (8, "4xH2x",
             ("balance",),
             ())
}

_VARIABLE_LEN_ATOMS = {
    "hdlr": (4 + 5 * 4, "4x5I",
             ("Component type",
              'component subtype',
              'component manufacturer',
              'component flags',
              'component flags mask'),
             (),
             "component name"
             ),
    "stsd": (8, "4xI",
             ("number of entries",),
             (),
             "sample description table"),
    "stts": (8, "4xI",
             ("number of entries",),
             (),
             "time-to-sample table"),
    "stsc": (8, "4xI",
             ("number of entries",),
             (),
             "sample-to-chunk table"),
    "stco": (8, "4xI",
             ("number of entries",),
             (),
             "chunk offset table"),
    "stsz": (12, "4xII",
             ("sample size", "number of entries",),
             (),
             "sample size table"),
    "ctts": (12, "4xII",
             ("entry count",),
             (),
             "composition offset table"),
    "stss": (12, "4xII",
             ("number of entries",),
             (),
             "sync sample table")
}

_VARIABLE_CHAINED_ATOMS = {
    "dref": (8, "4xI",
             ("number of entries",),
             (),
             "data references"
             )
}

_DATES = ("Creation time", "Modification time")


class Mov(object):
    def __init__(self, fn):
        self._fn = fn
        self._offsets = []
        self.metadata = dict()

    def parse(self):
        fsize = os.path.getsize(self._fn)
        # print("File: {} ({} bytes, {} MB)".format(
        #     self._fn, fsize, fsize / (1024.**2)))
        with open(self._fn, "rb") as self._f:
            self._parse(fsize)

    def _f_read(self, l):
        # print('reading '+str(l))
        return self._f.read(l)

    def _f_skip(self, l):
        self._f.seek(l, 1)

    def _parse(self, length, depth=0):
        n = 0
        while n < length:
            data = self._f_read(8)
            al, an = struct.unpack(">I4s", data)
            an = an.decode()

            if an in _ATOMS:
                self._parse_atom(an, al - 8, depth)
            elif an == "udta":
                self._parse_udta(al - 8, depth)
            elif an == "ftyp":
                self._read_ftyp(al - 8, depth)
            elif an in CONTAINER_ATOMS:
                self._parse(al - 8, depth + 1)
            elif an in _VARIABLE_LEN_ATOMS:
                self._parse_atom(an, al - 8, depth, variable=True)
            elif an in _VARIABLE_CHAINED_ATOMS:
                self._parse_atom(an, al - 8, depth, chained=True)
            elif an in _IGNORE_ATOMS:
                self._f_skip(al - 8)
            elif an == "meta":
                self._parse_meta(al - 8, depth)
            else:
                # print('unhandled thingie',al,an)
                if al == 1:
                    # 64 bit!
                    # print("64 bit header!")
                    al = struct.unpack(">Q", self._f_read(8))[0]
                    self._f_skip(al - 16)
                else:
                    self._f_skip(al - 8)
            n += al

    def _parse_atom(self, atom, length, depth, variable=False, chained=False):
        if variable:
            spec = _VARIABLE_LEN_ATOMS[atom]
        elif chained:
            spec = _VARIABLE_CHAINED_ATOMS[atom]
        else:
            spec = _ATOMS[atom]
            assert length == spec[0]

        pos = self._f.tell()
        data = self._f_read(length)
        if variable:
            v = struct.unpack(">" + spec[1], data[:spec[0]])
        elif chained:
            v = struct.unpack(">" + spec[1], data[:spec[0]])
        else:
            v = struct.unpack(">" + spec[1], data)
        k = spec[2]
        for i in range(0, len(k)):
            vv = v[i]
            if isinstance(vv, bytes):
                vv = vv.decode()
            elif k[i] in _DATES:
                vv = self._macdate2date(vv)
            # print("{}{}: {}".format(prefix, k[i], vv))
            metakey = k[i].lower().strip()
            if metakey not in self.metadata.keys():
                self.metadata[metakey] = vv

        if variable or chained:
            lim = 10
            realdata = data[spec[0]:]
            if len(realdata) > lim:
                # print("{}{}: {}{}{}{}".format(
                #     prefix, spec[4], realdata[:lim], '...',
                #     len(realdata)-lim,' more bytes'))
                pass
            else:
                # print("{}{}: {}".format(prefix, spec[4], realdata))
                pass

        for offset in spec[3]:
            self._offsets.append(pos + offset)

    def _parse_meta(self, length, depth):

        pos = self._f.tell()

        self._f_skip(16)

        header_version = self._f_read(4).decode("latin1")
        if header_version != "mdta":
            return

        self._f_skip(33)

        keys = []
        values = []

        h = self._f_read(4).decode("latin1")
        while h == "mdta":
            data = ""
            b = self._f_read(1)
            while b != b'\x00':
                data += b.decode("latin1")
                b = self._f_read(1)
            keys.append(data.lower().strip())
            while b == b'\x00':
                b = self._f_read(1)
            h = self._f_read(4).decode("latin1")

        i = 0
        while i < len(keys):
            h = ""
            while h != "data":
                b = self._f_read(1)
                while b == b'\x00':
                    b = self._f_read(1)
                b = self._f_read(1)
                if b != b'\x00':
                    h = b.decode("latin1")
                    h += self._f_read(3).decode("latin1")
            self._f_skip(8)
            data = ""
            b = self._f_read(1)
            while b != b'\x00' and self._f.tell() - pos < length:
                data += b.decode("latin1")
                b = self._f_read(1)
            values.append(data.strip())
            i += 1

        for i in range(0, min(len(keys), len(values))):

            key = keys[i]
            if key.startswith("com.apple.quicktime."):
                key = key[20:]

            self.metadata[key] = values[i]

        self._f.seek(pos + length, 0)

    def _read_ftyp(self, length, depth):
        data = self._f_read(8)
        brand, version = struct.unpack(">4sI", data)
        brand = brand.decode("latin1")
        # print("{}Brand: {}, version: {}".format(prefix, brand, version))
        self._f_skip(length - 8)

    def _parse_udta(self, length, depth):
        n = 0
        while n < length:
            atom_size, data_type = struct.unpack(">I4s", self._f_read(8))
            data_type = data_type.decode("latin1")
            n += atom_size

    def _macdate2date(self, md):
        d = datetime.datetime(1904, 1, 1) + datetime.timedelta(seconds=md)
        return "{} ({})".format(d, md)

    def _date2macdate(self, d):
        td = datetime.datetime(1970, 1, 1) - datetime.datetime(1904, 1, 1)
        dd = d + td
        sec = time.mktime(dd.timetuple()) - time.timezone
        return int(sec)

    def set_date(self, d):
        md = self._date2macdate(d)
        print("New date: {} ({})".format(d, md))
        with open(self._fn, "r+b") as f:
            print("Writing new date at {} positions...".format(
                len(self._offsets)))
            for offset in self._offsets:
                f.seek(offset)
                data = struct.pack(">I", md)
                f.write(data)
            f.flush()
            print("Touching file...")
            ts = time.mktime(d.timetuple())
            os.utime(self._fn, (ts, ts))
        print("Done!")


def get_mov_duration(mov_path, framerate=25):
    m = Mov(mov_path)
    m.parse()
    duration = (
        m.metadata['duration'] / float(m.metadata['time scale']) * framerate)
    return int(round(duration))
