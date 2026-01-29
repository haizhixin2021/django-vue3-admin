from django.core.management.base import BaseCommand
from dvadmin.system.models import Menu, MenuButton, Role, RoleMenuButtonPermission


class Command(BaseCommand):
    help = '检查并修复读书内容菜单按钮权限'

    def handle(self, *args, **options):
        try:
            # 检查读书内容菜单是否存在
            try:
                menu = Menu.objects.get(name='读书签到')
                self.stdout.write(f'✓ 找到菜单: {menu.name}')
            except Menu.DoesNotExist:
                self.stdout.write(self.style.ERROR('✗ 未找到读书内容菜单'))
                return

            # 检查菜单按钮是否存在
            buttons = MenuButton.objects.filter(menu=menu)
            self.stdout.write(f'✓ 菜单按钮数量: {buttons.count()}')
            for btn in buttons:
                self.stdout.write(f'  - {btn.name} ({btn.value})')

            # 检查管理员角色
            try:
                admin_role = Role.objects.get(name='管理员')
                self.stdout.write(f'✓ 找到角色: {admin_role.name}')
            except Role.DoesNotExist:
                self.stdout.write(self.style.ERROR('✗ 未找到管理员角色'))
                return

            # 检查管理员角色的按钮权限
            permissions = RoleMenuButtonPermission.objects.filter(role=admin_role, menu_button__menu=menu)
            self.stdout.write(f'✓ 管理员角色按钮权限数量: {permissions.count()}')
            for perm in permissions:
                self.stdout.write(f'  - {perm.menu_button.name} ({perm.menu_button.value})')

            # 检查是否缺少编辑和删除权限
            update_btn = buttons.filter(value='readContent:Update').first()
            delete_btn = buttons.filter(value='readContent:Delete').first()

            if not update_btn:
                self.stdout.write(self.style.WARNING('✗ 缺少编辑按钮'))
            else:
                has_update_perm = permissions.filter(menu_button=update_btn).exists()
                if not has_update_perm:
                    self.stdout.write(self.style.WARNING('✗ 管理员角色缺少编辑权限'))
                    # 创建权限
                    RoleMenuButtonPermission.objects.create(
                        role=admin_role,
                        menu_button=update_btn
                    )
                    self.stdout.write(self.style.SUCCESS('✓ 已为管理员角色添加编辑权限'))
                else:
                    self.stdout.write(f'✓ 管理员角色已有编辑权限')

            if not delete_btn:
                self.stdout.write(self.style.WARNING('✗ 缺少删除按钮'))
            else:
                has_delete_perm = permissions.filter(menu_button=delete_btn).exists()
                if not has_delete_perm:
                    self.stdout.write(self.style.WARNING('✗ 管理员角色缺少删除权限'))
                    # 创建权限
                    RoleMenuButtonPermission.objects.create(
                        role=admin_role,
                        menu_button=delete_btn
                    )
                    self.stdout.write(self.style.SUCCESS('✓ 已为管理员角色添加删除权限'))
                else:
                    self.stdout.write(f'✓ 管理员角色已有删除权限')

            self.stdout.write(self.style.SUCCESS('权限检查完成！'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'权限检查失败：{str(e)}'))
            import traceback
            traceback.print_exc()
