<template>
	<fs-page>
		<fs-crud ref="crudRef" v-bind="crudBinding">
			<template #actionbar>
				<el-button type="primary" @click="handleBatchAdd" v-auth="'readSign:Create'">批量添加签到</el-button>
			</template>
		</fs-crud>
	</fs-page>

	<el-dialog v-model="batchDialogVisible" title="批量添加签到人员" width="900px" :close-on-click-modal="false">
		<el-form :model="batchForm" label-width="120px">
			<el-form-item label="读书日期" required>
				<el-select v-model="batchForm.read_serial_id" placeholder="请选择读书日期" style="width: 100%">
					<el-option v-for="item in readContentList" :key="item.id" :label="`${item.read_date} (${item.read_serial})`" :value="item.id" />
				</el-select>
			</el-form-item>
			<el-form-item label="签到人员">
				<el-input v-model="batchForm.read_person" type="textarea" :rows="20" placeholder="请输入签到人员，格式如：1.杨艳2.刘艾英3.杨熙英..." />
				<div style="margin-top: 10px; color: #909399; font-size: 12px;">
					提示：签到人员格式为"序号.姓名"，多个人员用数字序号连接，如：1.杨艳2.刘艾英3.杨熙英...
				</div>
			</el-form-item>
		</el-form>
		<template #footer>
			<el-button @click="batchDialogVisible = false">取消</el-button>
			<el-button type="primary" @click="handleBatchSubmit" :loading="batchSubmitting">确定</el-button>
		</template>
	</el-dialog>
</template>

<script lang="ts" setup name="readSign">
import { defineAsyncComponent, onMounted, ref } from 'vue';
import { useFs } from '@fast-crud/fast-crud';
import { createCrudOptions } from './crud';
import * as api from './api';
import { ElMessage } from 'element-plus';
import { useRoute } from 'vue-router';

const { crudBinding, crudRef, crudExpose } = useFs({ createCrudOptions, context: {} });
const route = useRoute();

const batchDialogVisible = ref(false);
const batchSubmitting = ref(false);
const readContentList = ref<any[]>([]);
const batchForm = ref({
	read_serial_id: null as number | null,
	read_person: ''
});

onMounted(async () => {
	await loadReadContentList();
	
	const readContentId = route.query.read_content_id as string;
	if (readContentId && crudBinding.value.search) {
		crudBinding.value.search.form.read_content_id = readContentId;
	}
	
	crudExpose.doRefresh();
});

const loadReadContentList = async () => {
	try {
		const res = await api.GetReadContentList({ limit: 999 });
		readContentList.value = res.data;
	} catch (error) {
		ElMessage.error('加载读书内容列表失败');
	}
};

const handleBatchAdd = () => {
	batchForm.value = {
		read_serial_id: null,
		read_person: ''
	};
	batchDialogVisible.value = true;
};

const parseReadPerson = (text: string) => {
	const persons = [];
	const pattern = /(\d+)\.([^0-9]+)/g;
	let match;

	while ((match = pattern.exec(text)) !== null) {
		persons.push({
			rank: parseInt(match[1]),
			read_person: match[2].trim()
		});
	}

	return persons;
};

const handleBatchSubmit = async () => {
	if (!batchForm.value.read_serial_id) {
		ElMessage.warning('请选择读书流水');
		return;
	}

	if (!batchForm.value.read_person) {
		ElMessage.warning('请输入签到人员');
		return;
	}

	const persons = parseReadPerson(batchForm.value.read_person);

	if (persons.length === 0) {
		ElMessage.warning('签到人员格式不正确，请检查格式');
		return;
	}

	batchSubmitting.value = true;

	try {
		for (const person of persons) {
			await api.AddObj({
				read_serial: batchForm.value.read_serial_id,
				read_person: person.read_person,
				rank: person.rank
			});
		}

		ElMessage.success(`成功添加 ${persons.length} 条签到记录`);
		batchDialogVisible.value = false;
		crudExpose.doRefresh();
	} catch (error) {
		ElMessage.error('添加签到记录失败');
	} finally {
		batchSubmitting.value = false;
	}
};
</script>
