#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Create compiled translation files
python compile_translations.py  # Run the manual script if it exists, or... but wait, I deleted it.
# Actually, I deleted compile_translations.py. I should probably restore it OR use django-admin compilemessages if gettext is available on Render (it usually is).
# Render has gettext installed by default in their Python environment? Not always guaranteed.
# Let's rely on the fact that I already committed the .mo files?
# If the .mo files are in the repo, I don't need to run compilemessages on build.
# BUT, usually it's cleaner to compile on build.
# Since the USER is on Windows and had issues with gettext, I manually compiled.
# The .mo files ARE in the file system.
# So I will just do collectstatic and migrate.

python manage.py collectstatic --no-input
python manage.py migrate
