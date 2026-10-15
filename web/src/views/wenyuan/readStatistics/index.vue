<template>
	<fs-page>
		<div class="stat-container">
			<div class="stat-search">
				<el-form :inline="true" :model="searchForm" @submit.prevent="handleQuery">
					<el-form-item label="日期范围">
						<el-date-picker
							v-model="searchForm.dateRange"
							type="daterange"
							range-separator="至"
							start-placeholder="起始日期"
							end-placeholder="终止日期"
							value-format="YYYYMMDD"
						/>
					</el-form-item>
					<el-form-item>
						<el-button type="primary" @click="handleQuery">查询</el-button>
						<el-button @click="handleReset">重置</el-button>
						<el-button type="success" @click="handleExport" :loading="exporting">
							<el-icon style="margin-right: 4px;"><Download /></el-icon>
							导出 Excel
						</el-button>
					</el-form-item>
				</el-form>
			</div>

			<div class="stat-summary" v-if="totalCount > 0">
				<span>共 <b>{{ statsData.length }}</b> 人参与读书，累计 <b>{{ totalCount }}</b> 人次</span>
			</div>

			<el-table :data="statsData" v-loading="loading" border stripe style="width: 100%">
				<el-table-column type="index" label="排名" width="80" align="center">
					<template #default="{ $index }">
						<span v-if="$index === 0" class="rank rank-1">🥇</span>
						<span v-else-if="$index === 1" class="rank rank-2">🥈</span>
						<span v-else-if="$index === 2" class="rank rank-3">🥉</span>
						<span v-else>{{ $index + 1 }}</span>
					</template>
				</el-table-column>
				<el-table-column prop="read_person" label="姓名" min-width="150" />
				<el-table-column prop="count" label="读书次数" width="150" align="center">
					<template #default="{ row }">
						<span class="count-badge">{{ row.count }}</span>
					</template>
				</el-table-column>
			</el-table>

			<el-empty v-if="!loading && statsData.length === 0" description="暂无数据" />
		</div>
	</fs-page>
</template>

<script lang="ts" setup name="readStatistics">
import { ref, computed, onMounted } from 'vue';
import * as api from '../readSign/api';
import { ElMessage } from 'element-plus';
import { Download } from '@element-plus/icons-vue';

const loading = ref(false);
const exporting = ref(false);
const currentYear = new Date().getFullYear();
const searchForm = ref({
	dateRange: [`${currentYear}0101`, `${currentYear}1231`] as string[],
});
const statsData = ref<{ read_person: string; count: number }[]>([]);

const totalCount = computed(() => {
	return statsData.value.reduce((sum, item) => sum + item.count, 0);
});

const getQueryParams = () => {
	const params: { start_date?: string; end_date?: string } = {};
	if (searchForm.value.dateRange && searchForm.value.dateRange.length === 2) {
		params.start_date = searchForm.value.dateRange[0];
		params.end_date = searchForm.value.dateRange[1];
	}
	return params;
};

const handleQuery = async () => {
	loading.value = true;
	try {
		const res = await api.GetStatistics(getQueryParams());
		statsData.value = res.data || [];
	} catch (error) {
		ElMessage.error('获取统计数据失败');
	} finally {
		loading.value = false;
	}
};

const handleReset = () => {
	searchForm.value.dateRange = [];
	handleQuery();
};

const handleExport = async () => {
	exporting.value = true;
	try {
		const res = await api.ExportStatistics(getQueryParams());
		// 从 Content-Disposition 提取文件名
		const disposition = res.headers?.['content-disposition'] || res.headers?.['Content-Disposition'] || '';
		let filename = '读书统计.xlsx';
		const match = disposition.match(/filename\*?=(?:UTF-8'')?([^;]+)/i);
		if (match) {
			filename = decodeURIComponent(match[1].replace(/["']/g, '').trim());
		}

		const blob = new Blob([res.data], {
			type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
		});
		const url = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = url;
		link.download = filename;
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		URL.revokeObjectURL(url);
		ElMessage.success('导出成功');
	} catch (error) {
		ElMessage.error('导出失败');
	} finally {
		exporting.value = false;
	}
};

onMounted(() => {
	handleQuery();
});
</script>

<style scoped>
.stat-container {
	padding: 16px;
}
.stat-search {
	margin-bottom: 16px;
}
.stat-summary {
	margin-bottom: 12px;
	color: #606266;
	font-size: 14px;
}
.stat-summary b {
	color: #409eff;
	font-size: 16px;
}
.rank {
	font-weight: bold;
}
.count-badge {
	display: inline-block;
	padding: 2px 12px;
	background: #ecf5ff;
	color: #409eff;
	border-radius: 10px;
	font-weight: bold;
}
</style>
