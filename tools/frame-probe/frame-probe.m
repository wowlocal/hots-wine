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
#include <pthread.h>
#include <limits.h>

typedef struct {
    char magic[8];
    uint32_t version, record_size;
    uint64_t capacity;
    _Atomic uint64_t count;
    uint32_t timebase_numer, timebase_denom;
    uint64_t start_mach;
    double start_wall;
    uint32_t pid, reserved;
    _Atomic uint64_t acquired_count;
} ProbeHeader;
typedef struct {
    double presented_time;
    uint64_t callback_mach, drawable_id, acquired_mach;
    uint32_t width, height;
    uint64_t layer_id;
    _Atomic uint64_t committed;
} ProbeRecord;

static ProbeHeader *header;
static ProbeRecord *records;
static IMP original_next_drawable;
static pthread_once_t log_once = PTHREAD_ONCE_INIT;
static void initialize_log(void);

static id probe_next_drawable(id layer, SEL selector) {
    id<CAMetalDrawable> drawable = ((id (*)(id, SEL))original_next_drawable)(layer, selector);
    if (drawable) pthread_once(&log_once, initialize_log);
    if (drawable && header) {
        uint64_t acquired = mach_absolute_time();
        uint32_t width = (uint32_t)drawable.texture.width;
        uint32_t height = (uint32_t)drawable.texture.height;
        uint64_t layer_id = (uint64_t)(uintptr_t)(__bridge void *)layer;
        atomic_fetch_add_explicit(&header->acquired_count, 1, memory_order_relaxed);
        [drawable addPresentedHandler:^(id<MTLDrawable> shown) {
            uint64_t i = atomic_fetch_add_explicit(&header->count, 1, memory_order_relaxed);
            if (i < header->capacity) {
                ProbeRecord *record = &records[i];
                record->presented_time = shown.presentedTime;
                record->callback_mach = mach_absolute_time();
                record->drawable_id = shown.drawableID;
                record->acquired_mach = acquired;
                record->width = width; record->height = height;
                record->layer_id = layer_id;
                atomic_store_explicit(&record->committed, i + 1, memory_order_release);
            }
        }];
    }
    return drawable;
}

static void initialize_log(void) {
    const char *directory = getenv("HOTS_FRAME_LOG_DIR");
    char local_path[PATH_MAX];
    if (!directory || directory[0] != '/') return;
    int length = snprintf(local_path, sizeof(local_path), "%s/frames-%d.bin", directory, getpid());
    if (length <= 0 || (size_t)length >= sizeof(local_path)) return;
    uint64_t capacity = 1000000;
    size_t size = 4096 + capacity * sizeof(ProbeRecord);
    int fd = open(local_path, O_RDWR | O_CREAT | O_EXCL | O_NOFOLLOW, 0600);
    if (fd < 0 || ftruncate(fd, size) != 0) { if (fd >= 0) close(fd); return; }
    void *data = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);
    if (data == MAP_FAILED) return;
    header = data; records = (ProbeRecord *)((char *)data + 4096);
    mach_timebase_info_data_t tb; mach_timebase_info(&tb);
    struct timespec now; clock_gettime(CLOCK_REALTIME, &now);
    memcpy(header->magic, "HOTSMTL1", 8);
    header->version = 3; header->record_size = sizeof(ProbeRecord);
    header->capacity = capacity; atomic_store(&header->count, 0);
    atomic_store(&header->acquired_count, 0);
    header->timebase_numer = tb.numer; header->timebase_denom = tb.denom;
    header->start_mach = mach_absolute_time();
    header->start_wall = now.tv_sec + now.tv_nsec / 1e9; header->pid = getpid();
    fprintf(stderr, "HotS frame probe active: PID %d, record size %zu\n", getpid(), sizeof(ProbeRecord));
}

__attribute__((constructor)) static void install_probe(void) {
    const char *directory = getenv("HOTS_FRAME_LOG_DIR");
    if (!directory || directory[0] != '/') return;
    Method method = class_getInstanceMethod([CAMetalLayer class], @selector(nextDrawable));
    if (method) {
        original_next_drawable = method_getImplementation(method);
        method_setImplementation(method, (IMP)probe_next_drawable);
    }
}
