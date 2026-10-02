#!/system/bin/sh
setprop persist.wm.debug.predictive_back_anim 0

# A bind mount of magisk would be shadowed by later phh mounts via propagation; use a symlink.
if [ -e /debug_ramdisk/magisk ]; then
    umount -l /system/xbin/su
    rm -f /system/xbin/su
    ln -s /debug_ramdisk/magisk /system/xbin/su
fi
# TrebleDroid hook: resetprop ro.adb.secure 1 + restart adbd, now and at each later boot.
setprop persist.sys.phh.adb_secure 1

# On the first boot TrebleDroid enables CAF IMS after the phone process has started; restart it once.
(
    for _ in $(seq 1 60); do
        [ "$(getprop persist.sys.phh.ims.caf)" = true ] && break
        sleep 2
    done
    sleep 30
    if [ "$(getprop persist.sys.phh.ims.caf)" = true ] &&
        getprop gsm.sim.state | grep -q LOADED &&
        [ -z "$(cmd phone ims get-ims-service -s 0 -d 2>/dev/null)" ]; then
        am crash com.android.phone
    fi
) &

# On the first boot after a wipe WebViewUpdateService picks no provider and does not retry.
if dumpsys webviewupdate | grep -q "Current WebView package is null"; then
    cmd webviewupdate set-webview-implementation com.android.webview
fi

# StorageManagerService never records the system unlock of user 0 on this GSI.
[ "$(getprop persist.xp8.no_sm_mount)" = 1 ] && exit 0
while [ "$(getprop sys.user.0.ce_available)" != true ]; do
    sleep 2
done
sleep 5
media_ok() {
    content query --uri content://media/external_primary/audio/media --projection _id 2>&1 |
        grep -q "Volume external_primary not found" && return 1
    return 0
}
for try in 1 2 3; do
    if ! sm list-volumes | grep -q "^emulated;0 mounted"; then
        sm mount "emulated;0"
        sleep 5
    fi
    media_ok && break
    sm unmount "emulated;0"
    sleep 3
    sm mount "emulated;0"
    sleep 5
done
log -t xp8-gsi "done: $(sm list-volumes | grep emulated) try=$try"
