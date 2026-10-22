# rld_engine.py — Python port of RLDManager/Main.cs by marcussacana
# handles XOR cipher, string import/export, and brute-force key search
#
# EN builds (e.g. Imouto Paradise 3 [EN]) use cp1252 instead of cp932:
#   RLD bytes → GDI reads them as cp1252 → Unicode → glyph in the font
#   e.g. 0xED = í, 0xE1 = á, 0xF1 = ñ
#   is_char takes the active encoding so cp1252 high bytes aren't mistaken
#   for cp932 lead bytes

import os
import re
import struct
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

KNOWN_KEYS: dict[str, int] = {
    "Sakura no Mori Dreamers [JP]":        0xAD2B78EA,
    "Sakura no Mori Dreamers [JP] [Alt]":  0x0C328491,
    "Princess Evangile":                   0x39AA8BA0,
    "Princess Evangile W":                 0xE69A420B,
    "Magical Marriage Lunatics [JP]":      0xC9E849B1,
    "Magical Marriage Lunatics [EN]":      0xFA267D75,
    "Imouto Paradise 3 [JP]":             0x2A17122A,
    "Imouto Paradise 3 [EN]":             0x2A18A1A4,
    "Imouto Paradise 3 [def]":            0xAE85A916,
}

# which scripts use cp1252 (latin) instead of cp932 (japanese)
# GDI with ANSI_CHARSET on the EN build interprets bytes as cp1252:
#   RLD bytes → cp1252 → Unicode → glyph in the font
#   e.g. 0xED (í) → U+00ED → renders correctly with a latin font
KEY_ENCODING_MAP: dict[int, str] = {
    0x2A17122A: "cp932",   # Imouto Paradise 3 [JP] — scripts JP en Shift-JIS
    0x2A18A1A4: "cp1252",  # Imouto Paradise 3 [EN]
    0xAE85A916: "cp1252",  # Imouto Paradise 3 [def] — registros + font spec
    0xFA267D75: "cp1252",
    0x39AA8BA0: "cp1252",
    0xE69A420B: "cp1252",
}

SPEAKER_MAP: dict[int, str] = {
    1: "Protagonist", 3: "Protagonist",
    4: "Sakura", 5: "Rika", 6: "Hinata",
    7: "Hiharu", 8: "Zakuro",
    9: "Hare",
    10: "NPC", 11: "NPC", 12: "NPC", 13: "NPC", 14: "NPC",
    0: "—",
}

SPEAKER_GENDER: dict[int, str] = {
    1: "M", 3: "M",
    4: "F", 5: "F", 6: "F", 7: "F", 8: "F", 9: "F",
    10: "?", 11: "?", 12: "?", 13: "?", 14: "?",
    0: "?",
}


def encoding_for_key(key: int) -> str:
    return KEY_ENCODING_MAP.get(key, "cp1252")


def get_local_keys() -> list[int]:
    keys = []
    if os.path.exists("RLDKeys.txt"):
        for line in open("RLDKeys.txt").read().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                if line.lower().startswith("0x"):
                    keys.append(int(line, 16))
                else:
                    keys.append(int(line))
            except ValueError:
                pass
    return keys

def get_dw(data: bytearray, pos: int) -> int:
    return struct.unpack_from("<I", data, pos)[0]


def set_dw(data: bytearray, pos: int, val: int):
    struct.pack_into("<I", data, pos, val & 0xFFFFFFFF)


def get_string_at(data: bytearray, pos: int, enc: str) -> str:
    end = pos
    while end < len(data) and data[end] != 0x00:
        end += 1
    raw = bytes(data[pos:end])
    try:
        return raw.decode(enc, errors="replace")
    except Exception:
        return raw.decode("latin-1", errors="replace")

def _generate_seed_buffer(seed: int) -> list[int]:
    state = seed & 0xFFFFFFFF
    remaining = 0x270
    buf = []
    while remaining:
        product = (state * 0x10DCD) & 0xFFFFFFFF
        entry = (state & 0xFFFF0000) | (((product + 1) >> 0x10) & 0x0000FFFF)
        buf.append(entry)
        state = (state * 0x1C587629 + 0x10DCE) & 0xFFFFFFFF
        remaining -= 1
    return buf


