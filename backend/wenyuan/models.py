from django.db import models
from dvadmin.utils.models import CoreModel
import uuid


class ReadContent(CoreModel):
    """
    读书内容表
    """
    read_date = models.CharField(max_length=8, verbose_name="读书日期", help_text="读书日期")
    read_content = models.CharField(max_length=5000, verbose_name="读书内容", help_text="读书内容")
    read_serial = models.CharField(max_length=50, unique=True, verbose_name="读书流水", help_text="读书流水", default=uuid.uuid4, editable=False)
    sign_list = models.CharField(max_length=5000, null=False, blank=False, default='', verbose_name="签到列表", help_text="签到列表")




    class Meta:
        db_table = "read_content"
        verbose_name = '读书内容表'
        verbose_name_plural = verbose_name
        ordering = ('-create_datetime',)


class ReadSign(CoreModel):
    """
    读书签到表
    """
    read_content = models.ForeignKey(
        to='ReadContent',
        on_delete=models.CASCADE,
        verbose_name="读书内容ID",
        help_text="读书内容ID",
        db_constraint=False
    )
    read_date = models.CharField(max_length=8, verbose_name="读书日期", help_text="读书日期")
    read_person = models.CharField(max_length=50, verbose_name="读书人员", help_text="读书人员")
    rank = models.IntegerField(verbose_name="排名序号", help_text="排名序号")

    class Meta:
        db_table = "read_sign"
        verbose_name = '读书签到表'
        verbose_name_plural = verbose_name
        ordering = ('-read_content', '-rank')
