@echo off
REM Configurer la base de données HealthNet (Django 1.6.5 compatible)
cd /d "%~dp0.."
echo Configuration de la base de données HealthNet (syncdb)...
python manage.py syncdb --noinput
if not errorlevel 1 (
    echo Base de données configurée avec succès.
) else (
    echo Avertissement lors de la configuration.
)
pause
