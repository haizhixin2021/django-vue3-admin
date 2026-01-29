# Docker 部署说明

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-username/django-vue3-admin.git
cd django-vue3-admin
```

### 2. 配置环境变量

复制 `.env.example` 文件为 `.env` 并修改相关配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置以下变量：

```env
# MySQL 密码
MYSQL_PASSWORD=your_mysql_password

# Redis 密码
REDIS_PASSWORD=your_redis_password
```

### 3. 启动服务

```bash
docker-compose up -d
```

### 4. 访问应用

- 前端：http://localhost:8080
- 后端：http://localhost:8000
- MySQL：localhost:3306
- Redis：localhost:6379

## GitHub Actions 自动构建

### 配置阿里云镜像仓库凭证

1. 登录阿里云容器镜像服务（ACR）
   - 访问：https://cr.console.aliyun.com/
   - 创建命名空间（如果还没有）
   - 获取访问凭证

2. 登录 GitHub 仓库
3. 进入 `Settings` -> `Secrets and variables` -> `Actions`
4. 添加以下 secrets：
   - `ALIYUN_NAMESPACE`: 阿里云命名空间
   - `ALIYUN_USERNAME`: 阿里云用户名
   - `ALIYUN_PASSWORD`: 阿里云密码或访问令牌

### 自动构建流程

当代码推送到 `main` 或 `master` 分支时，GitHub Actions 会自动：

1. 构建 Django 后端镜像并推送到阿里云镜像仓库
2. 构建 Web 前端镜像并推送到阿里云镜像仓库
3. 构建 Celery 镜像并推送到阿里云镜像仓库

### 镜像标签

- `latest`: 最新版本
- `{commit_sha}`: 基于 Git 提交 SHA 的版本

### 使用构建的镜像

修改 `docker-compose.yml` 中的镜像引用：

```yaml
services:
  dvadmin3-django:
    image: registry.cn-zhangjiakou.aliyuncs.com/your-namespace/django-vue3-admin-django:latest
    
  dvadmin3-web:
    image: registry.cn-zhangjiakou.aliyuncs.com/your-namespace/django-vue3-admin-web:latest
    
  dvadmin3-celery:
    image: registry.cn-zhangjiakou.aliyuncs.com/your-namespace/django-vue3-admin-celery:latest
```

然后重新启动服务：

```bash
docker-compose down
docker-compose pull
docker-compose up -d
```

## 常用命令

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

## 网络配置

项目使用自定义网络配置，确保服务之间可以正常通信：

- 网络名称：`network`
- 子网：`177.10.0.0/16`
- Django 容器 IP：`177.10.0.12`
- MySQL 容器 IP：`177.10.0.13`
- Redis 容器 IP：`177.10.0.15`

如果需要修改网络配置，请编辑 `docker-compose.yml` 中的 `networks` 部分。

## 数据持久化

以下目录已挂载到宿主机，数据不会丢失：

- `./backend`: Django 后端代码
- `./backend/media`: 媒体文件
- `./docker_env/mysql/data`: MySQL 数据
- `./docker_env/redis/data`: Redis 数据
- `./logs/log`: 日志文件

## 故障排查

### 端口冲突

如果端口已被占用，修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "8081:8080"  # 修改为其他端口
```

### 权限问题

确保以下目录有正确的权限：

```bash
chmod -R 755 backend
chmod -R 755 logs
chmod -R 755 docker_env
```

### 数据库连接失败

检查 MySQL 容器是否正常运行：

```bash
docker-compose ps
docker-compose logs dvadmin3-mysql
```

确保 `conf/env.py` 中的数据库配置正确。
