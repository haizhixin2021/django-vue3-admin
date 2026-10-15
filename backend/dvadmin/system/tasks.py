from hashlib import md5
from io import BytesIO
from datetime import datetime
from time import sleep
import traceback

from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter
from django.core.files.base import ContentFile
from django.apps import apps

from application.celery import app
from dvadmin.system.models import DownloadCenter
from dvadmin.utils.import_export import import_to_data

def is_number(num):
    try:
        float(num)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(num)
        return True
    except (TypeError, ValueError):
        pass
    return False

def get_string_len(string):
    """
    获取字符串最大长度
    :param string:
    :return:
    """
    length = 4
    if string is None:
        return length
    if is_number(string):
        return length
    for char in string:
        length += 2.1 if ord(char) > 256 else 1
    return round(length, 1) if length <= 50 else 50

@app.task
def async_export_data(data: list, filename: str, dcid: int, export_field_label: dict):
    instance = DownloadCenter.objects.get(pk=dcid)
    instance.task_status = 1
    instance.save()
    sleep(2)
    try:
        wb = Workbook()
        ws = wb.active
        header_data = ["序号", *export_field_label.values()]
        hidden_header = ["#", *export_field_label.keys()]
        df_len_max = [get_string_len(ele) for ele in header_data]
        row = get_column_letter(len(export_field_label) + 1)
        column = 1
        ws.append(header_data)
        for index, results in enumerate(data):
            results_list = []
            for h_index, h_item in enumerate(hidden_header):
                for key, val in results.items():
                    if key == h_item:
                        if val is None or val == "":
                            results_list.append("")
                        elif isinstance(val, datetime):
                            val = val.strftime("%Y-%m-%d %H:%M:%S")
                            results_list.append(val)
                        else:
                            results_list.append(val)
                        # 计算最大列宽度
                        result_column_width = get_string_len(val)
                        if h_index != 0 and result_column_width > df_len_max[h_index]:
                            df_len_max[h_index] = result_column_width
            ws.append([index + 1, *results_list])
            column += 1
        # 　更新列宽
        for index, width in enumerate(df_len_max):
            ws.column_dimensions[get_column_letter(index + 1)].width = width
        tab = Table(displayName="Table", ref=f"A1:{row}{column}")  # 名称管理器
        style = TableStyleInfo(
            name="TableStyleLight11",
            showFirstColumn=True,
            showLastColumn=True,
            showRowStripes=True,
            showColumnStripes=True,
        )
        tab.tableStyleInfo = style
        ws.add_table(tab)
        stream = BytesIO()
        wb.save(stream)
        stream.seek(0)
        s = md5()
        while True:
            chunk = stream.read(1024)
            if not chunk:
                break
            s.update(chunk)
        stream.seek(0)
        instance.md5sum = s.hexdigest()
        instance.file_name = filename
        instance.url.save(filename, ContentFile(stream.read()))
        instance.task_status = 2
    except Exception as e:
        instance.task_status = 3
        instance.description = str(e)[:250]
    instance.save()


@app.task(bind=True)
def async_import_data(self, file_url, model_class_path, serializer_class_path,
                      import_field_dict, import_serializer_class_path, dcid,
                      user_info=None):
    """
    异步批量导入数据
    :param file_url: 上传的 Excel 文件路径（相对 media 根目录）
    :param model_class_path: 模型类路径，如 'wenyuan.models.ReadContent'
    :param serializer_class_path: 序列化器类路径，如 'wenyuan.serializers.ReadContentImportSerializer'
    :param import_field_dict: 导入字段映射 dict
    :param import_serializer_class_path: 用于导入的序列化器类路径
    :param dcid: DownloadCenter 主键
    :param user_info: 当前用户信息 dict，用于序列化器的 request.user 依赖
    """
    instance = DownloadCenter.objects.get(pk=dcid)
    instance.task_status = 1
    instance.description = "开始读取文件..."
    instance.save()

    try:
        # 动态加载模型和序列化器
        module_path, model_name = model_class_path.rsplit('.', 1)
        import importlib
        model_module = importlib.import_module(module_path)
        model_class = getattr(model_module, model_name)

        serial_module_path, serial_name = import_serializer_class_path.rsplit('.', 1)
        serial_module = importlib.import_module(serial_module_path)
        serializer_class = getattr(serial_module, serial_name)

        queryset = model_class.objects.all()
        # 获取多对多字段
        m2m_fields = [
            ele.name for ele in queryset.model._meta.get_fields()
            if hasattr(ele, 'many_to_many') and ele.many_to_many is True
        ]

        # 读 Excel
        instance.description = "解析 Excel 文件..."
        instance.save()
        import_field_dict_with_id = {'id': '更新主键(勿改)', **import_field_dict}
        data = import_to_data(file_url, import_field_dict_with_id, m2m_fields)

        total = len(data)
        success_count = 0
        fail_count = 0
        errors = []

        # 构造一个假的 request 对象，让序列化器用到 request.user 的地方能跑通
        class FakeUser:
            pk = user_info.get('id') if user_info else None
            dept_id = user_info.get('dept_id') if user_info else None

        class FakeRequest:
            user = FakeUser()

        fake_request = FakeRequest()

        instance.description = f"开始处理，共 {total} 条..."
        instance.save()

        # 分批处理，每 2 条更改进度
        BATCH_SIZE = 2
        for idx, ele in enumerate(data, 1):
            try:
                filter_dic = {'id': ele.get('id')}
                inst = filter_dic and queryset.filter(**filter_dic).first()
                serializer = serializer_class(inst, data=ele, request=fake_request)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                success_count += 1
            except Exception as e:
                fail_count += 1
                errors.append(f"第 {idx} 条: {str(e)[:100]}")
                if len(errors) > 20:  # 最多记录 20 条错误
                    break

            # 更改进度
            if idx % BATCH_SIZE == 0 or idx == total:
                instance.description = f"已处理 {idx}/{total} (成功 {success_count}，失败 {fail_count})"
                instance.save()

        # 完成
        instance.task_status = 2
        if fail_count > 0:
            instance.description = (
                f"导入完成：共 {total} 条，成功 {success_count}，失败 {fail_count}。"
                f"错误: {'; '.join(errors[:10])}"
            )[:500]
        else:
            instance.description = f"导入完成：共 {total} 条，全部成功"
        instance.save()

    except Exception as e:
        instance.task_status = 3
        instance.description = f"导入失败: {str(e)[:200]}\n{traceback.format_exc()[:300]}"
        instance.save()