def _mix_key_round(i: int, keys: list[int], ori_keys: list[int]) -> int:
    current = keys[i]
    nxt = i + 1
    if nxt >= len(keys):
        nxt = 0
    mixed = ((keys[nxt] ^ current) & 0x7FFFFFFF) ^ current
    carry = mixed & 1
    mixed = (mixed >> 1) & 0x7FFFFFFF
    if carry:
        mixed ^= 0x9908B0DF
    idx = i + 0x18D
    if idx >= len(keys):
        idx -= len(keys)
    mixed ^= ori_keys[idx]
    ori_keys[i] = mixed & 0xFFFFFFFF
    mixed &= 0xFFFFFFFF
    mixed ^= (mixed >> 0x0B)
    mixed &= 0xFFFFFFFF
    mixed ^= ((mixed & 0xFF3A58AD) << 0x7) & 0xFFFFFFFF
    mixed &= 0xFFFFFFFF
    mixed ^= ((mixed & 0xFFFFDF8C) << 0xF) & 0xFFFFFFFF
    mixed &= 0xFFFFFFFF
    return ((mixed >> 0x12) ^ mixed) & 0xFFFFFFFF


def gen_key_table(seed: int) -> list[int]:
    keys = _generate_seed_buffer(seed)
    ori  = list(keys)
    for i in range(len(keys)):
        k = _mix_key_round(i, keys, ori)
        keys[i] = (k ^ seed) & 0xFFFFFFFF
    return keys

def xor_script(data: bytearray, key: int):
    block_count = len(data)
    if block_count > 0xFFCF:
        block_count = 0xFFCF
    block_count -= block_count % 4
    key_table = gen_key_table(key)
    table_index = 0
    offset = 0x10
    while offset < block_count:
        encrypted = get_dw(data, offset)
        keystream = key_table[table_index & 0xFF]
        set_dw(data, offset, keystream ^ encrypted)
        offset += 4
        table_index += 1

def is_wtf(b: int) -> bool:
    """Magical Marriage Lunatics [EN] special control bytes."""
    return b == 0x0C or (0xAA <= b <= 0xAF)


# cp932 lead byte ranges — only meaningful in japanese encodings
_CP932_LEAD = frozenset(range(0x88, 0xA0)) | {0x81, 0x82, 0x83} | frozenset(range(0xE0, 0xF0))

# cp1252 undefined slots — not printable, skip them
_CP1252_UNDEF = frozenset([0x81, 0x8D, 0x8F, 0x90, 0x9D])


def is_char(b: int, enc: str = "cp1252") -> tuple[bool, bool]:
    """
    Returns (valid, multibyte).

    Si enc es cp932/shift-jis: 0xE0-0xEF y otros rangos son lead bytes de dos bytes.
    Si enc es cp1252/latin-1/mac_roman: 0x80-0xFE son chars de un byte.
    """
    is_japanese = enc.lower().replace("-", "").replace("_", "") in ("cp932", "shiftjis", "shift_jis")

    # always valid regardless of encoding
    if (0x20 <= b <= 0x7F) or b in (0x0A, 0x0D):
        return True, False

    if is_japanese:
        if b in _CP932_LEAD:
            return True, True
        return False, False
    else:
        # cp1252: 0x80-0xFE are all single-byte printable chars
        if 0x80 <= b <= 0xFE:
            if b in _CP1252_UNDEF:
                return False, False
            return True, False
        return False, False

def resolve_speaker(char_id: int) -> str:
    return SPEAKER_MAP.get(char_id, f"ID:{char_id}")

def resolve_gender(char_id: int) -> str:
    return SPEAKER_GENDER.get(char_id, "?")

_META_RE   = re.compile(r"^##\s+FILE:\s*(.+?)\s+INDEX:\s*(\d+)\s*$")
_ENTRY_RE  = re.compile(r"^(.+?)\s+\(([MF?])\):\s*(.*)")


def build_text_line(speaker: str, gender: str, text: str) -> str:
    safe = text.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")
    return f"{speaker} ({gender}): {safe}"


