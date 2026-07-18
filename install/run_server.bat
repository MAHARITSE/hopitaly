@echo off
REM Lancer le serveur HealthNet
cd /d "%~dp0.."
echo Lancement du serveur HealthNet...
python manage.py runserver
pause
