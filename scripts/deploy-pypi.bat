
SET APP_SCRIPT_PATH=%~dp0
IF %APP_SCRIPT_PATH:~-1%==\ SET APP_SCRIPT_PATH=%APP_SCRIPT_PATH:~0,-1%
SET PACKAGE_FOLDER=%APP_SCRIPT_PATH%/../geodataflow

REM ===========================================================================
REM Upload installers

@echo OFF
FOR /d /r "%PACKAGE_FOLDER%" %%d IN (__pycache__) DO @IF EXIST "%%d" rmdir /s /q "%%d"
@echo OFF

@echo INFO: Uploading installers

REM TEST:
REM twine upload -r testpypi "%PACKAGE_FOLDER%/core/dist/*"
REM twine upload -r testpypi "%PACKAGE_FOLDER%/spatial/dist/*"
REM twine upload -r testpypi "%PACKAGE_FOLDER%/dataframes/dist/*"
REM twine upload -r testpypi "%PACKAGE_FOLDER%/api/dist/*"
REM twine upload -r testpypi "%PACKAGE_FOLDER%/all/dist/*"

twine upload -r pypi "%PACKAGE_FOLDER%/core/dist/*"
twine upload -r pypi "%PACKAGE_FOLDER%/spatial/dist/*"
twine upload -r pypi "%PACKAGE_FOLDER%/dataframes/dist/*"
twine upload -r pypi "%PACKAGE_FOLDER%/api/dist/*"
twine upload -r pypi "%PACKAGE_FOLDER%/all/dist/*"

REM ===========================================================================
