# 阿里云镜像仓库配置指南

## 前置要求

- GitHub 账户（用于配置 Actions）
- 阿里云账户（用于创建镜像仓库）

## 第一步：创建阿里云容器镜像服务（ACR）

### 1.1 登录阿里云

访问：https://cr.console.aliyun.com/

### 1.2 创建命名空间

1. 进入"命名空间"页面
2. 点击"创建命名空间"
3. 填写信息：
   - **命名空间名称**：例如 `your-namespace`
   - **自动创建仓库**：选择"私有"或"公开"（根据需求）
4. 点击"确定"

**注意**：命名空间名称将作为镜像路径的一部分，例如：
```
registry.cn-zhangjiakou.aliyuncs.com/your-namespace/image-name:tag
```

### 1.3 创建镜像仓库（可选）

ACR 支持自动创建仓库，也可以手动创建：

1. 进入"镜像仓库"页面
2. 点击"创建镜像仓库"
3. 填写信息：
   - **命名空间**：选择之前创建的命名空间
   - **仓库名称**：例如 `django-vue3-admin-django`
   - **仓库类型**：选择"私有"或"公开"
4. 点击"下一步" -> "创建镜像仓库"

建议创建以下仓库：
- `django-vue3-admin-django`
- `django-vue3-admin-web`
- `django-vue3-admin-celery`

## 第二步：获取访问凭证

### 2.1 使用固定密码（推荐用于测试）

1. 进入"访问凭证"页面
2. 点击"设置Registry登录密码"
3. 设置登录密码（如果还没有设置）
4. 记录以下信息：
   - **Registry 登录用户名**：通常是阿里云账号
   - **Registry 登录密码**：刚设置的密码

### 2.2 使用访问令牌（推荐用于生产环境）

1. 进入"访问凭证"页面
2. 点击"设置固定密码"旁边的"访问令牌"
3. 点击"创建访问令牌"
4. 填写信息：
   - **令牌名称**：例如 `github-actions-token`
   - **令牌有效期**：选择合适的时间（例如：90天）
   - **访问范围**：选择"全部"或特定仓库
   - **权限**：勾选"读取"、"写入"、"删除"
5. 点击"确定"
6. **重要**：立即复制生成的令牌（只显示一次）

## 第三步：配置 GitHub Secrets

### 3.1 进入 GitHub 仓库设置

1. 打开你的 GitHub 仓库
2. 点击 `Settings` 标签
3. 左侧菜单选择 `Secrets and variables`
4. 点击 `Actions` 标签
5. 点击 `New repository secret` 按钮

### 3.2 添加 Secrets

需要添加以下 3 个 Secrets：

#### Secret 1: ALIYUN_NAMESPACE

- **Name**: `ALIYUN_NAMESPACE`
- **Value**: 你的阿里云命名空间名称
- **示例**: `your-namespace`

#### Secret 2: ALIYUN_USERNAME

- **Name**: `ALIYUN_USERNAME`
- **Value**: 阿里云 Registry 登录用户名
- **示例**: `your-aliyun-username`

#### Secret 3: ALIYUN_PASSWORD

- **Name**: `ALIYUN_PASSWORD`
- **Value**: 阿里云 Registry 登录密码或访问令牌
- **示例**: `your-password-or-token`

### 3.3 验证 Secrets

添加完成后，Secrets 列表应该显示：

```
ALIYUN_NAMESPACE          Updated 2 minutes ago
ALIYUN_USERNAME          Updated 2 minutes ago
ALIYUN_PASSWORD          Updated 2 minutes ago
```

## 第四步：触发自动构建

### 4.1 推送代码

```bash
git add .
git commit -m "Update code"
git push origin main
```

### 4.2 查看构建状态

1. 进入 GitHub 仓库
2. 点击 `Actions` 标签
3. 查看最新的 workflow 运行状态

构建过程包括：
1. ✅ Checkout code - 检出代码
2. ✅ Set up Docker Buildx - 设置 Docker 构建环境
3. ✅ Login to Aliyun Container Registry - 登录阿里云
4. ✅ Build Django image - 构建 Django 镜像
5. ✅ Build Web image - 构建 Web 镜像
6. ✅ Build Celery image - 构建 Celery 镜像