def parse_text_line(line: str) -> Optional[tuple[str, str, str]]:
    m = _ENTRY_RE.match(line)
    if not m:
        return None
    speaker = m.group(1).strip()
    gender  = m.group(2)
    text    = m.group(3).replace("\\n", "\n")
    return speaker, gender, text

_last_known_key: int = 0


class RLD:
    def __init__(self, script_bytes: bytes, key: Optional[int] = None):
        self.script      = bytearray(script_bytes)
        self.offsets:      list[int] = []
        self.byte_lengths: list[int] = []
        self.speaker_ids:  list[int] = []
        self._decrypted  = False

        if key is None:
            key = self._select_key()
            if key == 0xFFFFFFFF:
                raise ValueError("Unknown encryption key")
        self.key      = key
        self.encoding = encoding_for_key(key)

    def _select_key(self) -> int:
        global _last_known_key
        candidates = list(KNOWN_KEYS.values()) + get_local_keys()
        candidates = list(reversed(candidates))

        if _last_known_key:
            try:
                r = RLD(bytes(self.script), _last_known_key)
                if len(r.import_strings()) > 2:
                    return _last_known_key
            except Exception:
                pass

        for k in candidates:
            try:
                r = RLD(bytes(self.script), k)
                if len(r.import_strings()) > 2:
                    _last_known_key = k
                    return k
            except Exception:
                pass
        return 0xFFFFFFFF

    def _string_length_at(self, at: int) -> int:
        length = 0
        while self.script[at + length] != 0x00:
            length += 1
        return length

    def _is_valid_string(self, at: int) -> bool:
        while self.script[at] != 0x00:
            b = self.script[at]
            ok, multibyte = is_char(b, self.encoding)
            if not ok and not is_wtf(b):
                return False
            at += 2 if multibyte else 1
        return True

    def _is_valid_double_string(self, at: int) -> bool:
        if self._is_valid_string(at):
            at += self._string_length_at(at) + 1
            return self._is_valid_string(at)
        return False

    def _is_command_string(self, ptr: int) -> bool:
        s = get_string_at(self.script, ptr, self.encoding)
        minified = ""
        for c in s:
            if c in ("\u300C", "\u300D"):
                return False
            if c.isdigit() or c in ",.-*:#@":
                continue
            b = ord(c) & 0xFF
            if is_wtf(b):
                continue
            minified += c
        return len(minified) < len(s) / 4

    def _find_speaker_id(self, dialogue_offset: int) -> int:
        window = 128
        start  = max(4, dialogue_offset - window)
        script = self.script
        length = len(script)
        for j in range(dialogue_offset - 4, start - 1, -1):
            if (script[j]     == 0xFF and
                script[j + 1] == 0xFF and
                script[j + 2] == 0x52 and
                script[j + 3] == 0x0E and
                j + 8 <= length):
                return get_dw(script, j + 4)
            if (j >= 2 and
                script[j]     == 0x1C and
                script[j + 1] == 0x00 and
                script[j + 2] == 0x0E and
                script[j + 3] == 0x52 and
                j + 8 <= length):
                return get_dw(script, j + 4)
        return 0

    def _scan_offsets(self, pos: int) -> list[int]:
        script = self.script
        length = len(script)
        enc = self.encoding

        if pos + 7 < length:
            if script[pos] == 0xFF and script[pos + 1] == 0xFF:
                if script[pos + 2] == 0x2A and script[pos + 3] == 0x00:
                    string_start = pos + 4
                    ok1, _ = is_char(script[string_start], enc)
                    ok2, _ = is_char(script[string_start + 1], enc)
                    if ok1 and ok2:
                        return [string_start]

                if (script[pos + 2] == 0xFF and script[pos + 3] == 0xFF):
                    ok, _ = is_char(script[pos + 4], enc)
                    if ok and self._is_valid_string(pos + 4):
                        if self._is_valid_double_string(pos + 4):
                            ptr = pos + 4
                            result = [ptr]
                            while script[ptr] != 0x00:
                                ptr += 1
                            ptr += 1
                            result.append(ptr)
                            return result
                        return [pos + 4]

            value = get_dw(script, pos)
            if value == 0x64 and pos + 4 < length:
                ok, _ = is_char(script[pos + 4], enc)
                if ok:
                    if script[pos + 4] == 0x2A:
                        return [pos + 6]
                    found = [pos + 4]
                    if self._is_valid_double_string(pos + 4):
                        ptr = pos + 4
                        ptr += self._string_length_at(ptr)
                        found.append(ptr)
                    return found

        if pos + 3 < length:
            if script[pos] == 0x2A and script[pos + 1] == 0x00:
                ptr = pos - 1
                while ptr > 0x10 and script[ptr] == 0x00:
                    ptr -= 1
                i = pos + 2
                if script[ptr] == 0xFF and ptr > 0 and script[ptr - 1] == 0xFF:
                    ok1, _ = is_char(script[i], enc) if i < length else (False, False)
                    ok2, _ = is_char(script[i + 2], enc) if i + 2 < length else (False, False)
                    if ok1 and ok2:
                        found = [i]
                        while i < length and script[i] != 0x00:
                            i += 1
                        i += 1
                        if i < length:
                            ok3, _ = is_char(script[i], enc)
                            ok4, _ = is_char(script[i + 2], enc) if i + 2 < length else (False, False)
                            if ok3 and ok4:
                                found.append(i)
                        return found

        return []

    def import_strings(self) -> list[str]:
        if not self._decrypted:
            self._decrypted = True
            xor_script(self.script, self.key)

        self.offsets      = []
        self.byte_lengths = []
        self.speaker_ids  = []
        offsets_set: set[int] = set()

        for i in range(len(self.script)):
            for ptr in self._scan_offsets(i):
                if ptr in offsets_set:
                    continue
                if self._string_length_at(ptr) < 3:
                    continue
                if self._is_command_string(ptr):
                    continue
                offsets_set.add(ptr)
                self.offsets.append(ptr)

        strings: list[str] = []
        for ptr in self.offsets:
            s   = get_string_at(self.script, ptr, self.encoding)
            bl  = self._string_length_at(ptr)
            sid = self._find_speaker_id(ptr)
            strings.append(s)
            self.byte_lengths.append(bl)
            self.speaker_ids.append(sid)

        return strings

    def get_speakers(self) -> list[str]:
        return [resolve_speaker(sid) for sid in self.speaker_ids]

    def get_genders(self) -> list[str]:
        return [resolve_gender(sid) for sid in self.speaker_ids]

    def export_strings(self, strings: list[str]) -> bytes:
        if len(strings) != len(self.offsets):
            raise ValueError("String count mismatch — cannot add or remove entries")

        enc = self.encoding   # cp1252 for EN builds — GDI ANSI_CHARSET maps bytes to U+00xx

        # merge forward with a cursor, handles overlaps
        # (ported from the original C# export which did reverse-replace)
        items = sorted(zip(self.offsets, self.byte_lengths, strings),
                       key=lambda triple: triple[0])

        output = bytearray()
        oc = 0
        for pos, old_length, new_text in items:
            if pos < oc:
                del output[pos:]
                oc = pos
            if pos > oc:
                output.extend(self.script[oc:pos])
            # cp1252 special chars: á=0xE1 é=0xE9 í=0xED ó=0xF3 ú=0xFA ñ=0xF1
            try:
                raw = new_text.encode(enc, errors="strict") + b"\x00"
            except UnicodeEncodeError:
                raw = new_text.encode("latin-1", errors="replace") + b"\x00"
            output.extend(raw)
            oc = pos + old_length + 1
        if oc < len(self.script):
            output.extend(self.script[oc:])

        xor_script(output, self.key)
        return bytes(output)

    def xor(self, data: bytearray):
        xor_script(data, self.key)


