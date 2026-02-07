@packed
struct MemoryBlock:
    size: u32
    allocated: bool
    next: ptr<MemoryBlock>

@packed
struct MemoryPool:
    start: ptr<u8>
    current: u32
    limit: u32
    first_block: ptr<MemoryBlock>

# Глобальный heap
heap: MemoryPool

def init_heap(start: u32, size: u32):
    heap.start = cast start as ptr<u8>
    heap.current = 0
    heap.limit = size
    heap.first_block = cast 0 as ptr<MemoryBlock>

def allocate(size: u32) -> ptr<u8>:

    if heap.current + size > heap.limit:
        return cast 0 as ptr<u8>  # Недостаточно памяти
    
    ptr: ptr<u8> = heap.start + heap.current
    heap.current = heap.current + size
    
    return ptr

def allocate_aligned(size: u32, alignment: u32) -> ptr<u8>:

    current_addr: u32 = cast heap.start as u32 + heap.current
    
    aligned_addr: u32 = (current_addr + alignment - 1) / alignment * alignment
    
    offset: u32 = aligned_addr - (cast heap.start as u32)
    
    if offset + size > heap.limit:
        return cast 0 as ptr<u8>  # Недостаточно памяти
    
    heap.current = offset + size
    
    return cast aligned_addr as ptr<u8>

def deallocate(ptr: ptr<u8>):
    pass

def memory_set(ptr: ptr<u8>, value: u8, size: u32):
    for i in range(0, size):
        ptr[i] = value

def memory_copy(dest: ptr<u8>, src: ptr<u8>, size: u32):
    for i in range(0, size):
        dest[i] = src[i]

def memory_zero(ptr: ptr<u8>, size: u32):
    memory_set(ptr, 0 as u8, size)

def get_heap_used() -> u32:

    return heap.current

def get_heap_available() -> u32:

    if heap.current > heap.limit:
        return 0
    return heap.limit - heap.current

def allocate_page() -> ptr<u8>:
    return allocate_aligned(4096, 4096)

def allocate_pages(count: u32) -> ptr<u8>:
    size: u32 = count * 4096
    return allocate_aligned(size, 4096)

def allocate_page_table() -> ptr<u32>:
    ptr: ptr<u8> = allocate_aligned(4096, 4096)
    memory_zero(ptr, 4096)
    return cast ptr as ptr<u32>

def print_heap_stats():
    """
    Примеры вывода:
      Heap start:  0x100000
      Heap limit:  0x200000
      Heap used:   0x010000 (65536 байтов)
      Heap free:   0x0F0000 (983040 байтов)
    """
    # (требует импорта vga модуля)
    pass
