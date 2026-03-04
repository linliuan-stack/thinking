CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS modules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    service_type VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    module_id INTEGER NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    can_access BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, module_id)
);

INSERT INTO modules (name, description, icon, status, service_type) VALUES
    ('用户管理', '管理系统用户、角色和权限', 'UserOutlined', 'active', 'python'),
    ('数据分析', '数据可视化与统计分析', 'BarChartOutlined', 'active', 'python'),
    ('订单管理', '订单处理与跟踪管理', 'ShoppingCartOutlined', 'active', 'java'),
    ('库存管理', '商品库存管理与预警', 'DatabaseOutlined', 'active', 'java'),
    ('报表中心', '生成和导出各类报表', 'FileTextOutlined', 'active', 'python'),
    ('系统监控', '系统运行状态监控', 'DashboardOutlined', 'active', 'java'),
    ('消息中心', '站内消息和通知管理', 'BellOutlined', 'active', 'python'),
    ('API网关', 'API路由与流量控制', 'ApiOutlined', 'active', 'java')
ON CONFLICT DO NOTHING;
