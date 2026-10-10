# Microscope

Applicazione desktop per Ubuntu per acquisire immagini e video da una
telecamera USB ad alta risoluzione collegata a un microscopio.

## Funzioni

- **Selezione telecamera** tra quelle collegate (nome e percorso `/dev/videoN`).
- **Selezione risoluzione e frame rate** tra quelli supportati dalla telecamera.
- **Rotazione** 0°/90°/180°/270° e **specchiatura** sui due assi, con
  **memoria delle impostazioni per ogni telecamera**.
- **Navigazione immagine**:
  - zoom con la **rotellina del mouse**;
  - pan tenendo premuto il **click sinistro**;
  - **fit** alla finestra con il **click destro** (o doppio click, o `Ctrl+0`).
- **Fotografie in PNG** (anche JPEG/TIFF), ricordando l'ultima cartella usata.
- **Registrazione video compressa** (H.264 x264, con fallback MPEG-4),
  ricordando l'ultima cartella usata.

Tutte le preferenze sono salvate in `~/.config/microscope-app/settings.json`.

## Installazione

Il pacchetto `.deb` non include le librerie Python: le dichiara come
dipendenze e le scarica automaticamente dai repository Ubuntu.

```bash
# 1. Costruisci il pacchetto (non serve root)
make deb

# 2. Installalo (apt risolve le dipendenze)
sudo apt install ./dist/microscope-app_*_all.deb
```

Al termine l'applicazione compare nel menu delle applicazioni come
**Microscopio** e si avvia anche da terminale con:

```bash
microscope-app
```

### Disinstallazione

```bash
sudo apt remove microscope-app
# oppure, per rimuovere anche le impostazioni:
sudo apt purge microscope-app
```

Il file `~/.config/microscope-app/settings.json` viene rimosso solo con
`purge` tramite `rm -rf ~/.config/microscope-app` (le configurazioni utente
non sono gestite dal pacchetto).

## Dipendenze

Installate automaticamente come dipendenze del pacchetto:

| Pacchetto | Uso |
|---|---|
| `python3-pyside6.qtwidgets` | interfaccia grafica Qt |
| `python3-opencv` | acquisizione dalla telecamera |
| `python3-numpy` | elaborazione immagini |
| `python3-av` | compressione video (FFmpeg) |
| `python3-gi`, `gir1.2-gstreamer-1.0` | enumerazione telecamere |
| `gstreamer1.0-plugins-base`, `gstreamer1.0-plugins-good` | provider V4L2 |

## Sviluppo

```bash
make dev    # crea .venv e installa le dipendenze di sviluppo
make run    # avvia l'app dal sorgente
make clean  # rimuove build e cache
```

## Struttura del progetto

```
bin/microscope-app              launcher installato in /usr/bin
src/microscope_app/             codice dell'applicazione
packaging/                      file per il pacchetto .deb
build-deb.sh                    crea dist/microscope-app_<ver>_all.deb
Makefile                        scorciatoie build/install/run
```

## Scorciatoie da tastiera

| Tasto | Azione |
|---|---|
| `Ctrl+S` | salva fotografia |
| `Ctrl+R` | avvia/ferma la registrazione |
| `Ctrl+0` / `F` | adatta l'immagine alla finestra |
| `+` / `-` | zoom avanti / indietro |
