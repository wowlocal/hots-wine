// Passive, local Metal presentation timestamps. Intended for offline replay benchmarks.
#import <Foundation/Foundation.h>
#import <QuartzCore/CAMetalLayer.h>
#import <Metal/Metal.h>
#import <objc/runtime.h>
#include <mach/mach_time.h>
#include <mach-o/dyld.h>
#include <stdatomic.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>
#include <string.h>

typedef struct {
    char magic[8];
    uint32_t version, record_size;
    uint64_t capacity;
    _Atomic uint64_t count;
    uint32_t timebase_numer, timebase_denom;
    uint64_t start_mach;
    double start_wall;
    uint32_t pid, reserved;
} ProbeHeader;
typedef struct {
    double presented_time;
    uint64_t callback_mach, drawable_id, acquired_mach;
    uint32_t width, height;
} ProbeRecord;

static ProbeHeader *header;
static ProbeRecord *records;
static IMP original_next_drawable;

static id probe_next_drawable(id layer, SEL selector) {
    id<CAMetalDrawable> drawable = ((id (*)(id, SEL))original_next_drawable)(layer, selector);
    if (drawable && header) {
        uint64_t acquired = mach_absolute_time();
        uint32_t width = (uint32_t)drawable.texture.width;
        uint32_t height = (uint32_t)drawable.texture.height;
        [drawable addPresentedHandler:^(id<MTLDrawable> shown) {
            uint64_t i = atomic_fetch_add_explicit(&header->count, 1, memory_order_relaxed);
            if (i < header->capacity) {
                records[i] = (ProbeRecord){shown.presentedTime, mach_absolute_time(),
                                          shown.drawableID, acquired, width, height};
            }
        }];
    }
    return drawable;
}

__attribute__((constructor)) static void install_probe(void) {
    const char *path = getenv("HOTS_FRAME_LOG");
    if (!path || !*path) return;
    char executable[4096]; uint32_t length = sizeof(executable);
    if (_NSGetExecutablePath(executable, &length) != 0) return;
    // Wine children inherit the environment; only the requested game owns this file.
    const char *direct = getenv("HOTS_FRAME_PROBE_DIRECT");
    if (!direct && !strstr(executable, "HeroesOfTheStorm_x64.exe")) return;
    uint64_t capacity = 1000000;
    size_t size = 4096 + capacity * sizeof(ProbeRecord);
    int fd = open(path, O_RDWR | O_CREAT | O_TRUNC, 0600);
    if (fd < 0 || ftruncate(fd, size) != 0) { if (fd >= 0) close(fd); return; }
    void *data = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);
    if (data == MAP_FAILED) return;
    header = data; records = (ProbeRecord *)((char *)data + 4096);
    mach_timebase_info_data_t tb; mach_timebase_info(&tb);
    struct timespec now; clock_gettime(CLOCK_REALTIME, &now);
    memcpy(header->magic, "HOTSMTL1", 8);
    header->version = 1; header->record_size = sizeof(ProbeRecord);
    header->capacity = capacity; atomic_store(&header->count, 0);
    header->timebase_numer = tb.numer; header->timebase_denom = tb.denom;
    header->start_mach = mach_absolute_time();
    header->start_wall = now.tv_sec + now.tv_nsec / 1e9; header->pid = getpid();
    Method method = class_getInstanceMethod([CAMetalLayer class], @selector(nextDrawable));
    original_next_drawable = method_setImplementation(method, (IMP)probe_next_drawable);
    fprintf(stderr, "HotS frame probe active: PID %d, record size %zu\n", getpid(), sizeof(ProbeRecord));
}
