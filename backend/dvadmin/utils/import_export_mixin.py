# -*- coding: utf-8 -*-
import datetime
from urllib.parse import quote

from django.db import transaction
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter, quote_sheetname
from openpyxl.worksheet.table import Table, TableStyleInfo
from rest_framework.decorators import action
from rest_framework.request import Request

from dvadmin.utils.import_export import import_to_data
from dvadmin.utils.json_response import DetailResponse, SuccessResponse
from dvadmin.utils.request_util import get_verbose_name
from dvadmin.system.tasks import async_export_data
from dvadmin.system.models import DownloadCenter


class ImportSerializerMixin:
    """
    自定义导入模板、导入功能
    """

    # 导入字段
    import_field_dict = {}
    # 导入序列化器
    import_serializer_class = None
    # 表格表头最大宽度，默认50个字符
    export_column_width = 50

    def is_number(self,num):
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

    def get_string_len(self, string):
        """
        获取字符串最大长度
        :param string:
        :return:
        """
        length = 4
        if string is None:
            return length
        if self.is_number(string):
            return length
        for char in string:
            length += 2.1 if ord(char) > 256 else 1
        return round(length, 1) if length <= self.export_column_width else self.export_column_width

    @action(methods=['get','post'],detail=False)
    @transaction.atomic  # Django 事务,防止出错
    def import_data(self, request: Request, *args, **kwargs):
        """
        导入模板
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        assert self.import_field_dict, "'%s' 请配置对应的导出模板字段。" % self.__class__.__name__
        # 导出模板
        if request.method == "GET":
            # 示例数据
            queryset = self.filter_queryset(self.get_queryset())
            # 导出excel 表
            response = HttpResponse(content_type="application/msexcel")
            response["Access-Control-Expose-Headers"] = f"Content-Disposition"
            response[
                "Content-Disposition"
            ] = f'attachment;filename={quote(str(f"导入{get_verbose_name(queryset)}模板.xlsx"))}'
            wb = Workbook()
            ws1 = wb.create_sheet("data", 1)
            ws1.sheet_state = "hidden"
            ws = wb.active
            row = get_column_letter(len(self.import_field_dict) + 1)
            column = 10
            header_data = [
                "序号",
            ]
            validation_data_dict = {}
            for index, ele in enumerate(self.import_field_dict.values()):
                if isinstance(ele, dict):
                    header_data.append(ele.get("title"))
                    choices = ele.get("choices", {})
                    if choices.get("data"):
                        data_list = []
                        data_list.extend(choices.get("data").keys())
                        validation_data_dict[ele.get("title")] = data_list
                    elif choices.get("queryset") and choices.get("values_name"):
                        data_list = choices.get("queryset").values_list(choices.get("values_name"), flat=True)
                        validation_data_dict[ele.get("title")] = list(data_list)
                    else:
                        continue
                    column_letter = get_column_letter(len(validation_data_dict))
                    dv = DataValidation(
                        type="list",
                        formula1=f"{quote_sheetname('data')}!${column_letter}$2:${column_letter}${len(validation_data_dict[ele.get('title')]) + 1}",
                        allow_blank=True,
                    )
                    ws.add_data_validation(dv)
                    dv.add(f"{get_column_letter(index + 2)}2:{get_column_letter(index + 2)}1048576")
                else:
                    header_data.append(ele)
            # 添加数据列
            ws1.append(list(validation_data_dict.keys()))
            for index, validation_data in enumerate(validation_data_dict.values()):
                for inx, ele in enumerate(validation_data):
                    ws1[f"{get_column_letter(index + 1)}{inx + 2}"] = ele
            # 插入导出模板正式数据
            df_len_max = [self.get_string_len(ele) for ele in header_data]
            ws.append(header_data)
            # 　更新列宽
            for index, width in enumerate(df_len_max):
                ws.column_dimensions[get_column_letter(index + 1)].width = width
            tab = Table(displayName="Table1", ref=f"A1:{row}{column}")  # 名称管理器
            style = TableStyleInfo(
                name="TableStyleLight11",
                showFirstColumn=True,
                showLastColumn=True,
                showRowStripes=True,
                showColumnStripes=True,
            )
            tab.tableStyleInfo = style
            ws.add_table(tab)
            wb.save(response)
            return response
        else:
            # 从excel中组织对应的数据结构，然后使用序列化器保存
            queryset = self.filter_queryset(self.get_queryset())

            # 异步导入：传 async=true 参数时走后台线程（无需 Celery/Redis）
            use_async = request.query_params.get('async') == 'true' or request.data.get('async') is True
            if use_async:
                import threading
                from dvadmin.utils.import_export import import_to_data
                from dvadmin.system.models import DownloadCenter

                model_class = queryset.model
                serializer_class = self.import_serializer_class

                dc_instance = DownloadCenter.objects.create(
                    creator=request.user,
                    task_name=f'{model_class._meta.verbose_name}数据导入任务',
                    dept_belong_id=request.user.dept_id if request.user else None,
                    description='任务已创建，等待执行...',
                )

                file_url = request.data.get("url")
                import_field_dict = self.import_field_dict
                dc_pk = dc_instance.pk
                user_pk = request.user.pk if request.user else None
                user_dept_id = request.user.dept_id if request.user else None

                def run_import():
                    """后台线程中执行导入，不依赖 Celery"""
                    import threading
                    print(f"[导入线程启动] thread={threading.current_thread().ident}, dc_pk={dc_pk}")
                    try:
                        from dvadmin.system.models import DownloadCenter as _DC
                        instance = _DC.objects.get(pk=dc_pk)
                        print(f"[导入线程] 拿到 DownloadCenter: id={instance.id}, status={instance.task_status}, desc={instance.description}")
                        instance.task_status = 1
                        instance.description = "开始读取文件..."
                        instance.save()
                        print("[导入线程] 写入第一步进度 OK")

                        # 获取多对多字段
                        m2m_fields = [
                            ele.name for ele in queryset.model._meta.get_fields()
                            if hasattr(ele, "many_to_many") and ele.many_to_many is True
                        ]
                        print(f"[导入线程] m2m_fields={m2m_fields}")

                        instance.description = "解析 Excel 文件..."
                        instance.save()

                        import_field_dict_with_id = {'id': '更新主键(勿改)', **import_field_dict}
                        print(f"[导入线程] 开始 import_to_data, file_url={file_url}")
                        data = import_to_data(file_url, import_field_dict_with_id, m2m_fields)
                        print(f"[导入线程] Excel 解析完成, 共 {len(data)} 条")

                        total = len(data)
                        success_count = 0
                        fail_count = 0
                        errors = []

                        # 查真实 User 对象，确保 request.user 属性完整
                        from django.contrib.auth import get_user_model
                        UserModel = get_user_model()
                        try:
                            real_user = UserModel.objects.get(pk=user_pk) if user_pk else None
                            print(f"[导入线程] 查到真实用户: {real_user}")
                        except Exception as e:
                            print(f"[导入线程] 查真实用户失败: {e}")
                            real_user = None

                        class FakeRequest:
                            user = real_user

                        fake_request = FakeRequest()
                        print(f"[导入线程] FakeRequest.user={fake_request.user}")

                        instance.description = f"开始处理，共 {total} 条..."
                        instance.save()

                        # 每 2 条更改进度
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
                                err_msg = f"第 {idx} 条: {str(e)[:200]}"
                                print(f"[导入线程] 失败 {err_msg}")
                                import traceback as _tb2
                                print(_tb2.format_exc()[:300])
                                errors.append(err_msg)
                                if len(errors) > 20:
                                    break

                            if idx % BATCH_SIZE == 0 or idx == total:
                                instance.description = f"已处理 {idx}/{total} (成功 {success_count}，失败 {fail_count})"
                                instance.save()

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
                        import traceback as _tb
                        try:
                            instance = DownloadCenter.objects.get(pk=dc_pk)
                            instance.task_status = 3
                            instance.description = f"导入失败: {str(e)[:200]}\n{_tb.format_exc()[:300]}"
                            instance.save()
                        except Exception:
                            pass

                thread = threading.Thread(target=run_import, daemon=True)
                # 必须等父事务提交后再启动线程，否则线程读不到刚创建的 DownloadCenter
                transaction.on_commit(lambda: thread.start())
                return SuccessResponse(data={'task_id': dc_pk}, msg='导入任务已创建，请查看进度')

            # 同步导入（原有逻辑）
            m2m_fields = [
                ele.name
                for ele in queryset.model._meta.get_fields()
                if hasattr(ele, "many_to_many") and ele.many_to_many == True
            ]
            import_field_dict = {'id':'更新主键(勿改)',**self.import_field_dict}
            data = import_to_data(request.data.get("url"), import_field_dict, m2m_fields)
            for ele in data:
                filter_dic = {'id':ele.get('id')}
                instance = filter_dic and queryset.filter(**filter_dic).first()
                # print(156,ele)
                serializer = self.import_serializer_class(instance, data=ele, request=request)
                serializer.is_valid(raise_exception=True)
                serializer.save()
            return DetailResponse(msg=f"导入成功！")

    @action(methods=['get'],detail=False)
    def update_template(self,request):
        queryset = self.filter_queryset(self.get_queryset())
        assert self.import_field_dict, "'%s' 请配置对应的导入模板字段。" % self.__class__.__name__
        assert self.import_serializer_class, "'%s' 请配置对应的导入序列化器。" % self.__class__.__name__
        data = self.import_serializer_class(queryset, many=True, request=request).data
        # 导出excel 表
        response = HttpResponse(content_type="application/msexcel")
        response["Access-Control-Expose-Headers"] = f"Content-Disposition"
        response["content-disposition"] = f'attachment;filename={quote(str(f"导出{get_verbose_name(queryset)}.xlsx"))}'
        wb = Workbook()
        ws1 = wb.create_sheet("data", 1)
        ws1.sheet_state = "hidden"
        ws = wb.active
        import_field_dict = {}
        header_data = ["序号","更新主键(勿改)"]
        hidden_header = ["#","id"]
        #----设置选项----
        validation_data_dict = {}
        for index, item in enumerate(self.import_field_dict.items()):
            items = list(item)
            key = items[0]
            value = items[1]
            if isinstance(value, dict):
                header_data.append(value.get("title"))
                hidden_header.append(value.get('display'))
                choices = value.get("choices", {})
                if choices.get("data"):
                    data_list = []
                    data_list.extend(choices.get("data").keys())
                    validation_data_dict[value.get("title")] = data_list
                elif choices.get("queryset") and choices.get("values_name"):
                    data_list = choices.get("queryset").values_list(choices.get("values_name"), flat=True)
                    validation_data_dict[value.get("title")] = list(data_list)
                else:
                    continue
                column_letter = get_column_letter(len(validation_data_dict))
                dv = DataValidation(
                    type="list",
                    formula1=f"{quote_sheetname('data')}!${column_letter}$2:${column_letter}${len(validation_data_dict[value.get('title')]) + 1}",
                    allow_blank=True,
                )
                ws.add_data_validation(dv)
                dv.add(f"{get_column_letter(index + 3)}2:{get_column_letter(index + 3)}1048576")
            else:
                header_data.append(value)
                hidden_header.append(key)
        # 添加数据列
        ws1.append(list(validation_data_dict.keys()))
        for index, validation_data in enumerate(validation_data_dict.values()):
            for inx, ele in enumerate(validation_data):
                ws1[f"{get_column_letter(index + 1)}{inx + 2}"] = ele
        #--------
        df_len_max = [self.get_string_len(ele) for ele in header_data]
        row = get_column_letter(len(hidden_header) + 1)
        column = 1
        ws.append(header_data)
        for index, results in enumerate(data):
            results_list = []
            for h_index, h_item in enumerate(hidden_header):
                for key, val in results.items():
                    if key == h_item:
                        if val is None or val == "":
                            results_list.append("")
                        elif isinstance(val,list):
                            results_list.append(str(val))
                        else:
                            results_list.append(val)
                        # 计算最大列宽度
                        if isinstance(val,str):
                            result_column_width = self.get_string_len(val)
                            if h_index != 0 and result_column_width > df_len_max[h_index]:
                                df_len_max[h_index] = result_column_width
            ws.append([index+1,*results_list])
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
        wb.save(response)
        return response


class ExportSerializerMixin:
    """
    自定义导出功能
    """

    # 导出字段
    export_field_label = []
    # 导出序列化器
    export_serializer_class = None
    # 表格表头最大宽度，默认50个字符
    export_column_width = 50

    def is_number(self,num):
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

    def get_string_len(self, string):
        """
        获取字符串最大长度
        :param string:
        :return:
        """
        length = 4
        if string is None:
            return length
        if self.is_number(string):
            return length
        for char in string:
            length += 2.1 if ord(char) > 256 else 1
        return round(length, 1) if length <= self.export_column_width else self.export_column_width

    @action(methods=['get'],detail=False)
    def export_data(self, request: Request, *args, **kwargs):
        """
        导出功能
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        queryset = self.filter_queryset(self.get_queryset())
        assert self.export_field_label, "'%s' 请配置对应的导出模板字段。" % self.__class__.__name__
        assert self.export_serializer_class, "'%s' 请配置对应的导出序列化器。" % self.__class__.__name__
        data = self.export_serializer_class(queryset, many=True, request=request).data
        try:
            async_export_data.delay(
                data,
                str(f"导出{get_verbose_name(queryset)}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"),
                DownloadCenter.objects.create(creator=request.user, task_name=f'{get_verbose_name(queryset)}数据导出任务', dept_belong_id=request.user.dept_id).pk,
                self.export_field_label
            )
            return SuccessResponse(msg="导入任务已创建，请前往‘下载中心’等待下载")
        except:
            pass
        # 导出excel 表
        response = HttpResponse(content_type="application/msexcel")
        response["Access-Control-Expose-Headers"] = f"Content-Disposition"
        response["content-disposition"] = f'attachment;filename={quote(str(f"导出{get_verbose_name(queryset)}.xlsx"))}'
        wb = Workbook()
        ws = wb.active
        header_data = ["序号", *self.export_field_label.values()]
        hidden_header = ["#", *self.export_field_label.keys()]
        df_len_max = [self.get_string_len(ele) for ele in header_data]
        row = get_column_letter(len(self.export_field_label) + 1)
        column = 1
        ws.append(header_data)
        for index, results in enumerate(data):
            results_list = []
            for h_index, h_item in enumerate(hidden_header):
                for key,val in results.items():
                    if key == h_item:
                        if val is None or val=="":
                            results_list.append("")
                        else:
                            results_list.append(val)
                        # 计算最大列宽度
                        result_column_width = self.get_string_len(val)
                        if h_index !=0 and result_column_width > df_len_max[h_index]:
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
        wb.save(response)
        return response
