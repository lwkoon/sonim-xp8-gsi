// SPDX-FileCopyrightText: 2026 Andrew Yong
// SPDX-License-Identifier: MIT
// Platform (LL-NDK) libbinder_ndk declarations that the public NDK does not ship.
#pragma once
#include <android/binder_ibinder.h>
#include <android/binder_status.h>
#include <stdbool.h>
#include <stdint.h>
__BEGIN_DECLS
bool ABinderProcess_setThreadPoolMaxThreadCount(uint32_t numThreads);
void ABinderProcess_joinThreadPool(void);
__END_DECLS
