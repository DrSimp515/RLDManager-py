# RLD Manager

Multi-file editor for ExHIBIT engine RLD script files.  
Built specifically for working on **Imouto Paradise 3 [EN]**.

Supports text extraction, reinsertion, XOR cipher, brute-force key search, and GYU image decoding.

## Features

- Open multiple `.rld` files as tabs
- Extract and reinsert translated strings
- XOR cipher with key selection from a built-in list or `RLDKeys.txt`
- Brute-force key finder with automatic backend selection (CUDA / Numba / Python)
- Export strings to `.txt` (tagged or plain)
- Import translations from file
- GYU image viewer/decoder
- Light/dark theme, multi-language UI (en/es/pt/fr/it/de/ru)

## Requirements

```
Python 3.11+
PyQt6
PyQt-Fluent-Widgets
```

Install dependencies:

```
pip install -r requirements.txt
```

### Optional — faster key search

The brute-force key finder automatically picks the fastest backend available:

| Backend | Speedup | Install |
|---------|---------|---------|
| CUDA (Nvidia GPU) | ~500–2000x | `pip install cupy-cuda12x` ¹ |
| Numba (CPU JIT) | ~20–100x | `pip install numba numpy` |
| Python (default) | baseline | nothing |

¹ Replace `12x` with your CUDA version (`11x`, `12x`, etc.).  
Without either package the app falls back to the built-in Python scanner automatically.

## Run

```
python rldmanager-py/main.py
```

## Build (Windows executable)

```
pyinstaller rldmanager-py.spec
```

## Special characters (EN build)

The EN build of Imouto Paradise 3 uses **ANSI_CHARSET** for its fonts, which means the engine reads RLD script bytes as **cp1252** and passes them to GDI as-is. The font file needs to include the corresponding Latin glyphs.

Out of the box the engine hardcodes `SHIFTJIS_CHARSET` (0x80) in several font creation and reset paths, which breaks Latin text rendering. To fix this you need to patch `resident.dll` — see [resident_modded diff](docs/diff_resident_modded.md) for the exact byte changes (9 bytes across 8 locations).

Once patched, special characters work as follows:

| Char | cp1252 byte |
|------|-------------|
| á    | `0xE1`      |
| é    | `0xE9`      |
| í    | `0xED`      |
| ó    | `0xF3`      |
| ú    | `0xFA`      |
| ñ    | `0xF1`      |

## Key file

To add custom keys, create `RLDKeys.txt` in the working directory with one key per line (decimal or `0x` hex):

```
0xAD2B78EA
0x39AA8BA0
```

## Credits

**Original C# RLD engine**  
marcussacana — https://github.com/marcussacana/RLDManager

**GYU image decoder** — ported from `ImageGYU.cs`  
morkt — https://github.com/morkt/GARbro  
Copyright (C) 2015–2020 by morkt — MIT License

**Python port & application**  
Dr.Simp

## License

MIT License — see [LICENSE](LICENSE)

> The GYU decoder (`gyu_engine.py`) is a Python port of `ImageGYU.cs` from GARbro by morkt,
> distributed under the MIT License. The full copyright notice is retained in that file.
