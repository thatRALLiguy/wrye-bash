# -*- coding: utf-8 -*-
#
# GPL License and Copyright Notice ============================================
#  This file is part of Wrye Bash.
#
#  Wrye Bash is free software: you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation, either version 3
#  of the License, or (at your option) any later version.
#
#  Wrye Bash is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Wrye Bash.  If not, see <https://www.gnu.org/licenses/>.
#
#  Wrye Bash copyright (C) 2005-2009 Wrye, 2010-2026 Wrye Bash Team
#  https://github.com/wrye-bash
#
# =============================================================================
import io
import struct
import zlib

import pytest

from ...bosh.save_headers import _ABcpsSaveHeader
from ...exception import SaveHeaderError

class _BcpsProbe(_ABcpsSaveHeader):
    save_magic = b'TEST'
    __slots__ = (*_ABcpsSaveHeader._bcps_unpackers, '_bcps_rest', 'payload')

    def _load_header_data(self, ins, load_image=False):
        self.payload = ins.read()

def _container(payload, chunk_length, alignment=16):
    uncompressed = b'TEST' + payload
    compressed = [zlib.compress(uncompressed[pos:pos + chunk_length])
        for pos in range(0, len(uncompressed), chunk_length)]
    chunk_table = b''.join(struct.pack('<I', len(part)) for part in compressed)
    prefix = struct.pack('<4sIQQQQQQQI4s', b'BCPS', 1, 72, 0,
        72 + len(chunk_table), len(uncompressed), 0, chunk_length,
        alignment, 0, b'ZIP ')
    # Final alignment padding is unnecessary for locating subsequent chunks.
    framed = b''.join(part + b'\0' * (-len(part) % alignment)
        for part in compressed[:-1]) + compressed[-1]
    return prefix + chunk_table + framed

@pytest.mark.parametrize('chunk_length', [16, 128])
def test_bcps_reads_all_chunks_and_short_final_chunk(chunk_length):
    payload = bytes(range(93))
    save_header = object.__new__(_BcpsProbe)
    save_header.load_header(io.BytesIO(_container(payload, chunk_length)))
    assert save_header.payload == payload

@pytest.mark.parametrize('field_offset,replacement', [
    (8, 0), (24, 0), (48, 0), (56, 3)])
def test_bcps_rejects_invalid_framing(field_offset, replacement):
    encoded = bytearray(_container(b'example', 16))
    struct.pack_into('<Q', encoded, field_offset, replacement)
    save_header = object.__new__(_BcpsProbe)
    with pytest.raises(SaveHeaderError):
        save_header.load_header(io.BytesIO(encoded))

def test_bcps_rejects_truncated_chunk():
    encoded = _container(b'example', 16)[:-1]
    save_header = object.__new__(_BcpsProbe)
    with pytest.raises(SaveHeaderError):
        save_header.load_header(io.BytesIO(encoded))

def test_bcps_rejects_bad_checksum():
    encoded = bytearray(_container(b'example', 16))
    encoded[-1] ^= 1
    with pytest.raises(SaveHeaderError):
        object.__new__(_BcpsProbe).load_header(io.BytesIO(encoded))

def test_bcps_rejects_incorrect_output_length():
    encoded = bytearray(_container(b'example', 16))
    struct.pack_into('<Q', encoded, 32, 10)
    with pytest.raises(SaveHeaderError):
        object.__new__(_BcpsProbe).load_header(io.BytesIO(encoded))

def test_bcps_rejects_other_codecs():
    encoded = bytearray(_container(b'example', 16))
    encoded[68:72] = b'LZ4 '
    with pytest.raises(SaveHeaderError):
        object.__new__(_BcpsProbe).load_header(io.BytesIO(encoded))
