// SPDX-FileCopyrightText: 2026 Andrew Yong
// SPDX-License-Identifier: MIT
// Platform (LL-NDK) libbinder_ndk declarations that the public NDK does not ship.
#pragma once
#include <android/binder_ibinder.h>
#include <android/binder_status.h>
#include <stdbool.h>
#include <stdint.h>
__BEGIN_DECLS
void AIBinder_markVintfStability(AIBinder* binder);
__END_DECLS
