from urllib.parse import quote

from django.http import HttpResponse
from dvadmin.utils.viewset import CustomModelViewSet
from dvadmin.utils.json_response import SuccessResponse, ErrorResponse
from wenyuan.models import ReadContent, ReadSign
from wenyuan.serializers import ReadContentSerializer, ReadContentCreateSerializer, ReadContentImportSerializer, ReadSignSerializer, ReadSignCreateSerializer
from django_filters import rest_framework as filters
from django.db import transaction
from django.db.models import Count
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from rest_framework.decorators import action
import re
from wenyuan.llm_service import SignListLLMParser



class ReadContentFilter(filters.FilterSet):
    """
    读书内容过滤器
    """
    read_date = filters.CharFilter(method='filter_read_date')

    def filter_read_date(self, queryset, name, value):
        print(f"DEBUG: filter_read_date 被调用，name = {name}, value = {value}, type = {type(value)}")
        
        # 检查是否有 read_date[0] 和 read_date[1] 参数
        request = self.request
        start_date = request.query_params.get('read_date[0]')
        end_date = request.query_params.get('read_date[1]')
        
        if start_date and end_date:
            print(f"DEBUG: 日期范围查询 - 起始日期: {start_date}, 终止日期: {end_date}")
            return queryset.filter(read_date__gte=start_date, read_date__lte=end_date)
        
        if not value:
            print(f"DEBUG: value 为空，不过滤")
            return queryset

        if ',' in value:
            start_date, end_date = value.split(',')
            print(f"DEBUG: 日期范围查询 - 起始日期: {start_date}, 终止日期: {end_date}")
            return queryset.filter(read_date__gte=start_date, read_date__lte=end_date)
        else:
            print(f"DEBUG: 单个日期查询: {value}")
            return queryset.filter(read_date=value)

    class Meta:
        model = ReadContent
        fields = ['read_date']


class ReadSignFilter(filters.FilterSet):
    """
    读书签到过滤器
    """
    read_date = filters.CharFilter(method='filter_read_date')
    read_person = filters.CharFilter(lookup_expr='icontains')
    read_content_id = filters.NumberFilter(method='filter_read_content_id')

    def filter_read_date(self, queryset, name, value):
        if not value:
            return queryset

        if ',' in value:
            start_date, end_date = value.split(',')
            return queryset.filter(read_content__read_date__gte=start_date, read_content__read_date__lte=end_date)
        else:
            return queryset.filter(read_content__read_date=value)

    def filter_read_content_id(self, queryset, name, value):
        print(f"DEBUG: filter_read_content_id 被调用，value = {value}, type = {type(value)}")
        if not value:
            print(f"DEBUG: read_content_id 为空，不过滤")
            return queryset
        print(f"DEBUG: 使用 read_content_id = {value} 过滤")
        return queryset.filter(read_content_id=value)

    class Meta:
        model = ReadSign
        fields = ['read_date', 'read_person', 'read_content_id']


