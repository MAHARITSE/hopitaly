@echo off
REM HealthNet - Installation et lancement automatisé
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

REM Installer Django et dépendances
echo [2/4] Installation des dépendances (Django 1.6.5)...
pip install django==1.6.5
if errorlevel 1 (
    echo Avertissement : échec d'installation de django==1.6.5, tentative avec la dernière version...
    pip install django
)

REM Migrations
echo [3/4] Migration de la base de données...
python manage.py migrate
if errorlevel 1 (
    echo Avertissement : échec de la migration.
)

REM Lancement serveur
echo [4/4] Lancement du serveur de développement...
echo Accédez au site : http://127.0.0.1:8000
python manage.py runserver

pause
endlocal
