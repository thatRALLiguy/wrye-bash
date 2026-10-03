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
from types import SimpleNamespace

import pytest

from ... import load_order
from ...bolt import FName
from ...bosh.save_headers import StarfieldSaveHeader

@pytest.mark.parametrize('form_version', [122, 139])
@pytest.mark.parametrize('plugin_name', [b'Starfield.esm', b'STARFIELD.ESM'])
def test_pinned_master_has_no_creation_metadata(monkeypatch, form_version,
        plugin_name):
    monkeypatch.setattr(load_order, '_lo_handler', SimpleNamespace(
        pin_active_state={FName('Starfield.esm'): True}))
    save_header = object.__new__(StarfieldSaveHeader)
    save_header._formVersion = form_version
    save_header._master_info_block_size = {}
    plugin_entry = struct.pack('<H', len(plugin_name)) + plugin_name
    plugin_stream = io.BytesIO(plugin_entry + b'NEXT')
    assert save_header._unpack_master(plugin_stream) == plugin_name
    assert plugin_stream.tell() == len(plugin_entry)
    assert plugin_stream.read() == b'NEXT'

@pytest.mark.parametrize('form_version', [122, 139])
def test_unpinned_master_consumes_creation_metadata(monkeypatch, form_version):
    monkeypatch.setattr(load_order, '_lo_handler', SimpleNamespace(
        pin_active_state={FName('Starfield.esm'): True}))
    save_header = object.__new__(StarfieldSaveHeader)
    save_header._formVersion = form_version
    save_header._master_info_block_size = {}
    plugin_name = b'Example.esm'
    plugin_entry = struct.pack('<H', len(plugin_name)) + plugin_name
    plugin_stream = io.BytesIO(plugin_entry + b'\0\0' * 3 + b'\1NEXT')
    assert save_header._unpack_master(plugin_stream) == plugin_name
    assert plugin_stream.read() == b'NEXT'