### 4.3 验证镜像推送

1. 登录阿里云 ACR 控制台
2. 进入"镜像仓库"页面
3. 选择你的命名空间
4. 查看以下镜像是否已推送：
   - `django-vue3-admin-django`
   - `django-vue3-admin-web`
   - `django-vue3-admin-celery`

## 第五步：使用镜像部署

### 5.1 本地登录阿里云镜像仓库

```bash
docker login registry.cn-zhangjiakou.aliyuncs.com
```

输入用户名和密码（或访问令牌）。

### 5.2 拉取镜像

```bash
# 拉取 Django 镜像
docker pull registry.cn-zhangjiakou.aliyuncs.com/your-namespace/django-vue3-admin-django:latest

# 拉取 Web 镜像
docker pull registry.cn-zhangjiakou.aliyuncs.com/your-namespace/django-vue3-admin-web:latest

# 拉取 Celery 镜像
docker pull registry.cn-zhangjiakou.aliyuncs.com/your-namespace/django-vue3-admin-celery:latest
```

### 5.3 修改 docker-compose.yml

```yaml
services:
  dvadmin3-django:
    image: registry.cn-zhangjiakou.aliyuncs.com/your-namespace/django-vue3-admin-django:latest
    
  dvadmin3-web:
    image: registry.cn-zhangjiakou.aliyuncs.com/your-namespace/django-vue3-admin-web:latest
    
  dvadmin3-celery:
    image: registry.cn-zhangjiakou.aliyuncs.com/your-namespace/django-vue3-admin-celery:latest
```

### 5.4 启动服务

```bash
docker-compose down
docker-compose pull
docker-compose up -d
```

## 常见问题

### Q1: 构建失败，提示登录失败

**原因**：GitHub Secrets 配置错误

**解决方法**：
1. 检查 `ALIYUN_USERNAME` 是否正确
2. 检查 `ALIYUN_PASSWORD` 是否正确（注意访问令牌只显示一次）
3. 重新生成访问令牌并更新 Secret

### Q2: 镜像推送成功但拉取失败

**原因**：本地未登录阿里云镜像仓库

**解决方法**：
```bash
docker logout registry.cn-zhangjiakou.aliyuncs.com
docker login registry.cn-zhangjiakou.aliyuncs.com
```

### Q3: 构建速度慢

**原因**：网络问题或镜像较大

**解决方法**：
- 使用阿里云的构建缓存（已配置）
- 优化 Dockerfile，减少层数
- 使用多阶段构建

### Q4: 访问令牌过期

**原因**：访问令牌有有效期限制

**解决方法**：
1. 登录阿里云 ACR
2. 删除过期的访问令牌
3. 创建新的访问令牌
4. 更新 GitHub Secret `ALIYUN_PASSWORD`

### Q5: 权限不足

**原因**：访问令牌权限配置不正确

**解决方法**：
1. 检查访问令牌的权限设置
2. 确保包含"读取"、"写入"、"删除"权限
3. 重新创建访问令牌

## 最佳实践

### 1. 使用访问令牌而非固定密码

访问令牌更安全，可以：
- 设置有效期
- 限制访问范围
- 随时撤销

### 2. 定期轮换访问令牌

建议每 90 天轮换一次访问令牌：
1. 创建新的访问令牌
2. 更新 GitHub Secret
3. 撤销旧的访问令牌

### 3. 使用私有仓库

对于生产环境，建议使用私有镜像仓库：
- 创建时选择"私有"
- 避免敏感信息泄露

### 4. 镜像标签管理

- `latest`: 用于开发环境，随时更新
- `{commit_sha}`: 用于生产环境，版本可追溯

### 5. 监控构建日志

定期查看 GitHub Actions 日志：
- 及时发现构建问题
- 优化构建速度
- 确保镜像推送成功

## 参考资料

- [阿里云容器镜像服务文档](https://help.aliyun.com/product/60716.html)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Docker Buildx 文档](https://docs.docker.com/buildx/working-with-buildx/)
