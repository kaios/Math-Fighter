[app]
title = Math Fighter
package.name = mathfighter
package.domain = org.mathfighter
source.dir = .
source.include_exts = py,png
source.exclude_dirs = tests,tools,build,dist,bin,.buildozer,.git
version = 1.0.0
requirements = python3,pygame
icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/icon.png
orientation = landscape
fullscreen = 1

android.api = 34
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
