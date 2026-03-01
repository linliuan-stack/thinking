package com.thinking.module.controller;

import com.thinking.module.model.Module;
import com.thinking.module.model.UserPermission;
import com.thinking.module.repository.ModuleRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/modules")
public class ModuleController {

    private final ModuleRepository moduleRepository;

    public ModuleController(ModuleRepository moduleRepository) {
        this.moduleRepository = moduleRepository;
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "ok", "service", "module-java");
    }

    @GetMapping
    public List<Module> getAllModules() {
        return moduleRepository.findAll();
    }

    @GetMapping("/permissions/{userId}")
    public List<UserPermission> getPermissions(@PathVariable int userId) {
        return moduleRepository.findPermissionsByUserId(userId);
    }

    @PutMapping("/permissions")
    public ResponseEntity<Map<String, String>> updatePermission(@RequestBody Map<String, Object> body) {
        int userId = (int) body.get("userId");
        int moduleId = (int) body.get("moduleId");
        boolean canAccess = (boolean) body.get("canAccess");
        moduleRepository.updatePermission(userId, moduleId, canAccess);
        return ResponseEntity.ok(Map.of("message", "权限更新成功"));
    }
}
