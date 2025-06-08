@echo off
setlocal

echo Creating project structure...
echo.

REM === Create Root Folder ===
IF NOT EXIST "QingtingzheFullProject" (
    mkdir "QingtingzheFullProject"
    echo Created: QingtingzheFullProject
) ELSE (
    echo Exists: QingtingzheFullProject
)
pushd "QingtingzheFullProject"

REM === Create PsychologyAnalysis Structure ===
IF NOT EXIST "PsychologyAnalysis" (
    mkdir "PsychologyAnalysis"
    echo   Created: PsychologyAnalysis
) ELSE (
    echo   Exists: PsychologyAnalysis
)
pushd "PsychologyAnalysis"

IF NOT EXIST "config" mkdir "config" && echo     Created: config || echo     Exists: config
IF NOT EXIST "input" mkdir "input" && echo     Created: input || echo     Exists: input
pushd "input"
IF NOT EXIST "images" mkdir "images" && echo       Created: images || echo       Exists: images
IF NOT EXIST "questionnaires" mkdir "questionnaires" && echo       Created: questionnaires || echo       Exists: questionnaires
popd

IF NOT EXIST "logs" mkdir "logs" && echo     Created: logs || echo     Exists: logs
IF NOT EXIST "output" mkdir "output" && echo     Created: output || echo     Exists: output
pushd "output"
IF NOT EXIST "descriptions" mkdir "descriptions" && echo       Created: descriptions || echo       Exists: descriptions
IF NOT EXIST "reports" mkdir "reports" && echo       Created: reports || echo       Exists: reports
popd

IF NOT EXIST "src" mkdir "src" && echo     Created: src || echo     Exists: src
pushd "src"
IF NOT EXIST "__pycache__" mkdir "__pycache__" && echo       Created: __pycache__ || echo       Exists: __pycache__
popd

IF NOT EXIST "templates" mkdir "templates" && echo     Created: templates || echo     Exists: templates
pushd "templates"
IF NOT EXIST "static" mkdir "static" && echo       Created: static || echo       Exists: static
popd

IF NOT EXIST "uploads" mkdir "uploads" && echo     Created: uploads || echo     Exists: uploads
IF NOT EXIST "__pycache__" mkdir "__pycache__" && echo     Created: __pycache__ || echo     Exists: __pycache__
IF NOT EXIST "文档部分" (
    mkdir "文档部分"
    echo     Created: 文档部分
) ELSE (
    echo     Exists: 文档部分
)
REM --- Placeholder for files inside PsychologyAnalysis (optional, creates empty files) ---
REM IF NOT EXIST "app.py" type nul > "app.py" && echo     Created file: app.py
REM IF NOT EXIST "config.yaml" type nul > "config.yaml" && echo     Created file: config.yaml
REM IF NOT EXIST "requirements.txt" type nul > "requirements.txt" && echo     Created file: requirements.txt
REM IF NOT EXIST "data_handler.py" type nul > "data_handler.py" && echo     Created file: data_handler.py
REM IF NOT EXIST "ai_utils.py" type nul > "ai_utils.py" && echo     Created file: ai_utils.py
REM IF NOT EXIST "templates\app_prototype_form.html" type nul > "templates\app_prototype_form.html" && echo     Created file: templates\app_prototype_form.html
REM IF NOT EXIST "templates\report_prototype.html" type nul > "templates\report_prototype.html" && echo     Created file: templates\report_prototype.html
REM IF NOT EXIST "templates\error.html" type nul > "templates\error.html" && echo     Created file: templates\error.html

popd REM Exit PsychologyAnalysis

REM === Create AndroidAppPrototype Structure ===
IF NOT EXIST "AndroidAppPrototype" (
    mkdir "AndroidAppPrototype"
    echo   Created: AndroidAppPrototype
) ELSE (
    echo   Exists: AndroidAppPrototype
)
pushd "AndroidAppPrototype"

IF NOT EXIST "app" mkdir "app" && echo     Created: app || echo     Exists: app
pushd "app"
IF NOT EXIST "libs" mkdir "libs" && echo       Created: libs || echo       Exists: libs
IF NOT EXIST "src" mkdir "src" && echo       Created: src || echo       Exists: src
pushd "src"
IF NOT EXIST "androidTest" mkdir "androidTest" && echo         Created: androidTest || echo         Exists: androidTest
IF NOT EXIST "main" mkdir "main" && echo         Created: main || echo         Exists: main
pushd "main"
IF NOT EXIST "java" mkdir "java" && echo           Created: java || echo           Exists: java
pushd "java"
IF NOT EXIST "com" mkdir "com" && echo             Created: com || echo             Exists: com
pushd "com"
IF NOT EXIST "example" mkdir "example" && echo               Created: example || echo               Exists: example
pushd "example"
IF NOT EXIST "qingtingzheproto" mkdir "qingtingzheproto" && echo                 Created: qingtingzheproto || echo                 Exists: qingtingzheproto
popd
popd
popd
popd REM Exit java path
IF NOT EXIST "res" mkdir "res" && echo           Created: res || echo           Exists: res
pushd "res"
IF NOT EXIST "drawable" mkdir "drawable" && echo             Created: drawable || echo             Exists: drawable
IF NOT EXIST "layout" mkdir "layout" && echo             Created: layout || echo             Exists: layout
IF NOT EXIST "mipmap" mkdir "mipmap" && echo             Created: mipmap || echo             Exists: mipmap
IF NOT EXIST "values" mkdir "values" && echo             Created: values || echo             Exists: values
IF NOT EXIST "xml" mkdir "xml" && echo             Created: xml || echo             Exists: xml
popd
popd REM Exit main
IF NOT EXIST "test" mkdir "test" && echo         Created: test || echo         Exists: test
popd REM Exit src
popd REM Exit app

IF NOT EXIST "gradle" mkdir "gradle" && echo     Created: gradle || echo     Exists: gradle
pushd "gradle"
IF NOT EXIST "wrapper" mkdir "wrapper" && echo       Created: wrapper || echo       Exists: wrapper
popd

popd REM Exit AndroidAppPrototype

popd REM Exit QingtingzheFullProject

echo.
echo Structure creation process complete.
echo Check the directory you ran this script from for 'QingtingzheFullProject'.

endlocal