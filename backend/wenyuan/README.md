# 读书签到应用开发文档

## 应用概述

这是一个读书签到管理应用，用于记录读书内容和签到人员信息。

## 功能特点

1. **读书内容管理**
   - 录入读书日期和读书内容
   - 支持增删改查操作

2. **读书签到管理**
   - 支持批量添加签到人员
   - 自动解析签到人员格式（如：1.杨艳2.刘艾英3.杨熙英...）
   - 关联读书内容记录

## 后端文件结构

```
wenyuan/
├── __init__.py
├── admin.py
├── apps.py
├── models.py              # 数据模型
├── serializers.py         # 序列化器
├── views.py             # 视图
├── urls.py              # 路由配置
├── tests.py
└── fixtures/
    └── init_menu.json    # 菜单初始化数据
```

## 数据模型

### ReadContent（读书内容表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| read_date | Char(8) | 读书日期 |
| read_content | Char(5000) | 读书内容 |
| create_datetime | DateTime | 创建时间 |
| update_datetime | DateTime | 更新时间 |

### ReadSign（读书签到表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| read_content | ForeignKey | 关联读书内容 |
| read_person | Char(50) | 读书人员姓名 |
| rank | Integer | 排名序号 |
| create_datetime | DateTime | 创建时间 |
| update_datetime | DateTime | 更新时间 |

## 安装步骤

### 1. 注册应用

在 `backend/application/settings.py` 的 `INSTALLED_APPS` 中添加：

```python
INSTALLED_APPS = [
    # ... 其他应用
    "wenyuan",
]
```

### 2. 创建数据库迁移

```bash
cd backend
python3 manage.py makemigrations wenyuan
python3 manage.py migrate
```

### 3. 初始化菜单数据

运行初始化脚本：

```bash
cd backend
python manage.py loaddata wenyuan/fixtures/init_menu.json
```

或者使用 Django Shell：

```python
from wenyuan.management.commands.init_wenyuan_menu import Command
Command().handle()
```

### 4. 为角色分配菜单权限

在系统管理界面中：
1. 进入「角色管理」
2. 点击角色的「权限配置」
3. 勾选「文苑管理」菜单及其子菜单
4. 保存

### 5. 为角色分配按钮权限

在系统管理界面中：
1. 进入「角色管理」
2. 点击角色的「权限配置」
3. 点击「读书内容」菜单
4. 在「接口权限」标签页中勾选需要的按钮权限
5. 点击「读书签到」菜单
6. 在「接口权限」标签页中勾选需要的按钮权限
7. 保存

## 前端文件结构

```
web/src/views/wenyuan/
├── readContent/           # 读书内容
│   ├── api.ts            # API 接口
│   ├── crud.tsx          # CRUD 配置
│   └── index.vue         # 页面组件
└── readSign/             # 读书签到
    ├── api.ts            # API 接口
    ├── crud.tsx          # CRUD 配置
    └── index.vue         # 页面组件
```

## 使用说明

### 读书内容管理

1. 进入「文苑管理」→「读书内容」
2. 点击「新增」按钮
3. 填写读书日期和读书内容
4. 点击确定保存

### 读书签到管理

1. 进入「文苑管理」→「读书签到」
2. 点击「批量添加签到」按钮
3. 选择读书内容
4. 输入签到人员，格式为：`序号.姓名`
   - 例如：`1.杨艳2.刘艾英3.杨熙英4.周小鸥 5.马小平...`
5. 点击确定，系统会自动解析并创建多条签到记录

### 签到人员格式说明

签到人员格式要求：
- 每个人用 `序号.姓名` 的格式表示
- 多个人之间不需要分隔符，直接连接即可
- 序号必须是数字
- 姓名不能包含数字

示例：
```
1.杨艳2.刘艾英3.杨熙英4.周小鸥 5.马小平6.韩歌军7.谭雁红8.赵艳香9.张迎春10.常风仙11.赵红12.韩果香13.张慧14.梁文喜15.李瑞珍16.李普17.润兰18.刘剑勇19.白莉20.何晓英21.李淑玲22.谷润贞23.陶琳24.段燕文25胡秀英26.李小玲27.何雯曈28.王虹29.刘春英30.王改萍31.田琦琪32.吕蕴颖33.李效中34.申见先35.史艳红36.纪霞东37.武卫岗38.申太仙39.孙丽君40.马聚会41.李海军42.谢锋辉43.王朝阳44.赵建华45.梁艳46.段宣刚47.赵育新48.史鹏飞49.邢燕50.
```

## API 接口

### 读书内容接口

- `GET /api/wenyuan/read_content/` - 查询列表
- `GET /api/wenyuan/read_content/{id}/` - 获取详情
- `POST /api/wenyuan/read_content/` - 新增
- `PUT /api/wenyuan/read_content/{id}/` - 修改
- `DELETE /api/wenyuan/read_content/{id}/` - 删除

### 读书签到接口

- `GET /api/wenyuan/read_sign/` - 查询列表
- `GET /api/wenyuan/read_sign/{id}/` - 获取详情
- `POST /api/wenyuan/read_sign/` - 新增
- `PUT /api/wenyuan/read_sign/{id}/` - 修改
- `DELETE /api/wenyuan/read_sign/{id}/` - 删除

## 权限标识

### 读书内容

- `readContent:Search` - 查询
- `readContent:Retrieve` - 单例
- `readContent:Create` - 新增
- `readContent:Update` - 编辑
- `readContent:Delete` - 删除

### 读书签到

- `readSign:Search` - 查询
- `readSign:Retrieve` - 单例
- `readSign:Create` - 新增
- `readSign:Update` - 编辑
- `readSign:Delete` - 删除

## 注意事项

1. **数据库迁移**：修改模型后必须运行 `makemigrations` 和 `migrate`
2. **权限配置**：新应用需要为角色分配菜单和按钮权限
3. **签到人员格式**：批量添加时必须按照 `序号.姓名` 的格式输入
4. **关联关系**：签到记录必须关联到读书内容
5. **重新登录**：权限配置后需要重新登录才能生效

## 常见问题

### Q: 找不到「文苑管理」菜单？

A: 请检查：
1. 是否运行了菜单初始化脚本
2. 当前用户的角色是否被分配了「文苑管理」菜单权限
3. 是否重新登录了系统

### Q: 批量添加签到失败？

A: 请检查：
1. 签到人员格式是否正确（序号.姓名）
2. 是否选择了读书内容
3. 是否有新增签到的权限

### Q: 如何修改签到人员列表？

A: 可以在前端代码中修改 `readSign/index.vue` 文件中的提示文本，或者在数据库中直接修改记录。

## 扩展功能建议

1. 添加签到统计功能（统计每个人签到的次数）
2. 添加签到导出功能（导出为 Excel）
3. 添加签到提醒功能（定时提醒签到）
4. 添加签到照片上传功能
5. 添加签到时间记录功能
