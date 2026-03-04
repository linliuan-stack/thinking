package com.thinking.module.model;

public class UserPermission {
    private Integer id;
    private Integer userId;
    private Integer moduleId;
    private Boolean canAccess;
    private String moduleName;
    private String moduleDescription;
    private String moduleIcon;
    private String moduleStatus;
    private String serviceType;

    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }
    public Integer getUserId() { return userId; }
    public void setUserId(Integer userId) { this.userId = userId; }
    public Integer getModuleId() { return moduleId; }
    public void setModuleId(Integer moduleId) { this.moduleId = moduleId; }
    public Boolean getCanAccess() { return canAccess; }
    public void setCanAccess(Boolean canAccess) { this.canAccess = canAccess; }
    public String getModuleName() { return moduleName; }
    public void setModuleName(String moduleName) { this.moduleName = moduleName; }
    public String getModuleDescription() { return moduleDescription; }
    public void setModuleDescription(String moduleDescription) { this.moduleDescription = moduleDescription; }
    public String getModuleIcon() { return moduleIcon; }
    public void setModuleIcon(String moduleIcon) { this.moduleIcon = moduleIcon; }
    public String getModuleStatus() { return moduleStatus; }
    public void setModuleStatus(String moduleStatus) { this.moduleStatus = moduleStatus; }
    public String getServiceType() { return serviceType; }
    public void setServiceType(String serviceType) { this.serviceType = serviceType; }
}
