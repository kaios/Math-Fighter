#!/usr/bin/env bash
# Builds a Debian/Ubuntu package at dist/mathfighter_<version>_<arch>.deb
# The package wraps the self-contained PyInstaller binary, so it needs no
# Python or pygame on the target machine.
set -e
cd "$(dirname "$0")"

VERSION=$(sed -n 's/^__version__ = "\(.*\)"/\1/p' mathfighter/config.py)
ARCH=$(dpkg --print-architecture)
PKG=mathfighter
ROOT=build/deb/${PKG}_${VERSION}_${ARCH}

./build_linux.sh

rm -rf "$ROOT"
install -Dm755 dist/MathFighter "$ROOT/usr/games/mathfighter"
install -Dm644 assets/icon.png "$ROOT/usr/share/icons/hicolor/512x512/apps/mathfighter.png"
install -Dm644 LICENSE "$ROOT/usr/share/doc/$PKG/copyright"

install -d "$ROOT/usr/share/applications"
cat > "$ROOT/usr/share/applications/mathfighter.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Math Fighter
Comment=Anime fighting game that teaches kids math
Exec=/usr/games/mathfighter
Icon=mathfighter
Terminal=false
Categories=Game;Education;KidsGame;
EOF

install -d "$ROOT/DEBIAN"
cat > "$ROOT/DEBIAN/control" <<EOF
Package: $PKG
Version: $VERSION
Architecture: $ARCH
Maintainer: Shawn Rapaz <shawnrapaz@gmail.com>
Section: games
Priority: optional
Installed-Size: $(du -sk "$ROOT/usr" | cut -f1)
Depends: libc6
Description: Math Fighter: Tournament of Numbers
 An anime-style fighting game for kids where every punch, kick and block
 is powered by a math question. Pick one of four fighters (addition,
 subtraction, multiplication or division), choose a level from 1 to 5,
 and battle through 4 stages to become the Math Tournament Champion.
EOF

cat > "$ROOT/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t /usr/share/icons/hicolor || true
fi
EOF
cp "$ROOT/DEBIAN/postinst" "$ROOT/DEBIAN/postrm"
chmod 755 "$ROOT/DEBIAN/postinst" "$ROOT/DEBIAN/postrm"

dpkg-deb --root-owner-group --build "$ROOT" "dist/${PKG}_${VERSION}_${ARCH}.deb"
echo "Done: dist/${PKG}_${VERSION}_${ARCH}.deb"
echo "Install with:  sudo apt install ./dist/${PKG}_${VERSION}_${ARCH}.deb"
