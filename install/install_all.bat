@echo off
REM HealthNet - Installation et lancement automatisé
REM Compatible Django 1.6.5 + Python 3.11+ (incl. 3.12+)
REM Placez ce fichier dans le dossier contenant manage.py ou utilisez-le depuis install/

setlocal

cd /d "%~dp0.."

echo ==================================
echo  HealthNet - Installation auto
echo ==================================

REM Vérifier Python
echo [1/4] Vérification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Erreur : Python n'est pas installé ou non accessible.
    pause
    exit /b 1
)

REM Installer Django 1.6.5 + compatibilité Python moderne
echo [2/4] Installation des dépendances (Django 1.6.5 + zombie-imp pour Python 3.12+)...
pip install django==1.6.5 zombie-imp
if errorlevel 1 (
    echo Avertissement : échec d'installation de django==1.6.5, tentative avec la dernière version...
    pip install django zombie-imp
)

REM Synchroniser la base de données (Django 1.6 utilise syncdb, pas migrate)
echo [3/4] Configuration de la base de données (syncdb)...
python manage.py syncdb --noinput
if errorlevel 1 (
    echo Avertissement : échec de la configuration de la base.
)

REM Lancement serveur
echo [4/4] Lancement du serveur de développement...
echo Accédez au site : http://127.0.0.1:8000
python manage.py runserver

pause
endlocal
