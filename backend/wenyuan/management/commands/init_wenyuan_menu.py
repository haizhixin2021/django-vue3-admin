from django.core.management.base import BaseCommand
import json
from dvadmin.system.models import Menu, MenuButton


class Command(BaseCommand):
    help = '初始化文苑菜单数据'

    def handle(self, *args, **options):
        try:
            with open('wenyuan/fixtures/init_menu.json', 'r', encoding='utf-8') as f:
                menu_data = json.load(f)

            self.create_menus(menu_data)
            self.stdout.write(self.style.SUCCESS('菜单初始化成功！'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'菜单初始化失败：{str(e)}'))

    def create_menus(self, menu_list, parent=None):
        for menu_item in menu_list:
            try:
                menu, created = Menu.objects.get_or_create(
                    name=menu_item['name'],
                    web_path=menu_item.get('web_path'),
                    component_name=menu_item.get('component_name', ''),
                    defaults={
                        'parent': parent,
                        'icon': menu_item.get('icon'),
                        'sort': menu_item.get('sort', 1),
                        'is_link': menu_item.get('is_link', False),
                        'is_catalog': menu_item.get('is_catalog', False),
                        'web_path': menu_item.get('web_path'),
                        'component': menu_item.get('component', ''),
                        'component_name': menu_item.get('component_name', ''),
                        'status': menu_item.get('status', True),
                        'cache': menu_item.get('cache', False),
                        'visible': menu_item.get('visible', True),
                    }
                )

                if created:
                    self.stdout.write(f'  创建菜单: {menu.name}')
                else:
                    self.stdout.write(f'  菜单已存在: {menu.name}')

                if 'menu_button' in menu_item and menu_item['menu_button']:
                    self.create_menu_buttons(menu, menu_item['menu_button'])

                if 'children' in menu_item and menu_item['children']:
                    self.create_menus(menu_item['children'], menu)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  创建菜单 {menu_item.get("name")} 失败: {str(e)}'))

    def create_menu_buttons(self, menu, buttons):
        for btn_data in buttons:
            try:
                btn, created = MenuButton.objects.get_or_create(
                    menu=menu,
                    value=btn_data['value'],
                    defaults={
                        'name': btn_data['name'],
                        'api': btn_data['api'],
                        'method': btn_data['method']
                    }
                )

                if created:
                    self.stdout.write(f'    创建按钮: {btn.name}')
                else:
                    self.stdout.write(f'    按钮已存在: {btn.name}')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    创建按钮 {btn_data.get("name")} 失败: {str(e)}'))
