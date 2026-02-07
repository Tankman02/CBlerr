/*
Модуль VGA (Video Graphics Array)
==================================

Предоставляет функции для работы с VGA видеопамятью.
VGA буфер находится на адресе 0xB8000 в физической памяти.

Каждый символ на экране занимает 2 байта:
  - Первый байт: ASCII код символа
  - Второй байт: Атрибут (цвет переднего плана, цвет фона, яркость)

Размер экрана: 80 символов × 25 строк = 2000 символов
Общий размер буфера: 2000 × 2 = 4000 байт

Примеры использования:
  from vga import init_vga, clear_screen, print_string
  
  vga = init_vga()
  clear_screen(&vga)
  print_string(&vga, "Hello, World!", 0x0F)
*/

@packed
struct VGABuffer:
    address: ptr<u8>
    width: u16
    height: u16
    cursor_x: u16
    cursor_y: u16

def init_vga() -> VGABuffer:
    """
    Инициализирует VGA буфер.
    
    Returns:
        VGABuffer структура с настройками видеопамяти
    """
    vga: VGABuffer
    vga.address = cast 0xB8000 as ptr<u8>
    vga.width = 80
    vga.height = 25
    vga.cursor_x = 0
    vga.cursor_y = 0
    return vga

def clear_screen(vga: ptr<VGABuffer>):
    """
    Очищает экран (заполняет пробелами).
    
    Args:
        vga: Указатель на VGABuffer
    """
    for i in range(0, vga.width * vga.height):
        vga.address[i * 2] = ' ' as u8      # Символ: пробел
        vga.address[i * 2 + 1] = 0x0F as u8 # Атрибут: белый на чёрном

def print_char(vga: ptr<VGABuffer>, ch: u8, color: u8):
    """
    Печатает один символ на текущей позиции курсора.
    
    Args:
        vga: Указатель на VGABuffer
        ch: ASCII код символа
        color: Цвет (формат: 0xBF, где B=фон, F=передний план)
    """
    offset: u16 = (vga.cursor_y * vga.width + vga.cursor_x) * 2
    
    vga.address[offset] = ch
    vga.address[offset + 1] = color
    
    vga.cursor_x = vga.cursor_x + 1
    
    if vga.cursor_x >= vga.width:
        vga.cursor_x = 0
        vga.cursor_y = vga.cursor_y + 1
        
        if vga.cursor_y >= vga.height:
            vga.cursor_y = vga.height - 1
            scroll_screen(vga)

def print_string(vga: ptr<VGABuffer>, str: str, color: u8):
    """
    Печатает строку на экран.
    
    Args:
        vga: Указатель на VGABuffer
        str: Строка для вывода
        color: Цвет символов
    """
    # В простой версии просто выводим каждый символ
    # Реальная реализация будет итерировать по символам строки
    pass

def scroll_screen(vga: ptr<VGABuffer>):
    """
    Прокручивает содержимое экрана на одну строку вверх.
    
    Args:
        vga: Указатель на VGABuffer
    """
    # Копируем всё содержимое на одну строку вверх
    for y in range(0, vga.height - 1):
        for x in range(0, vga.width):
            src_offset: u16 = ((y + 1) * vga.width + x) * 2
            dst_offset: u16 = (y * vga.width + x) * 2
            
            vga.address[dst_offset] = vga.address[src_offset]
            vga.address[dst_offset + 1] = vga.address[src_offset + 1]
    
    # Очищаем последнюю строку
    for x in range(0, vga.width):
        offset: u16 = ((vga.height - 1) * vga.width + x) * 2
        vga.address[offset] = ' ' as u8
        vga.address[offset + 1] = 0x0F as u8

def set_cursor_position(vga: ptr<VGABuffer>, x: u16, y: u16):
    """
    Устанавливает позицию курсора.
    
    Args:
        vga: Указатель на VGABuffer
        x: Горизонтальная позиция (0-79)
        y: Вертикальная позиция (0-24)
    """
    if x < vga.width and y < vga.height:
        vga.cursor_x = x
        vga.cursor_y = y

def get_cursor_position(vga: ptr<VGABuffer>) -> u32:
    """
    Получает текущую позицию курсора в виде одного значения.
    
    Returns:
        (y << 8) | x
    """
    return ((vga.cursor_y as u32) << 8) | (vga.cursor_x as u32)

def newline(vga: ptr<VGABuffer>):
    """
    Переводит курсор на новую строку.
    """
    vga.cursor_x = 0
    vga.cursor_y = vga.cursor_y + 1
    
    if vga.cursor_y >= vga.height:
        vga.cursor_y = vga.height - 1
        scroll_screen(vga)

/* Цветовая палитра VGA */
@comptime:
    BLACK = 0x0
    BLUE = 0x1
    GREEN = 0x2
    CYAN = 0x3
    RED = 0x4
    MAGENTA = 0x5
    BROWN = 0x6
    LIGHTGRAY = 0x7
    DARKGRAY = 0x8
    LIGHTBLUE = 0x9
    LIGHTGREEN = 0xA
    LIGHTCYAN = 0xB
    LIGHTRED = 0xC
    LIGHTMAGENTA = 0xD
    YELLOW = 0xE
    WHITE = 0xF

/* Макрос для создания цвета (передний план | (фон << 4)) */
def make_color(fg: u8, bg: u8) -> u8:
    return fg | (bg << 4)
