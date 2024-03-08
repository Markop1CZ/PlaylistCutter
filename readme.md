# GJO Playlist Cutter

Velmi jednoduchý a narychlo splácaný nástroj na vystřihnutí krátkých ukázek z adresáře zvukových souborů. Možnost nastavit fade in a fade out.

# Instalace (Windows)

- `pip install -r requirements.txt`
- stáhnout binárky `ffmpeg` buď [odsud](https://www.gyan.dev/ffmpeg/builds/) nebo [odsud](https://github.com/BtbN/FFmpeg-Builds/releases)
- extrahovat `ffmpeg` někam na disk
- přidat do `%path%` adresář `ffmpeg/bin`

# Použití

- spustit `pcutter.py`
- zvolit adresář se songy (podporuje MP3, WAV, FLAC)
- zvolit u každého zvuku začátek/délku a fade in/out
- export (vytvoří v původním adresáři adresář output)
- pokud chcete vytvářet další playlist, musíte restartovat program :D

# Info/doporučení

Nástroj exportuje soubory s původním názvem, ale konvertuje vždy do formátu MP3. 

## Usnadnění očíslování/pojmenování

Pokud soubory obsahují tagy, na rychlé pojmenování doporučuji například [Mp3tag](https://www.mp3tag.de/en/download.html).  
Pro případné očíslování může posloužit Multi-Rename Tool programu [Total Commander](https://www.ghisler.com/download.htm).
