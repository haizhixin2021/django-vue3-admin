import { CreateCrudOptionsProps, CreateCrudOptionsRet, dict, compute } from '@fast-crud/fast-crud';
import { nextTick } from 'vue';
import * as api from './api';
import { dictionary } from '/@/utils/dictionary';
import { successMessage } from '/@/utils/message';
import { auth } from '/@/utils/authFunction';

export const createCrudOptions = function ({ crudExpose, context }: CreateCrudOptionsProps): CreateCrudOptionsRet {
	const pageRequest = async (query: any) => {
		return await api.GetList(query);
	};
	const editRequest = async ({ form, row }: any) => {
		form.id = row.id;
		return await api.UpdateObj(form);
	};
	const delRequest = async ({ row }: any) => {
		return await api.DelObj(row.id);
	};
	const addRequest = async ({ form }: any) => {
		return await api.AddObj(form);
	};

	const signPersonnelShow = compute(({ form }: any) => {
		return form.mode !== 'view';
	});

	return {
		crudOptions: {
			request: {
				pageRequest,
				addRequest,
				editRequest,
				delRequest,
			},
			pagination: {
				show: true,
			},
			search: {
				show: true,
				col: { span: 6 },
			},
			actionbar: {
				buttons: {
					add: {
						show: auth('readContent:Create'),
					},
				},
			},
			rowHandle: {
				fixed: 'right',
				width: 280,
				buttons: {
					view: {
						show: true,
						text: '查看',
						type: 'text',
						iconRight: 'View',
					},
					edit: {
						show: auth('readContent:Update'),
						text: '编辑',
						type: 'text',
						iconRight: 'Edit',
					},
					remove: {
						show: auth('readContent:Delete'),
						text: '删除',
						type: 'text',
						iconRight: 'Delete',
					},
					viewSignPersonnel: {
						text: '签到人员',
						type: 'text',
						iconRight: 'User',
						click: (ctx: any) => {
							const { row } = ctx;
							context!.subSignPersonnelRef.value.drawer = true;
							nextTick(() => {
								context!.subSignPersonnelRef.value.setSearchFormData({ form: { read_content_id: row.id } });
								context!.subSignPersonnelRef.value.doRefresh();
							});
						},
						show: true,
					},
				},
			},
			form: {
				col: { span: 24 },
				labelWidth: '100px',
				wrapper: {
					is: 'el-dialog',
					width: '600px',
				},
			},
			columns: {
				_index: {
					title: '序号',
					form: { show: false },
					column: {
						type: 'index',
						align: 'center',
						width: '70px',
						columnSetDisabled: true,
					},
				},
				id: {
					title: 'ID',
					column: { show: false },
					search: { show: false },
					form: { show: false },
				},
				read_date: {
					title: '读书日期',
					search: {
						show: true,
						component: {
							name: 'el-date-picker',
							type: 'daterange',
							placeholder: '请选择日期范围',
							format: 'YYYYMMDD',
							valueFormat: 'YYYYMMDD',
						},
					},
					column: {
						minWidth: 120,
						sortable: 'custom',
					},
					form: {
						rules: [{ required: true, message: '读书日期必填' }],
						component: {
							name: 'el-date-picker',
							type: 'date',
							placeholder: '请选择读书日期',
							format: 'YYYYMMDD',
							valueFormat: 'YYYYMMDD',
						},
					},
				},
				read_content: {
					title: '读书内容',
					search: { show: false },
					column: {
						minWidth: 300,
						showOverflow: true,
					},
					form: {
						rules: [{ required: true, message: '读书内容必填' }],
						component: {
							placeholder: '请输入读书内容',
							type: 'textarea',
							rows: 5,
						},
					},
				},
				sign_list: {
					title: '签到列表',
					search: { show: false },
					column: { show: false },
					form: {
						show: signPersonnelShow,
						component: {
							placeholder: '请输入签到人员，格式：1.张三2.李四3.王五4.赵六5.',
							type: 'textarea',
							rows: 10,
						},
					},
				},
				create_datetime: {
					title: '创建时间',
					column: {
						minWidth: 160,
						sortable: 'custom',
					},
					form: { show: false },
					search: { show: false },
				},
			},
		},
	};
};
