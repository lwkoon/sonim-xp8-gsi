// SPDX-FileCopyrightText: 2026 Andrew Yong
// SPDX-License-Identifier: MIT
// Platform (LL-NDK) libbinder_ndk declarations that the public NDK does not ship.
#pragma once
#include <android/binder_ibinder.h>
#include <android/binder_status.h>
#include <stdbool.h>
#include <stdint.h>
__BEGIN_DECLS
binder_exception_t AServiceManager_addService(AIBinder* binder, const char* instance);
__END_DECLS
