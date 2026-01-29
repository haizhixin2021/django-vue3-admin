<template>
	<fs-page>
		<fs-crud ref="crudRef" v-bind="crudBinding">
			<template #actionbar-right>
				<importExcel api="api/wenyuan/read_content/" v-auth="'readContent:Import'">导入</importExcel>
			</template>
		</fs-crud>
		<signPersonnel ref="subSignPersonnelRef"></signPersonnel>
	</fs-page>
</template>

<script lang="ts" setup name="readContent">
import { defineAsyncComponent, onMounted, ref } from 'vue';
import { useFs } from '@fast-crud/fast-crud';
import { createCrudOptions } from './crud';
import importExcel from '/@/components/importExcel/index.vue';

const signPersonnel = defineAsyncComponent(() => import('./signPersonnel/index.vue'));
const subSignPersonnelRef = ref();

const { crudBinding, crudRef, crudExpose } = useFs({ createCrudOptions, context: { subSignPersonnelRef } });

onMounted(() => {
	crudExpose.doRefresh();
});
</script>