def extract_to_text(rld: "RLD", filename: str, strings: list[str],
                    speakers: list[str], genders: list[str]) -> list[str]:
    lines: list[str] = []
    for idx, (spk, gen, text) in enumerate(zip(speakers, genders, strings)):
        lines.append(f"## FILE: {filename}  INDEX: {idx}")
        lines.append(build_text_line(spk, gen, text))
    return lines


def parse_text_block(text_content: str) -> dict[str, dict[int, str]]:
    result: dict[str, dict[int, str]] = {}
    current_file: Optional[str] = None
    current_index: Optional[int] = None

    for raw_line in text_content.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        m = _META_RE.match(line)
        if m:
            current_file  = m.group(1)
            current_index = int(m.group(2))
            if current_file not in result:
                result[current_file] = {}
            continue

        parsed = parse_text_line(line)
        if parsed and current_file is not None and current_index is not None:
            _speaker, _gender, text = parsed
            result[current_file][current_index] = text
            current_index = None

    return result


def apply_translations(rld: "RLD", original_strings: list[str],
                       translations: dict[int, str]) -> list[str]:
    merged = list(original_strings)
    for idx, text in translations.items():
        if 0 <= idx < len(merged) and text.strip():
            merged[idx] = text
    return merged

try:
    import keyfinder_fast as _kf
    _KF_AVAILABLE = True
