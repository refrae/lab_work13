
import ctypes
import sys

# Размечаем типы аргументов для корректной работы с Windows API на уровне байт
# DWORD — это 32-битное целое число, LPCWSTR — указатель на UTF-16 строку, HANDLE — указатель.
DWORD = ctypes.c_ulong
LPCWSTR = ctypes.c_wchar_p
HANDLE = ctypes.c_void_p

print("--- ШАГ 1: Загрузка управляющей библиотеки kernel32.dll ---")
# Загружаем базовую библиотеку ядра. Она уже есть в памяти любого процесса Windows.
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

print("\n--- ШАГ 2: Ручное проецирование внешней библиотеки user32.dll в ОЗУ ---")
# Явно вызываем LoadLibraryW из kernel32.dll, передавая путь к системной библиотеке
dll_name = "user32.dll"
h_module = kernel32.LoadLibraryW(dll_name)

if not h_module:
    print(f"[ОШИБКА] Не удалось загрузить библиотеку. Код ошибки Windows: {ctypes.get_last_error()}")
    sys.exit(1)

print(f"[УСПЕХ] Библиотека {dll_name} успешно спроецирована в память Ring 3!")
print(f"[НИЗКИЙ УРОВЕНЬ] Дескриптор HMODULE (базовый адрес в ОЗУ): {hex(h_module)}")

print("\n--- ШАГ 3: Парсинг Таблицы Экспорта и поиск адреса функции ---")
# Настраиваем типы данных для GetProcAddress: принимает HMODULE и имя функции (строку ASCII)
kernel32.GetProcAddress.argtypes = [HANDLE, ctypes.c_char_p]
kernel32.GetProcAddress.restype = HANDLE

func_name = b"MessageBoxW"  # Имя функции обязательно в формате байтовой строки ASCII

func_address = kernel32.GetProcAddress(h_module, func_name)

if not func_address:
    print(f"[ОШИБКА] Функция {func_name.decode()} не найдена в Таблице Экспорта DLL!")
    kernel32.FreeLibrary(h_module)
    sys.exit()

print(f"[УСПЕХ] Функция найдена!")
print(f"[НИЗКИЙ УРОВЕНЬ] Точный виртуальный адрес кода {func_name.decode()} в ОЗУ: {hex(func_address)}")

print("\n--- ШАГ 4: Динамический вызов функции по найденному адресу ---")
# Создаем исполняемый прототип функции на основе её низкоуровневого адреса
# MessageBoxW(HWND hWnd, LPCWSTR lpText, LPCWSTR lpCaption, UINT uType)
WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_int, HANDLE, LPCWSTR, LPCWSTR, ctypes.c_uint)
message_box_func = WNDPROC(func_address)

print("[ПРОЦЕССОР] Выполняем переход по адресу функции (CALL)...")
# Вызываем функцию: передаем NULL (0) для родительского окна, текст, заголовок и стиль окна (0)
message_box_func(0, "Сообщение вызвано через прямой адрес из Таблицы Экспорта", "Системное программирование", 0)

print("\n--- ШАГ 5: Освобождение системных ресурсов ---")
kernel32.FreeLibrary(h_module)
print("[УСПЕХ] Модуль выгружен из памяти процесса.")