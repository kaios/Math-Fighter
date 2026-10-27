[app]
title = Math Fighter
package.name = mathfighter
package.domain = org.mathfighter
source.dir = .
source.include_exts = py,png
source.exclude_dirs = tests,tools,build,dist,bin,.buildozer,.git,p4a-recipes
version.regex = __version__ = ['"](.*)['"]
version.filename = %(source.dir)s/mathfighter/config.py
requirements = python3,pygame
icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/icon.png
orientation = landscape
fullscreen = 1

# Android 10 (API 29) and newer
android.api = 35
android.minapi = 29
android.ndk_api = 29
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
p4a.bootstrap = sdl2
# pygame 2.6.1 instead of the stock 2.1.0 (see p4a-recipes/pygame)
p4a.local_recipes = ./p4a-recipes

[buildozer]
log_level = 2
warn_on_root = 1
