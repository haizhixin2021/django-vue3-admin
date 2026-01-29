# Django Vue3 Admin - Docker 部署

## 项目简介

Django Vue3 Admin 是一个基于 Django + Vue3 的后台管理系统，支持 Docker 容器化部署。

## 快速开始

### 前置要求

- Docker >= 20.10
- Docker Compose >= 2.0
- Git

### 1. 克隆项目

```bash
git clone https://github.com/your-username/django-vue3-admin.git
cd django-vue3-admin
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置必要的密码：

```env
MYSQL_PASSWORD=your_secure_password
REDIS_PASSWORD=your_redis_password
```

### 3. 启动所有服务

```bash
docker-compose up -d
```

这将启动以下服务：
- `dvadmin3-web`: Vue3 前端（端口 8080）
- `dvadmin3-django`: Django 后端（端口 8000）
- `dvadmin3-mysql`: MySQL 数据库（端口 3306）
- `dvadmin3-celery`: Celery 异步任务
- `dvadmin3-redis`: Redis 缓存和消息队列（端口 6379）

### 4. 访问应用

打开浏览器访问：

- 前端界面：http://localhost:8080
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

## GitHub Actions 自动构建

### 配置步骤

1. **Fork 本仓库到你的 GitHub 账户**

2. **添加 Docker Hub Secrets**

   进入你的 GitHub 仓库：
   - `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`
   
   添加以下 secrets：
   
   | Secret 名称 | 说明 | 示例 |
   |------------|------|------|
   | `DOCKER_USERNAME` | Docker Hub 用户名 | `your-dockerhub-username` |
   | `DOCKER_PASSWORD` | Docker Hub 密码或访问令牌 | `dckr_pat_xxxxxxxx` |

3. **触发自动构建**

   当代码推送到 `main` 或 `master` 分支时，GitHub Actions 会自动：
   - 构建 Django 后端 Docker 镜像
   - 构建 Web 前端 Docker 镜像
   - 构建 Celery Docker 镜像
   - 推送所有镜像到 Docker Hub

### 镜像标签策略

- `latest`: 始终指向最新的构建
- `{commit_sha}`: 基于特定 Git 提交的版本（例如：`a1b2c3d`）

### 使用自动构建的镜像

修改 `docker-compose.yml` 中的镜像引用：

```yaml
services:
  dvadmin3-django:
    image: your-dockerhub-username/django-vue3-admin-django:latest
    
  dvadmin3-web:
    image: your-dockerhub-username/django-vue3-admin-web:latest
    
  dvadmin3-celery:
    image: your-dockerhub-username/django-vue3-admin-celery:latest
```

然后拉取最新镜像并重启服务：

```bash
docker-compose down
docker-compose pull
docker-compose up -d
```

## Docker 镜像说明

### 后端镜像

- **基础镜像**: `registry.cn-zhangjiakou.aliyuncs.com/dvadmin-pro/dvadmin3-base-backend:latest`
- **工作目录**: `/backend`
- **端口**: 8000
- **依赖**: MySQL, Redis

### 前端镜像

- **基础镜像**: `registry.cn-zhangjiakou.aliyuncs.com/dvadmin-pro/dvadmin3-base-web:18.20-alpine`
- **工作目录**: `/web/`
- **端口**: 8080
- **Web 服务器**: Nginx

### Celery 镜像

- **基础镜像**: 与后端相同
- **工作目录**: `/backend`
- **依赖**: MySQL, Redis

## 数据持久化

以下目录已挂载到宿主机，确保数据不会丢失：

| 宿主机目录 | 容器内路径 | 说明 |
|------------|-------------|------|
| `./backend` | `/backend` | Django 后端代码 |
| `./backend/media` | `/backend/media` | 媒体文件上传 |
| `./docker_env/mysql/data` | `/var/lib/mysql` | MySQL 数据库数据 |
| `./docker_env/redis/data` | `/data` | Redis 持久化数据 |
| `./logs/log` | `/var/log` | 应用日志 |

## 网络配置

项目使用自定义 Docker 网络：

- **网络名称**: `network`
- **子网**: `177.10.0.0/16`
- **各服务 IP**:
  - Django: `177.10.0.12`
  - MySQL: `177.10.0.13`
  - Celery: `177.10.0.14`
  - Redis: `177.10.0.15`

## 常用命令

### 查看服务状态

```bash
docker-compose ps
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f dvadmin3-django
docker-compose logs -f dvadmin3-web
```

### 停止服务

```bash
docker-compose down
```

### 重启服务

```bash
docker-compose restart
```

### 进入容器

```bash
# 进入 Django 容器
docker-compose exec dvadmin3-django sh

# 进入 Web 容器
docker-compose exec dvadmin3-web sh

# 进入 MySQL 容器
docker-compose exec dvadmin3-mysql bash
```

### 执行 Django 管理命令

```bash
docker-compose exec dvadmin3-django python manage.py migrate
docker-compose exec dvadmin3-django python manage.py createsuperuser
```

## 故障排查

### 端口冲突

如果端口已被占用，修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "8081:8080"  # 修改为其他端口
```

### 权限问题

确保挂载目录有正确的权限：

```bash
chmod -R 755 backend
chmod -R 755 logs
chmod -R 755 docker_env
```

### 数据库连接失败

1. 检查 MySQL 容器是否正常运行：
   ```bash
   docker-compose ps
   docker-compose logs dvadmin3-mysql
   ```

2. 检查网络连接：
   ```bash
   docker-compose exec dvadmin3-django ping 177.10.0.13
   ```

3. 验证数据库配置：
   ```bash
   docker-compose exec dvadmin3-django cat conf/env.py | grep DATABASE
   ```

### Redis 连接失败

```bash
docker-compose exec dvadmin3-django ping 177.10.0.15
docker-compose logs dvadmin3-redis
```

## 生产环境部署建议

### 1. 使用环境变量管理敏感信息

不要将密码等敏感信息提交到代码库，使用 `.env` 文件（已添加到 `.gitignore`）。

### 2. 配置 HTTPS

使用 Nginx 反向代理配置 SSL 证书。

### 3. 设置日志轮转

配置日志轮转策略，避免日志文件过大。

### 4. 定期备份数据

```bash
# 备份 MySQL 数据
docker-compose exec dvadmin3-mysql mysqldump -u root -p django-vue3-admin > backup.sql

# 备份 Redis 数据
docker-compose exec dvadmin3-redis redis-cli --rdb /data/dump.rdb SAVE
```

### 5. 监控和告警

配置容器健康检查和监控告警。

## 技术栈

- **后端**: Django 4.x + DRF
- **前端**: Vue 3 + Element Plus
- **数据库**: MySQL 8.0
- **缓存**: Redis 6.2
- **异步任务**: Celery
- **Web 服务器**: Nginx
- **容器化**: Docker + Docker Compose

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 支持

如有问题，请提交 [Issue](https://github.com/your-username/django-vue3-admin/issues)。
