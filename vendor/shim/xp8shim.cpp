// SPDX-FileCopyrightText: 2026 Andrew Yong
// SPDX-License-Identifier: MIT

// Symbols the stock A10 vendor libs need but the A16 VNDK v29 libbinder/libselinux lack.
extern "C" {
int open(const char*, int, ...);
long write(int, const void*, unsigned long);
int close(int);
unsigned long strlen(const char*);
}
#define O_RDWR 02
#define O_CLOEXEC 02000000
extern "C" int fgetfilecon(int fd, char** con);

extern "C" __attribute__((visibility("default"))) bool
_ZN7android15PermissionCache15checkPermissionERKNS_8String16Eij(const void*, int, unsigned int uid) {
    return uid == 0 || uid == 1000 || uid == 2000;
}

extern "C" __attribute__((visibility("default"))) int fgetfilecon_raw(int fd, char** con) {
    return fgetfilecon(fd, con);
}

extern "C" __attribute__((visibility("default"))) int setsockcreatecon_raw(const char* con) {
    int fd = open("/proc/thread-self/attr/sockcreate", O_RDWR | O_CLOEXEC);
    if (fd < 0) return -1;
    long r = con ? write(fd, con, strlen(con) + 1) : write(fd, nullptr, 0);
    close(fd);
    return r < 0 ? -1 : 0;
}
