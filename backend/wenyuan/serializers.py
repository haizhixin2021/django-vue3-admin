from rest_framework import serializers
from dvadmin.utils.serializers import CustomModelSerializer
from wenyuan.models import ReadContent, ReadSign


class ReadContentSerializer(CustomModelSerializer):
    """
    读书内容-序列化器
    """
    class Meta:
        model = ReadContent
        fields = "__all__"
        read_only_fields = ["id", "read_serial"]


class ReadContentCreateSerializer(CustomModelSerializer):
    """
    读书内容-创建序列化器
    """
    sign_list = serializers.CharField(required=False, allow_blank=True, write_only=True, help_text='签到列表')

    class Meta:
        model = ReadContent
        fields = "__all__"
        read_only_fields = ["id", "read_serial"]

    def validate(self, attrs):
        read_date = attrs.get('read_date')
        instance = self.instance

        if read_date:
            queryset = ReadContent.objects.filter(read_date=read_date)
            
            if instance and instance.pk:
                queryset = queryset.exclude(pk=instance.pk)

            existing_records = list(queryset.values('id', 'read_date'))
            
            if existing_records:
                print(f"DEBUG: 查询到重复记录: {existing_records}")
                raise serializers.ValidationError({
                    'read_date': f'日期 {read_date} 的读书内容已存在（ID: {[r["id"] for r in existing_records]}），请勿重复添加'
                })
            else:
                print(f"DEBUG: 未查询到重复记录，日期: {read_date}")

        return attrs

    def create(self, validated_data):
        sign_list = validated_data.pop('sign_list', '')
        instance = super().create(validated_data)
        if sign_list:
            instance.sign_list = sign_list
            instance.save()
        return instance

    def update(self, instance, validated_data):
        print(f"DEBUG: ReadContentCreateSerializer.update 被调用")
        print(f"DEBUG: validated_data = {validated_data}")
        print(f"DEBUG: instance = {instance}, instance.sign_list = {instance.sign_list if instance else 'None'}")
        
        sign_list = validated_data.pop('sign_list', None)
        print(f"DEBUG: sign_list = {sign_list}, type = {type(sign_list)}")
        
        try:
            instance = super().update(instance, validated_data)
            print(f"DEBUG: 更新后的 instance.sign_list = {instance.sign_list}")
        except Exception as e:
            print(f"DEBUG: super().update() 失败: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        if sign_list is not None:
            print(f"DEBUG: 更新 sign_list 字段为: {sign_list}")
            instance.sign_list = sign_list
            instance.save()
            print(f"DEBUG: 保存后的 instance.sign_list = {instance.sign_list}")
        else:
            print(f"DEBUG: sign_list 为 None，不更新 sign_list 字段")
        
        return instance


class ReadContentImportSerializer(CustomModelSerializer):
    """
    读书内容-导入序列化器
    """
    sign_list = serializers.CharField(required=False, allow_blank=True, help_text='签到列表')

    class Meta:
        model = ReadContent
        fields = "__all__"
        read_only_fields = ["id", "read_serial"]

    def validate(self, attrs):
        read_date = attrs.get('read_date')
        instance = self.instance

        if read_date:
            queryset = ReadContent.objects.filter(read_date=read_date)
            
            if instance and instance.pk:
                queryset = queryset.exclude(pk=instance.pk)

            existing_records = list(queryset.values('id', 'read_date'))
            
            if existing_records:
                raise serializers.ValidationError({
                    'read_date': f'日期 {read_date} 的读书内容已存在（ID: {[r["id"] for r in existing_records]}），请勿重复添加'
                })

        return attrs

    def _delete_and_recreate_sign_records(self, read_content_id, sign_list):
        """
        删除旧的签到记录并重新创建
        格式：1.杨艳2.武卫岗3.谢锋辉4.赵艳香5.
        支持格式：1.杨艳2.刘艾英3李普4.王润兰5. 或 1.杨艳2.刘艾英3、李普4.王润兰5.
        """
        print(f"DEBUG: 删除读书内容ID {read_content_id} 的所有签到记录")
        ReadSign.objects.filter(read_content_id=read_content_id).delete()

        self._parse_and_create_sign_records(read_content_id, sign_list)

    def _parse_and_create_sign_records(self, read_content_id, sign_list):
        """
        解析签到人员文本并创建签到记录
        格式：1.杨艳2.武卫岗3.谢锋辉4.赵艳香5.
        支持格式：1.杨艳2.刘艾英3李普4.王润兰5. 或 1.杨艳2.刘艾英3、李普4.王润兰5.
        """
        print(f"DEBUG: 原始签到列表文本: {sign_list}")

        if not sign_list:
            return

        # 统一分隔符：如果包含中文顿号，替换为英文句号
        if '、' in sign_list:
            sign_list = sign_list.replace('、', '.')
            print(f"DEBUG: 替换中文顿号后的文本: {sign_list}")

        # 处理数字后面直接跟汉字的情况（没有分隔符），在数字和汉字之间插入句号
        # 匹配模式：数字后面直接跟汉字（不是句号）
        import re as regex_module
        sign_list = regex_module.sub(r'(\d)([\u4e00-\u9fa5])', r'\1.\2', sign_list)
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

    def create(self, validated_data):
        sign_list = validated_data.pop('sign_list', '')
        instance = super().create(validated_data)
        if sign_list:
            instance.sign_list = sign_list
            instance.save()
            self._parse_and_create_sign_records(instance.id, sign_list)
        return instance

    def update(self, instance, validated_data):
        sign_list = validated_data.pop('sign_list', None)
        
        try:
            instance = super().update(instance, validated_data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise
        
        if sign_list is not None:
            instance.sign_list = sign_list
            instance.save()
            self._delete_and_recreate_sign_records(instance.id, sign_list)
        
        return instance


class ReadSignSerializer(CustomModelSerializer):
    """
    读书签到-序列化器
    """
    read_content_name = serializers.CharField(source='read_content.read_content', read_only=True)
    read_serial_value = serializers.CharField(source='read_content.read_serial', read_only=True)
    read_date = serializers.CharField(read_only=True)

    class Meta:
        model = ReadSign
        fields = "__all__"
        read_only_fields = ["id"]


class ReadSignCreateSerializer(CustomModelSerializer):
    """
    读书签到-创建序列化器
    """
    class Meta:
        model = ReadSign
        fields = "__all__"
        read_only_fields = ["id"]
