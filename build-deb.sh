#!/usr/bin/env bash
#
# Build the Debian package (.deb) for microscope-app.
#
# It does not require root privileges: it uses `dpkg-deb --root-owner-group`.
# The resulting package is installed with:
#
#     sudo apt install ./dist/microscope-app_<version>_all.deb
#
# and removed with:
#
#     sudo apt remove microscope-app
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PKG="microscope-app"
VERSION="$(sed -n 's/^__version__[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' \
    "$ROOT/src/microscope_app/__init__.py" | head -n1)"
VERSION="${VERSION:-1.0.0}"
ARCH="${ARCH:-all}"

MAINTAINER="${MAINTAINER:-Microscope contributors <microscope@localhost>}"
HOMEPAGE="${HOMEPAGE:-https://example.org/microscope-app}"

BUILD="$ROOT/build/${PKG}_${VERSION}_${ARCH}"
DIST="$ROOT/dist"
OUTPUT="$DIST/${PKG}_${VERSION}_${ARCH}.deb"

# Dependencies: all available in the Ubuntu repositories.
DEPENDS="python3 (>= 3.10), python3-pyside6.qtwidgets, python3-opencv, python3-numpy, python3-av, python3-gi, gir1.2-gstreamer-1.0, gstreamer1.0-plugins-base, gstreamer1.0-plugins-good, libgl1"

echo ">> Building $PKG $VERSION ($ARCH)"

rm -rf "$BUILD"
mkdir -p "$BUILD/DEBIAN"

# --- Program ---------------------------------------------------------------
install -Dm755 "$ROOT/bin/microscope-app" "$BUILD/usr/bin/microscope-app"

mkdir -p "$BUILD/usr/lib/microscope-app"
cp -r "$ROOT/src/microscope_app" "$BUILD/usr/lib/microscope-app/"
find "$BUILD/usr/lib/microscope-app" -type d -name '__pycache__' -prune -exec rm -rf {} +

# --- Desktop integration ---------------------------------------------------
install -Dm644 "$ROOT/packaging/microscope-app.desktop" \
    "$BUILD/usr/share/applications/microscope-app.desktop"
install -Dm644 "$ROOT/packaging/microscope-app.appdata.xml" \
    "$BUILD/usr/share/metainfo/microscope-app.appdata.xml"
install -Dm644 "$ROOT/src/microscope_app/resources/microscope-app.svg" \
    "$BUILD/usr/share/icons/hicolor/scalable/apps/microscope-app.svg"

# --- Documentation ---------------------------------------------------------
install -Dm644 "$ROOT/packaging/copyright" \
    "$BUILD/usr/share/doc/$PKG/copyright"
gzip -9n -c "$ROOT/packaging/changelog" > "$BUILD/usr/share/doc/$PKG/changelog.gz"

# --- Maintainer scripts ----------------------------------------------------
install -Dm755 "$ROOT/packaging/postinst" "$BUILD/DEBIAN/postinst"
install -Dm755 "$ROOT/packaging/postrm" "$BUILD/DEBIAN/postrm"

# --- Standard permissions --------------------------------------------------
find "$BUILD" -type d -exec chmod 755 {} +
find "$BUILD" -type f -exec chmod 644 {} +
chmod 755 "$BUILD/usr/bin/microscope-app"
chmod 755 "$BUILD/DEBIAN/postinst" "$BUILD/DEBIAN/postrm"

# --- Control ---------------------------------------------------------------
INSTALLED_SIZE="$(du -sk --exclude=DEBIAN "$BUILD" | cut -f1)"

cat > "$BUILD/DEBIAN/control" <<EOF
Package: $PKG
Version: $VERSION
Section: science
Priority: optional
Architecture: $ARCH
Depends: $DEPENDS
Installed-Size: $INSTALLED_SIZE
Maintainer: $MAINTAINER
Homepage: $HOMEPAGE
Description: Capture images and videos from a USB microscope
 Microscope is a simple desktop application that acquires real-time images
 from a high-resolution USB camera attached to a microscope.
 .
 Main features:
  * selection of camera, resolution and frame rate;
  * image rotation and mirroring, remembered per camera;
  * zoom with the wheel, pan with the left click, fit with the right click;
  * PNG photo capture, remembering the last folder;
  * compressed video recording (H.264 / MPEG-4).
  * English and Italian interface.
 .
 Microscope e' una semplice applicazione desktop che acquisisce immagini in
 tempo reale da una telecamera USB ad alta risoluzione collegata a un
 microscopio.
 .
 Caratteristiche principali:
  * selezione di telecamera, risoluzione e frame rate;
  * rotazione e specchiatura dell'immagine, con memoria per telecamera;
  * zoom con la rotellina, pan con il click sinistro, fit con il click destro;
  * salvataggio di fotografie in PNG con memoria dell'ultima cartella;
  * registrazione video compressa (H.264 / MPEG-4);
  * interfaccia in inglese e italiano.
EOF

# --- Build -----------------------------------------------------------------
mkdir -p "$DIST"
dpkg-deb --build --root-owner-group "$BUILD" "$OUTPUT" >/dev/null

echo ">> Created: $OUTPUT"
echo ">> Install with: sudo apt install $OUTPUT"
