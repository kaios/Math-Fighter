#!/usr/bin/env bash
# Builds dist/MathFighter-<version>.exe on Linux, using Windows Python under Wine.
# (On a Windows PC, use build_windows.bat instead.)
# Needs: wine (64-bit), curl, unzip.
set -e
cd "$(dirname "$0")"

PYVER=3.11.9
VERSION=$(sed -n 's/^__version__ = "\(.*\)"/\1/p' mathfighter/config.py)
export WINEPREFIX=${WINEPREFIX:-$HOME/.wine-mathfighter}
export WINEDEBUG=-all
PYDIR="$WINEPREFIX/drive_c/Python311"

# Python's official installer does not run under Wine, but the NuGet package
# is the same Python as a plain zip.
if [ ! -f "$PYDIR/python.exe" ]; then
    echo "Setting up Windows Python $PYVER in $WINEPREFIX ..."
    wineboot -i >/dev/null 2>&1 || true
    tmp=$(mktemp -d)
    curl -sSL -o "$tmp/python.nupkg" "https://www.nuget.org/api/v2/package/python/$PYVER"
    unzip -q "$tmp/python.nupkg" 'tools/*' -d "$tmp"
    mkdir -p "$PYDIR"
    cp -r "$tmp/tools/." "$PYDIR/"
    rm -r "$tmp"
fi

# Python needs Windows-side standard streams under Wine, so everything runs
# from a batch file through cmd with its output redirected to a log.
# (Wine's cmd mishandles "||", hence the "if errorlevel" lines.)
SRC="Z:$(pwd | sed 's|/|\\|g')"
cat > "$WINEPREFIX/drive_c/mf_build.bat" <<EOF
@echo off
cd /d "$SRC"
C:\\Python311\\python.exe -m ensurepip
C:\\Python311\\python.exe -m pip install -q --disable-pip-version-check -r requirements.txt pyinstaller pillow
if errorlevel 1 exit /b 1
C:\\Python311\\python.exe -m PyInstaller --noconfirm --onefile --windowed --name MathFighter-$VERSION --icon assets\\icon.png --distpath dist --workpath build\\win main.py
if errorlevel 1 exit /b 1
EOF
set +e
wine cmd /c 'C:\mf_build.bat > C:\mf_build.log 2>&1 < NUL' </dev/null >/dev/null 2>&1
status=$?
set -e
grep -v "^$" "$WINEPREFIX/drive_c/mf_build.log" | tail -n 5
if [ $status -ne 0 ] || [ ! -f "dist/MathFighter-$VERSION.exe" ]; then
    echo "Build failed, full log: $WINEPREFIX/drive_c/mf_build.log"
    exit 1
fi
rm -f "MathFighter-$VERSION.spec"
echo "Done: dist/MathFighter-$VERSION.exe"
