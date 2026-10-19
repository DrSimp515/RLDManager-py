# resident.dll — Font Charset Patch

Binaries compared (same size, 5,468,160 bytes):

- `resident.dll` (original)
- `resident_modded.dll` (patched)

Total: **9 bytes changed across 8 locations**.

## Changes

Each VA points directly to the `0x80` byte being patched.

| # | VA | orig → patched | Context |
|---|---|---|---|
| 1 | `0x10002F33` | `80` → `00` | Descriptor ctor — `mov [esi+0x1C], 0x80` → `0` |
| 2 | `0x10017E29` | `80` → `00` | Descriptor ctor — same |
| 3 | `0x10257E77` | `80` → `00` | Descriptor ctor — same |
| 4 | `0x100622DB` | `80` → `00` | Reset-default family — `push 0x80` → `push 0` |
| 5 | `0x10063CA5` | `80` → `00` | Reset-default family — same |
| 6 | `0x100AE66B` | `80` → `00` | Finalizer preset font — `mov [esp+0x24], 0x80` → `0` |
| 7 | `0x102259E0` | `85` → `31` | Inline setter — `test eax,eax` → `xor eax,eax` (forces `esi+0x1BB = 0`) |
| 8 | `0x102CBCC8` | `3b` → `33` | Inline setter — `cmp eax,ebx` → `xor eax,eax` (forces `esi+0x1A3 = 0`) |

## Why

The EN build of Imouto Paradise 3 uses **cp1252/ANSI** for its text. The game's font config (`backlog.pa.fontCharset` / `info.fontCharset`) overrides the charset to ANSI (0), but the engine hardcodes `SHIFTJIS_CHARSET` (0x80) in multiple font creation and reset paths:

- Descriptor constructors — 3 sites
- Reset-default family — 2 sites
- Finalizer preset font (`0x100AE3B0`) — 1 site
- Inline setters — 2 sites

When 0x80 is in effect, GDI creates fonts with Shift-JIS charset and renders Latin text as mojibake. The `.rnf` ANSI override never gets a chance to take effect because the hardcoded value gets written after it.

## Result

This is a **font charset patch**: it replaces `SHIFTJIS_CHARSET` (0x80) with `ANSI_CHARSET` (0) at all 8 sites, so fonts are created with the correct codepage for the EN build and Latin characters render properly.