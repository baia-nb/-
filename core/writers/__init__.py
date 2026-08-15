# -*- coding: utf-8 -*-
"""格式写入器 / format writers."""
from . import txt, ibi, dsb, ldlmusic, musicjson, mcstructure as mcstruct_writer

def write_txt(structure, out_path=None, name=None):
    return txt.write(structure, out_path, name)

def write_ibi(structure, out_path=None, name=None):
    return ibi.write(structure, out_path, name)

def write_dsb(structure, out_path=None, name=None):
    return dsb.write(structure, out_path, name)

def write_ldlmusic(midi_data, out_path=None, name=None):
    return ldlmusic.write(midi_data, out_path, name)

def write_musicjson(midi_data, out_path=None, name=None):
    return musicjson.write(midi_data, out_path, name)

def write_mcstructure(structure, out_path=None, name=None):
    return mcstruct_writer.write(structure, out_path, name)
