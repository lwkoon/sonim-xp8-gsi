// SPDX-FileCopyrightText: 2026 Andrew Yong
// SPDX-License-Identifier: MIT
// Minimal AIDL android.hardware.vibrator.IVibrator (V1) over timed_output.
#include <android/binder_ibinder.h>
#include <android/binder_manager.h>
#include <android/binder_process.h>
#include <android/binder_stability.h>
#include <android/log.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#define TAG "xp8-vibrator"
#define NODE "/sys/class/timed_output/vibrator/enable"
#define HASH "eeab78b6096b029f424ab5ce9c2c4ef1249a5cb0"

static binder_status_t write_node(int ms) {
    char buf[16];
    int fd = open(NODE, O_WRONLY | O_CLOEXEC);
    if (fd < 0) return STATUS_UNKNOWN_ERROR;
    int n = snprintf(buf, sizeof(buf), "%d", ms);
    ssize_t w = write(fd, buf, n);
    close(fd);
    return w == n ? STATUS_OK : STATUS_UNKNOWN_ERROR;
}

static binder_status_t reply(AParcel* out, AStatus* st) {
    binder_status_t r = AParcel_writeStatusHeader(out, st);
    AStatus_delete(st);
    return r;
}

static binder_status_t on_transact(AIBinder* b, transaction_code_t code, const AParcel* in,
                                   AParcel* out) {
    (void)b;
    binder_status_t r;
    int32_t v;
    switch (code) {
        case 1: /* getCapabilities */
            if ((r = reply(out, AStatus_newOk())) != STATUS_OK) return r;
            return AParcel_writeInt32(out, 0);
        case 2: /* off */
            return reply(out, write_node(0) == STATUS_OK
                                      ? AStatus_newOk()
                                      : AStatus_fromExceptionCode(EX_SERVICE_SPECIFIC));
        case 3: /* on(timeoutMs, callback) */
            if ((r = AParcel_readInt32(in, &v)) != STATUS_OK) return r;
            return reply(out, write_node(v > 0 ? v : 0) == STATUS_OK
                                      ? AStatus_newOk()
                                      : AStatus_fromExceptionCode(EX_SERVICE_SPECIFIC));
        case 5:  /* getSupportedEffects */
        case 10: /* getSupportedPrimitives */
        case 13: /* getSupportedAlwaysOnEffects */
            if ((r = reply(out, AStatus_newOk())) != STATUS_OK) return r;
            return AParcel_writeInt32(out, 0);
        case 16777215: /* getInterfaceVersion */
            if ((r = reply(out, AStatus_newOk())) != STATUS_OK) return r;
            return AParcel_writeInt32(out, 1);
        case 16777214: /* getInterfaceHash */
            if ((r = reply(out, AStatus_newOk())) != STATUS_OK) return r;
            return AParcel_writeString(out, HASH, strlen(HASH));
        default:
            if (code >= 1 && code <= 30)
                return reply(out, AStatus_fromExceptionCode(EX_UNSUPPORTED_OPERATION));
            return STATUS_UNKNOWN_TRANSACTION;
    }
}

static void* on_create(void* args) { return args; }
static void on_destroy(void* data) { (void)data; }

int main(void) {
    AIBinder_Class* clazz = AIBinder_Class_define("android.hardware.vibrator.IVibrator", on_create,
                                                  on_destroy, on_transact);
    AIBinder* binder = AIBinder_new(clazz, NULL);
    AIBinder_markVintfStability(binder);
    ABinderProcess_setThreadPoolMaxThreadCount(0);
    binder_exception_t e =
            AServiceManager_addService(binder, "android.hardware.vibrator.IVibrator/default");
    if (e != EX_NONE) {
        __android_log_print(ANDROID_LOG_ERROR, TAG, "addService failed: %d", e);
        return 1;
    }
    ABinderProcess_joinThreadPool();
    return 1;
}
