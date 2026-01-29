<template>
	<el-drawer size="70%" v-model="drawer" direction="rtl" destroy-on-close :before-close="handleClose">
		<fs-crud ref="crudRef" v-bind="crudBinding"> </fs-crud>
	</el-drawer>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue';
import { useFs } from '@fast-crud/fast-crud';
import { createCrudOptions } from './crud';
import { useExpose, useCrud } from '@fast-crud/fast-crud';
import { ElMessageBox } from 'element-plus';

const drawer = ref(false);

const handleClose = (done: () => void) => {
	ElMessageBox.confirm('您确定要关闭?', {
		confirmButtonText: '确定',
		cancelButtonText: '取消',
		type: 'warning',
	})
		.then(() => {
			done();
		})
		.catch(() => {
		});
};

const { crudBinding, crudRef, crudExpose } = useFs({ createCrudOptions, context: {} });
const { setSearchFormData, doRefresh } = crudExpose;

const openDrawer = (readContentId: number) => {
	setSearchFormData({ form: { read_content_id: readContentId } });
	drawer.value = true;
	doRefresh();
};

defineExpose({ drawer, setSearchFormData, doRefresh, openDrawer });

onMounted(() => {
	crudExpose.doRefresh();
});
</script>
