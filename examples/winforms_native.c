#include <windows.h>
#include <stdio.h>

// Simple native Win32 WinForms-like demo with proper message loop and painting
// Builds to a standalone exe and demonstrates stable UI render and controls.

#define IDC_EDIT_NAME 101
#define IDC_BUTTON_HELLO 102
#define IDC_BUTTON_EXIT 103

LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam)
{
    switch (message)
    {
    case WM_CREATE:
    {
        HWND hEdit = CreateWindowExA(0, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER,
            20, 20, 240, 24, hWnd, (HMENU)IDC_EDIT_NAME, (HINSTANCE)GetModuleHandle(NULL), NULL);

        HWND hBtn = CreateWindowExA(0, "BUTTON", "Say Hello", WS_CHILD | WS_VISIBLE | WS_BORDER,
            20, 60, 100, 30, hWnd, (HMENU)IDC_BUTTON_HELLO, (HINSTANCE)GetModuleHandle(NULL), NULL);

        HWND hBtn2 = CreateWindowExA(0, "BUTTON", "Exit", WS_CHILD | WS_VISIBLE | WS_BORDER,
            140, 60, 100, 30, hWnd, (HMENU)IDC_BUTTON_EXIT, (HINSTANCE)GetModuleHandle(NULL), NULL);
        return 0;
    }

    case WM_COMMAND:
    {
        int id = LOWORD(wParam);
        if (id == IDC_BUTTON_HELLO)
        {
            char buf[256] = {0};
            GetWindowTextA(GetDlgItem(hWnd, IDC_EDIT_NAME), buf, sizeof(buf));
            char msg[320];
            snprintf(msg, sizeof(msg), "Hello, %s!", buf[0] ? buf : "world");
            MessageBoxA(hWnd, msg, "Greeting", MB_OK | MB_ICONINFORMATION);
        }
        else if (id == IDC_BUTTON_EXIT)
        {
            PostMessageA(hWnd, WM_CLOSE, 0, 0);
        }
        return 0;
    }

    case WM_PAINT:
    {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hWnd, &ps);
        RECT r;
        GetClientRect(hWnd, &r);
        SetTextColor(hdc, RGB(0, 100, 180));
        SetBkMode(hdc, TRANSPARENT);
        TextOutA(hdc, 20, 100, "This is a native Win32 UI rendered via GDI.", 36);
        EndPaint(hWnd, &ps);
        return 0;
    }

    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcA(hWnd, message, wParam, lParam);
}

int APIENTRY WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow)
{
    const char CLASS_NAME[]  = "CBlerrNativeWinFormsClass";

    WNDCLASSA wc = {0};
    wc.lpfnWndProc   = WndProc;
    wc.hInstance     = hInstance;
    wc.lpszClassName = CLASS_NAME;
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);

    if (!RegisterClassA(&wc)) {
        MessageBoxA(NULL, "RegisterClass failed", "Error", MB_OK | MB_ICONERROR);
        return 0;
    }

    HWND hWnd = CreateWindowExA(0, CLASS_NAME, "CBlerr Native WinForms (GDI)",
        WS_OVERLAPPEDWINDOW | WS_VISIBLE,
        CW_USEDEFAULT, CW_USEDEFAULT, 320, 220,
        NULL, NULL, hInstance, NULL);

    if (!hWnd) {
        MessageBoxA(NULL, "CreateWindowEx failed", "Error", MB_OK | MB_ICONERROR);
        return 0;
    }

    // Proper message loop: blocks here until WM_QUIT
    MSG msg;
    while (GetMessageA(&msg, NULL, 0, 0) > 0)
    {
        TranslateMessage(&msg);
        DispatchMessageA(&msg);
    }

    return (int) msg.wParam;
}
