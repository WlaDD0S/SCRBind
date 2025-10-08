# -*- mode: python ; coding: utf-8 -*-

# Analysis - конфигурация анализа и сборки зависимостей
# Определяет, какие файлы и модули будут включены в сборку

a = Analysis(
    ['SCRBind.py'],  # Главный файл программы
    pathex=[],      # Дополнительные пути для поиска модулей (как PYTHONPATH)
    binaries=[],    # Список дополнительных бинарных файлов (dll, so)
    datas=[],       # Дополнительные файлы данных (картинки, конфиги и т.д.)
    hiddenimports=[],  # Модули, которые PyInstaller не может найти автоматически
    hookspath=[],    # Пути к дополнительным hook-файлам
    hooksconfig={},  # Конфигурация для hooks
    runtime_hooks=[],  # Скрипты, запускаемые перед основной программой
    excludes=[],     # Модули, которые НЕ нужно включать в сборку
    noarchive=False,  # True - не архивировать .pyc файлы в PYZ
    optimize=0       # Уровень оптимизации Python (0-2)
)

# PYZ - создание архива Python-модулей (как zip-файл)
pyz = PYZ(a.pure)

# EXE - конфигурация создания исполняемого файла
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SCRBind',    # Имя выходного exe-файла
    debug=False,     # Включение отладочной информации
    bootloader_ignore_signals=False,  # True - загрузчик не обрабатывает сигналы
    strip=False,     # Удаление отладочных символов из бинарных файлов
    upx=True,       # Использование UPX для сжатия бинарных файлов
    upx_exclude=[], # Файлы, которые не нужно сжимать через UPX
    runtime_tmpdir=None,  # Временная директория для распаковки
    console=False,   # False - GUI приложение, True - консольное
    disable_windowed_traceback=False,  # Отключение traceback в GUI-режиме
    argv_emulation=False,  # Эмуляция аргументов командной строки (для macOS)
    target_arch=None,  # Целевая архитектура (None = текущая система)
    codesign_identity=None,  # Идентификатор для подписи кода (macOS)
    entitlements_file=None,  # Файл с правами для подписи (macOS)
    icon=['SCR.ico'],  # Путь к иконке приложения
)
