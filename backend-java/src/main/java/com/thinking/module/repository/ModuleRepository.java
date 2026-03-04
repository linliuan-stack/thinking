package com.thinking.module.repository;

import com.thinking.module.model.Module;
import com.thinking.module.model.UserPermission;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public class ModuleRepository {

    private final JdbcTemplate jdbcTemplate;

    public ModuleRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    private final RowMapper<Module> moduleRowMapper = (rs, rowNum) -> {
        Module m = new Module();
        m.setId(rs.getInt("id"));
        m.setName(rs.getString("name"));
        m.setDescription(rs.getString("description"));
        m.setIcon(rs.getString("icon"));
        m.setStatus(rs.getString("status"));
        m.setServiceType(rs.getString("service_type"));
        m.setCreatedAt(rs.getTimestamp("created_at").toLocalDateTime());
        return m;
    };

    private final RowMapper<UserPermission> permissionRowMapper = (rs, rowNum) -> {
        UserPermission p = new UserPermission();
        p.setId(rs.getInt("id"));
        p.setUserId(rs.getInt("user_id"));
        p.setModuleId(rs.getInt("module_id"));
        p.setCanAccess(rs.getBoolean("can_access"));
        p.setModuleName(rs.getString("name"));
        p.setModuleDescription(rs.getString("description"));
        p.setModuleIcon(rs.getString("icon"));
        p.setModuleStatus(rs.getString("status"));
        p.setServiceType(rs.getString("service_type"));
        return p;
    };

    public List<Module> findAll() {
        return jdbcTemplate.query("SELECT * FROM modules ORDER BY id", moduleRowMapper);
    }

    public List<UserPermission> findPermissionsByUserId(int userId) {
        String sql = """
            SELECT up.id, up.user_id, up.module_id, up.can_access,
                   m.name, m.description, m.icon, m.status, m.service_type
            FROM user_permissions up
            JOIN modules m ON up.module_id = m.id
            WHERE up.user_id = ?
            ORDER BY m.id
            """;
        return jdbcTemplate.query(sql, permissionRowMapper, userId);
    }

    public void updatePermission(int userId, int moduleId, boolean canAccess) {
        jdbcTemplate.update(
            "UPDATE user_permissions SET can_access = ? WHERE user_id = ? AND module_id = ?",
            canAccess, userId, moduleId
        );
    }
}
