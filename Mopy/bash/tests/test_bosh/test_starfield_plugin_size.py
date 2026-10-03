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

import pytest

from ...bosh.save_headers import StarfieldSaveHeader

@pytest.mark.parametrize('metadata_length', [3, 23000])
def test_plugin_size_includes_high_word(monkeypatch, metadata_length):
    # No scaled masters are needed to exercise the common length field.
    monkeypatch.setattr(StarfieldSaveHeader, '_scale_flags', lambda self: [])
    save_header = object.__new__(StarfieldSaveHeader)
    save_header._master_info_block_size = {}
    plugin_name = b'Example.esm'
    creation_string = struct.pack('<H', metadata_length) + (
        b'A' * metadata_length)
    plugin_block = (b'\1' + struct.pack('<H', len(plugin_name)) + plugin_name
        + b'\1' + creation_string * 3 + b'\1' + b'\0\0')
    version_string = b'\3\0' + b'1.0'
    plugin_stream = io.BytesIO(b'\x96' + version_string * 2
        + struct.pack('<I', len(plugin_block)) + plugin_block)
    save_header._load_masters(plugin_stream)
    assert save_header.plugin_info_size == len(plugin_block)
    assert save_header.masters_regular == [plugin_name]
