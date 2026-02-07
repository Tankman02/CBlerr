extern def CreateWindowExA(
    dwExStyle: u32,
    lpClassName: str,
    lpWindowName: str,
    dwStyle: u32,
    x: i32,
    y: i32,
    nWidth: i32,
    nHeight: i32,
    hWndParent: i32,
    hMenu: i32,
    hInstance: i32,
    lpParam: i32
) -> i32

extern def ShowWindow(hWnd: i32, nCmdShow: i32) -> i32

extern def UpdateWindow(hWnd: i32) -> i32

extern def GetMessageA(
    lpMsg: i32,
    hWnd: i32,
    wMsgFilterMin: u32,
    wMsgFilterMax: u32
) -> i32

extern def TranslateMessage(lpMsg: i32) -> i32

extern def DispatchMessageA(lpMsg: i32) -> i32

extern def PostQuitMessage(nExitCode: i32) -> void

extern def DefWindowProcA(
    hWnd: i32,
    Msg: u32,
    wParam: i32,
    lParam: i32
) -> i32

extern def SendMessageA(
    hWnd: i32,
    Msg: u32,
    wParam: i32,
    lParam: i32
) -> i32

extern def SetWindowTextA(hWnd: i32, lpString: str) -> i32

extern def GetWindowTextA(hWnd: i32, lpString: str, nMaxCount: i32) -> i32

extern def DestroyWindow(hWnd: i32) -> i32

extern def MessageBoxA(
    hWnd: i32,
    lpText: str,
    lpCaption: str,
    uType: u32
) -> i32

extern def InvalidateRect(hWnd: i32, lpRect: i32, bErase: i32) -> i32

extern def BeginPaint(hWnd: i32, lpPaint: i32) -> i32

extern def EndPaint(hWnd: i32, lpPaint: i32) -> i32

extern def GetDC(hWnd: i32) -> i32

extern def ReleaseDC(hWnd: i32, hDC: i32) -> i32

extern def TextOutA(
    hDC: i32,
    x: i32,
    y: i32,
    lpString: str,
    c: i32
) -> i32

extern def GetModuleHandleA(lpModuleName: str) -> i32

extern def RegisterClassA(lpWndClass: i32) -> i32

extern def CreateSolidBrush(crColor: u32) -> i32

extern def SetBkColor(hDC: i32, color: u32) -> u32

extern def SetTextColor(hDC: i32, color: u32) -> u32

extern def Rectangle(hDC: i32, left: i32, top: i32, right: i32, bottom: i32) -> i32

extern def FillRect(hDC: i32, lprc: i32, hbr: i32) -> i32

extern def printf(fmt: str, ...) -> i32

def WS_OVERLAPPEDWINDOW() -> u32:
    return 13565952

def WS_VISIBLE() -> u32:
    return 268435456

def WS_CHILD() -> u32:
    return 1073741824

def WS_BORDER() -> u32:
    return 8388608

def SW_SHOW() -> i32:
    return 5

def WM_DESTROY() -> u32:
    return 2

def WM_PAINT() -> u32:
    return 15

def WM_COMMAND() -> u32:
    return 273

def WM_CLOSE() -> u32:
    return 16

def MB_OK() -> u32:
    return 0

def MB_OKCANCEL() -> u32:
    return 1

def MB_YESNO() -> u32:
    return 4

def MB_ICONINFORMATION() -> u32:
    return 64

def MB_ICONWARNING() -> u32:
    return 48

def MB_ICONSTOP() -> u32:
    return 16

def COLOR_WINDOW() -> u32:
    return 5

def IDOK() -> i32:
    return 1

def IDCANCEL() -> i32:
    return 2

def IDYES() -> i32:
    return 6

def IDNO() -> i32:
    return 7

def RGB(r: u8, g: u8, b: u8) -> u32:
    red: u32 = r
    green: u32 = g
    blue: u32 = b
    return (blue << 16) | (green << 8) | red

global_hWnd: i32 = 0
global_running: i32 = 1
global_button_pressed: i32 = 0
global_text_input: str = ""

def ui_show_message(title: str, message: str) -> i32:
    result: i32 = MessageBoxA(0, message, title, MB_OK())
    return result

def ui_show_question(title: str, message: str) -> i32:
    result: i32 = MessageBoxA(0, message, title, MB_YESNO() | MB_ICONINFORMATION())
    if result == IDYES():
        return 1
    else:
        return 0