except ImportError:
    _KF_AVAILABLE = False

class KeyFinder:
    def __init__(self, script: bytes):
        self.script   = script
        self.progress = 0
        self.found: list[int] = []
        self._stop    = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.on_progress = None
        self.on_done     = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _test_seed(self, seed: int) -> Optional[int]:
        if self._stop.is_set():
            return None
        script_copy = bytearray(self.script)
        rst = get_dw(script_copy, 0x10)

        state = seed & 0xFFFFFFFF
        end = 0x18E
        buf = [0] * end
        idx = 0
        while idx < end:
            product = (state * 0x10DCD + 1) & 0xFFFFFFFF
            buf[idx] = (state & 0xFFFF0000) | ((product >> 0x10) & 0x0000FFFF)
            idx += 1
            state = (state * 0x1C587629 + 0x10DCE) & 0xFFFFFFFF

        current = buf[0]
        nxt = 1 if 1 < len(buf) else 0
        mixed = ((buf[nxt] ^ current) & 0x7FFFFFFF) ^ current
        carry = mixed & 1
        mixed = (mixed >> 1) & 0x7FFFFFFF
        if carry:
            mixed ^= 0x9908B0DF
        mixed ^= buf[0x18D]
        buf[0] = mixed & 0xFFFFFFFF

        mixed ^= (mixed >> 0x0B)
        mixed ^= (mixed & 0xFF3A58AD) << 0x7
        mixed ^= (mixed & 0xFFFFDF8C) << 0xF
        key = ((mixed >> 0x12) ^ mixed) & 0xFFFFFFFF
        key = (key ^ seed) & 0xFFFFFFFF

        if (key ^ rst) & 0xFFFFFFFF < 0xF:
            try:
                r = RLD(bytes(script_copy), seed)
                if len(r.import_strings()) >= 2:
                    return seed
            except Exception:
                pass
        return None

    def _test_range(self, start: int, end: int) -> Optional[int]:
        for seed in range(start, end):
            if self._stop.is_set():
                return None
            result = self._test_seed(seed)
            if result is not None:
                return result
        return None

    def _run(self):
        if _KF_AVAILABLE:
            result = _kf.scan(self.script, self._stop, self.on_progress)
            self.found = [result] if result is not None else []
            if self.on_done:
                self.on_done(self.found)
            return

        TOTAL = 0xFFFFFFFF
        WORKER_CHUNK = 4096
        found: list[int] = []
        max_workers = os.cpu_count() or 4

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            cursor = 0
            while cursor < TOTAL and not self._stop.is_set() and not found:
                futures = []
                for _ in range(max_workers):
                    if cursor >= TOTAL:
                        break
                    end = min(cursor + WORKER_CHUNK, TOTAL)
                    futures.append(pool.submit(self._test_range, cursor, end))
                    cursor = end

                for future in as_completed(futures):
                    if self._stop.is_set():
                        break
                    result = future.result()
                    if result is not None:
                        found.append(result)
                        self._stop.set()
                        break

                if self.on_progress:
                    self.on_progress(cursor, TOTAL)
                if found:
                    break

        self.found = found
        if self.on_done:
            self.on_done(found)
