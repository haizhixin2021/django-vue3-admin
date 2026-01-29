#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings')
django.setup()

from dvadmin.system.models import Menu, MenuButton, Role, RoleMenuButtonPermission

def add_scan_data_menu_buttons():
    """为扫码数据菜单添加按钮权限"""
    print("开始为扫码数据菜单添加按钮权限...")

    # 获取扫码数据菜单
    try:
        scan_data_menu = Menu.objects.get(component_name='scanData')
        print(f"找到菜单: {scan_data_menu.name} (ID: {scan_data_menu.id})")
    except Menu.DoesNotExist:
        print("✗ 找不到扫码数据菜单！")
        return

    # 定义要添加的按钮权限
    buttons_data = [
        {
            'name': '查询',
            'value': 'scanData:Search',
            'api': '/api/code_info/scan_data/',
            'method': 0
        },
        {
            'name': '单例',
            'value': 'scanData:Retrieve',
            'api': '/api/code_info/scan_data/{id}/',
            'method': 0
        },
        {
            'name': '新增',
            'value': 'scanData:Create',
            'api': '/api/code_info/scan_data/',
            'method': 1
        },
        {
            'name': '编辑',
            'value': 'scanData:Update',
            'api': '/api/code_info/scan_data/{id}/',
            'method': 2
        },
        {
            'name': '删除',
            'value': 'scanData:Delete',
            'api': '/api/code_info/scan_data/{id}/',
            'method': 3
        }
    ]

    # 创建按钮权限
    for btn_data in buttons_data:
        btn, created = MenuButton.objects.get_or_create(
            menu=scan_data_menu,
            value=btn_data['value'],
            defaults={
                'name': btn_data['name'],
                'api': btn_data['api'],
                'method': btn_data['method'],
                'status': True
            }
        )

        if created:
            print(f"  ✓ 创建按钮: {btn.name} ({btn.value})")
        else:
            print(f"  - 按钮已存在: {btn.name} ({btn.value})")

    print(f"\n成功为 {scan_data_menu.name} 菜单添加了 {len(buttons_data)} 个按钮权限！")

def assign_buttons_to_admin_role():
    """为管理员角色分配扫码数据的按钮权限"""
    print("\n开始为管理员角色分配扫码数据按钮权限...")

    try:
        admin_role = Role.objects.get(key='admin')
        print(f"找到角色: {admin_role.name} (key: {admin_role.key})")
    except Role.DoesNotExist:
        print("✗ 找不到管理员角色！")
        return

    # 获取扫码数据菜单的所有按钮
    try:
        scan_data_menu = Menu.objects.get(component_name='scanData')
        buttons = MenuButton.objects.filter(menu_id=scan_data_menu.id)
        print(f"找到 {buttons.count()} 个按钮")
    except Menu.DoesNotExist:
        print("✗ 找不到扫码数据菜单！")
        return

    # 为管理员角色分配按钮权限
    assigned_count = 0
    for button in buttons:
        if not RoleMenuButtonPermission.objects.filter(
            role=admin_role,
            menu_button=button
        ).exists():
            RoleMenuButtonPermission.objects.create(
                role=admin_role,
                menu_button=button,
                data_range=0  # 默认仅本人数据权限
            )
            assigned_count += 1
            print(f"  ✓ 分配按钮: {button.name} ({button.value})")

    print(f"\n成功为管理员角色分配了 {assigned_count} 个按钮权限！")

if __name__ == '__main__':
    # 1. 添加按钮权限
    add_scan_data_menu_buttons()

    # 2. 为管理员角色分配按钮权限
    assign_buttons_to_admin_role()

    print("\n" + "=" * 60)
    print("操作完成！请重新登录系统以使权限生效。")
    print("=" * 60)