def ui_show_warning(title: str, message: str) -> i32:
    result: i32 = MessageBoxA(0, message, title, MB_OK() | MB_ICONWARNING())
    return result

def ui_show_error(title: str, message: str) -> i32:
    result: i32 = MessageBoxA(0, message, title, MB_OK() | MB_ICONSTOP())
    return result

def ui_input_box(prompt: str, default_value: str) -> str:
    printf("Input required: %s\n", prompt)
    printf("Default: %s\n", default_value)
    return default_value

def ui_simple_window(title: str, width: i32, height: i32) -> i32:
    hInstance: i32 = GetModuleHandleA("")
    
    hWnd: i32 = CreateWindowExA(
        0,
        "STATIC",
        title,
        WS_OVERLAPPEDWINDOW() | WS_VISIBLE(),
        100,
        100,
        width,
        height,
        0,
        0,
        hInstance,
        0
    )
    
    if hWnd == 0:
        printf("Failed to create window\n")
        return 0
    
    ShowWindow(hWnd, SW_SHOW())
    UpdateWindow(hWnd)
    
    return hWnd

def ui_run_message_loop() -> void:
    while global_running != 0:
        # Простая обработка - в реальном приложении используется GetMessage
        global_running = 0

def ui_close_window(hWnd: i32) -> i32:
    result: i32 = DestroyWindow(hWnd)
    PostQuitMessage(0)
    return result

def ui_set_window_title(hWnd: i32, title: str) -> i32:
    result: i32 = SetWindowTextA(hWnd, title)
    return result

def ui_color_red() -> u32:
    return RGB(255, 0, 0)

def ui_color_green() -> u32:
    return RGB(0, 255, 0)

def ui_color_blue() -> u32:
    return RGB(0, 0, 255)

def ui_color_white() -> u32:
    return RGB(255, 255, 255)

def ui_color_black() -> u32:
    return RGB(0, 0, 0)

def ui_color_gray() -> u32:
    return RGB(128, 128, 128)

def ui_color_custom(r: u8, g: u8, b: u8) -> u32:
    return RGB(r, g, b)

def ui_log(message: str) -> void:
    printf("[UI LOG] %s\n", message)

def ui_debug(message: str) -> void:
    printf("[UI DEBUG] %s\n", message)

def ui_error(message: str) -> void:
    printf("[UI ERROR] %s\n", message)

def ui_info(message: str) -> void:
    printf("[UI INFO] %s\n", message)

def main() -> i32:
    printf("╔════════════════════════════════════════════╗\n")
    printf("║   CBlerr UI Library v1.0                   ║\n")
    printf("║   Встроенная библиотека для GUI            ║\n")
    printf("║   Windows без внешних зависимостей        ║\n")
    printf("╚════════════════════════════════════════════╝\n\n")
    
    printf("Доступные функции UI:\n\n")
    
    printf("1. Окна и сообщения:\n")
    printf("   - ui_show_message(title, message)\n")
    printf("   - ui_show_question(title, message)\n")
    printf("   - ui_show_warning(title, message)\n")
    printf("   - ui_show_error(title, message)\n\n")
    
    printf("2. Создание окон:\n")
    printf("   - ui_simple_window(title, width, height)\n")
    printf("   - ui_set_window_title(hWnd, title)\n")
    printf("   - ui_close_window(hWnd)\n\n")
    
    printf("3. Цвета (ARGB):\n")
    printf("   - ui_color_red(), green(), blue()\n")
    printf("   - ui_color_white(), black(), gray()\n")
    printf("   - ui_color_custom(r, g, b)\n\n")
    
    printf("4. Вспомогательные функции:\n")
    printf("   - ui_log(message)\n")
    printf("   - ui_debug(message)\n")
    printf("   - ui_error(message)\n")
    printf("   - ui_info(message)\n\n")
    
    printf("Примеры использования смотрите в:\n")
    printf("  - examples/ui_demo_simple.cbl\n")
    printf("  - examples/ui_demo_dialog.cbl\n")
    printf("  - examples/ui_demo_colors.cbl\n\n")
    
    printf("Компиляция:\n")
    printf("  python build\\build_standalone.py examples\\ui_demo.cbl\n\n")
    
    return 0
