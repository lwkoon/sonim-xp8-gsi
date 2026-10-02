.method private isTaskbarEnabled(Lcom/android/launcher3/DeviceProfile;)Z
    .registers 4
    sget-boolean v0, Lcom/android/launcher3/config/FeatureFlags;->ENABLE_TASKBAR_NAVBAR_UNIFICATION:Z
    if-eqz v0, :check_dp
    invoke-static {}, Landroid/view/WindowManagerGlobal;->getWindowManagerService()Landroid/view/IWindowManager;
    move-result-object v0
    const/4 v1, 0x0
    :try_start
    invoke-interface {v0, v1}, Landroid/view/IWindowManager;->hasNavigationBar(I)Z
    move-result v0
    :try_end
    .catch Landroid/os/RemoteException; {:try_start .. :try_end} :ret_true
    if-eqz v0, :check_dp
    :ret_true
    const/4 v0, 0x1
    return v0
    :check_dp
    iget-boolean v0, p1, Lcom/android/launcher3/DeviceProfile;->isTaskbarPresent:Z
    return v0
.end method