class ReadContentViewSet(CustomModelViewSet):
    """
    读书内容接口
    list:查询
    create:新增
    update:修改
    retrieve:单例
    destroy:删除
    """
    queryset = ReadContent.objects.all()
    serializer_class = ReadContentSerializer
    create_serializer_class = ReadContentCreateSerializer
    update_serializer_class = ReadContentCreateSerializer
    filter_class = ReadContentFilter
    import_serializer_class = ReadContentImportSerializer
    import_field_dict = {
        "read_date": "读书日期",
        "read_content": "读书内容",
        "sign_list": "签到列表",
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 手动处理日期范围查询
        start_date = self.request.query_params.get('read_date[0]')
        end_date = self.request.query_params.get('read_date[1]')
        
        if start_date and end_date:
            print(f"DEBUG: get_queryset 处理日期范围查询 - 起始日期: {start_date}, 终止日期: {end_date}")
            queryset = queryset.filter(read_date__gte=start_date, read_date__lte=end_date)
        
        return queryset

    def list(self, request, *args, **kwargs):
        print(f"DEBUG: ReadContentViewSet.list 被调用")
        print(f"DEBUG: request.query_params = {request.query_params}")
        print(f"DEBUG: request.GET = {request.GET}")
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        sign_list = request.data.get('sign_list', '')
        print(f"DEBUG: 接收到的签到列表数据: {sign_list}")

        with transaction.atomic():
            response = super().create(request, *args, **kwargs)
            read_content_id = response.data.get('data').get('id')
            print(f"DEBUG: 创建的读书内容ID: {read_content_id}")

            if sign_list and read_content_id:
                print(f"DEBUG: 开始解析签到人员")
                self._parse_and_create_sign_records(read_content_id, sign_list)
                
                # 更新 sign_list 字段
                try:
                    read_content = ReadContent.objects.get(id=read_content_id)
                    read_content.sign_list = sign_list
                    read_content.save()
                    print(f"DEBUG: 成功更新 sign_list 字段")
                except Exception as e:
                    print(f"DEBUG: 更新 sign_list 字段失败: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"DEBUG: 签到人员数据为空或读书内容ID为空")

            return response

    def update(self, request, *args, **kwargs):
        sign_list = request.data.get('sign_list', '')
        print(f"DEBUG: 编辑接收到的签到列表数据: {sign_list}")

        with transaction.atomic():
            print(f"DEBUG: 1111111update 被调用")
            response = super().update(request, *args, **kwargs)
            read_content_id = kwargs.get('pk')
            print(f"DEBUG: 编辑的读书内容ID: {read_content_id}")

            if sign_list and read_content_id:
                print(f"DEBUG: 开始重新解析签到人员")
                self._delete_and_recreate_sign_records(read_content_id, sign_list)
                
                # 更新 sign_list 字段
                try:
                    read_content = ReadContent.objects.get(id=read_content_id)
                    print(f"DEBUG: 获取到的读书内容对象: {read_content}")
                    read_content.sign_list = sign_list
                    read_content.save()
                    print(f"DEBUG: 成功更新 sign_list 字段")
                except Exception as e:
                    print(f"DEBUG: 更新 sign_list 字段失败: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"DEBUG: 签到列表数据为空或读书内容ID为空，sign_list={sign_list}, read_content_id={read_content_id}")

            return response

    def _parse_and_create_sign_records(self, read_content_id, sign_list):
        """
        解析签到人员文本并创建签到记录
        格式：1.杨艳2.武卫岗3.谢锋辉4.赵艳香5.
        支持格式：1.杨艳2.刘艾英3李普4.王润兰5. 或 1.杨艳2.刘艾英3、李普4.王润兰5.
        """
        print(f"DEBUG: 原始签到列表文本: {sign_list}")

        # 调用dify工作流解析签到人员列表
        sign_parser = SignListLLMParser()
        sign_list = sign_parser._call_dify_workflow(sign_list)
        if not sign_list:
            print(f"DEBUG: 调用dify工作流解析失败，原始文本: {sign_list}")
            return

        # 统一分隔符：如果包含中文顿号，替换为英文句号
        #if '、' in sign_list:
        #    sign_list = sign_list.replace('、', '.')
        #    print(f"DEBUG: 替换中文顿号后的文本: {sign_list}")

        # 处理数字后面直接跟汉字的情况（没有分隔符），在数字和汉字之间插入句号
        # 匹配模式：数字后面直接跟汉字（不是句号）
        import re as regex_module
        #sign_list = regex_module.sub(r'(\d)([\u4e00-\u9fa5])', r'\1.\2', sign_list)
        print(f"DEBUG: 统一分隔符后的文本: {sign_list}")

        pattern = r'(\d+)\.([^\d.]+)'
        matches = regex_module.findall(pattern, sign_list)
        print(f"DEBUG: 解析到的匹配结果: {matches}")

        try:
            read_content = ReadContent.objects.get(id=read_content_id)
            print(f"DEBUG: 获取到的读书内容对象: {read_content}, 类型: {type(read_content)}")
        except ReadContent.DoesNotExist:
            print(f"DEBUG: 未找到ID为 {read_content_id} 的读书内容")
            return

        for rank_str, name in matches:
            rank = int(rank_str)
            name = name.strip()

            print(f"DEBUG: 准备创建签到记录 - 排名: {rank}, 人员: {name}")

            if name:
                sign_record = ReadSign.objects.create(
                    read_content=read_content,
                    read_date=read_content.read_date,
                    rank=rank,
                    read_person=name
                )
                print(f"DEBUG: 成功创建签到记录，ID: {sign_record.id}")

    def _delete_and_recreate_sign_records(self, read_content_id, sign_list):
        """
        删除旧的签到记录并重新创建
        格式：1.杨艳2.武卫岗3.谢锋辉4.赵艳香5.
        支持格式：1.杨艳2.刘艾英3李普4.王润兰5. 或 1.杨艳2.刘艾英3、李普4.王润兰5.
        """
        print(f"DEBUG: 删除读书内容ID {read_content_id} 的所有签到记录")
        ReadSign.objects.filter(read_content_id=read_content_id).delete()

        print(f"DEBUG: 原始签到列表文本: {sign_list}")

        # 调用dify工作流解析签到人员列表
        sign_parser = SignListLLMParser()
        sign_list = sign_parser._call_dify_workflow(sign_list)
        if not sign_list:
            print(f"DEBUG: 调用dify工作流解析失败，原始文本: {sign_list}")
            return

        # 统一分隔符：如果包含中文顿号，替换为英文句号
        #if '、' in sign_list:
        #    sign_list = sign_list.replace('、', '.')
        #    print(f"DEBUG: 替换中文顿号后的文本: {sign_list}")

        # 处理数字后面直接跟汉字的情况（没有分隔符），在数字和汉字之间插入句号
        # 匹配模式：数字后面直接跟汉字（不是句号）
        import re as regex_module
        #sign_list = regex_module.sub(r'(\d)([\u4e00-\u9fa5])', r'\1.\2', sign_list)
        print(f"DEBUG: 统一分隔符后的文本: {sign_list}")

        pattern = r'(\d+)\.([^\d.]+)'
        matches = regex_module.findall(pattern, sign_list)
        print(f"DEBUG: 解析到的匹配结果: {matches}")

        try:
            read_content = ReadContent.objects.get(id=read_content_id)
            print(f"DEBUG: 获取到的读书内容对象: {read_content}, 类型: {type(read_content)}")
        except ReadContent.DoesNotExist:
            print(f"DEBUG: 未找到ID为 {read_content_id} 的读书内容")
            return

        for rank_str, name in matches:
            rank = int(rank_str)
            name = name.strip()

            print(f"DEBUG: 准备创建签到记录 - 排名: {rank}, 人员: {name}")

            if name:
                sign_record = ReadSign.objects.create(
                    read_content=read_content,
                    read_date=read_content.read_date,
                    rank=rank,
                    read_person=name
                )
                print(f"DEBUG: 成功创建签到记录，ID: {sign_record.id}")


class ReadSignViewSet(CustomModelViewSet):
    """
    读书签到接口
    list:查询
    create:新增
    update:修改
    retrieve:单例
    destroy:删除
    """
    queryset = ReadSign.objects.all().order_by('rank')
    serializer_class = ReadSignSerializer
    create_serializer_class = ReadSignCreateSerializer
    update_serializer_class = ReadSignCreateSerializer
    filter_class = ReadSignFilter

    def list(self, request, *args, **kwargs):
        print(f"DEBUG: ReadSignViewSet.list 被调用")
        print(f"DEBUG: request.query_params = {request.query_params}")
        print(f"DEBUG: request.GET = {request.GET}")
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        """
        读书次数统计：按时间段统计每个人的读书次数
        参数: start_date (起始日期), end_date (终止日期)，格式 YYYYMMDD
        """
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        queryset = ReadSign.objects.all()
        if start_date and end_date:
            queryset = queryset.filter(read_date__gte=start_date, read_date__lte=end_date)

        stats = queryset.values('read_person').annotate(
            count=Count('id')
        ).order_by('-count')

        return SuccessResponse(data=list(stats), msg='获取统计数据成功')

    @action(detail=False, methods=['get'], url_path='export_statistics')
    def export_statistics(self, request):
        """
        导出读书统计到 Excel
        参数: start_date (起始日期), end_date (终止日期)，格式 YYYYMMDD
        """
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        queryset = ReadSign.objects.all()
        if start_date and end_date:
            queryset = queryset.filter(read_date__gte=start_date, read_date__lte=end_date)

        stats = list(
            queryset.values('read_person').annotate(count=Count('id')).order_by('-count')
        )

        # 生成文件名
        if start_date and end_date:
            filename = f"读书统计_{start_date}_{end_date}.xlsx"
        else:
            filename = f"读书统计.xlsx"

        wb = Workbook()
        ws = wb.active
        ws.title = "读书统计"

        # 表头
        headers = ["排名", "姓名", "读书次数"]
        ws.append(headers)

        # 表头加粗
        bold_font = Font(bold=True)
        for cell in ws[1]:
            cell.font = bold_font

        # 数据行
        total_count = 0
        for idx, item in enumerate(stats, 1):
            ws.append([idx, item['read_person'], item['count']])
            total_count += item['count']

        # 汇总行
        ws.append(["合计", f"{len(stats)} 人", total_count])
        last_row = ws.max_row
        for cell in ws[last_row]:
            cell.font = bold_font

        # 自动列宽
        for col_idx, header in enumerate(headers, 1):
            max_len = len(str(header))
            for row in ws.iter_rows(min_col=col_idx, max_col=col_idx, min_row=2, max_row=last_row):
                for cell in row:
                    cell_val = str(cell.value) if cell.value else ''
                    # 中文字符算 2 宽度
                    char_len = sum(2 if ord(c) > 127 else 1 for c in cell_val)
                    if char_len > max_len:
                        max_len = char_len
            ws.column_dimensions[get_column_letter(col_idx)].width = max_len + 4

        # 冻结首行
        ws.freeze_panes = 'A2'

        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Access-Control-Expose-Headers"] = "Content-Disposition"
        response["Content-Disposition"] = f'attachment;filename={quote(filename)}'
        wb.save(response)
        return response
