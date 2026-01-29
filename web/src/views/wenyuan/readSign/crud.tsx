import { CreateCrudOptionsProps, CreateCrudOptionsRet, dict, compute } from '@fast-crud/fast-crud';
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
			actionbar: {
				buttons: {
					add: {
						show: auth('readSign:Create'),
					},
				},
			},
			rowHandle: {
				fixed: 'right',
				width: 200,
				buttons: {
					view: {
						show: true,
					},
					edit: {
						show: auth('readSign:Update'),
					},
					remove: {
						show: auth('readSign:Delete'),
					},
				},
			},
			form: {
				col: { span: 24 },
				labelWidth: '100px',
				wrapper: {
					is: 'el-dialog',
					width: '800px',
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
				read_content_id: {
					title: '读书内容ID',
					search: { show: true },
					column: { show: false },
					form: { show: false },
					component: {
						name: 'el-input',
						placeholder: '请输入读书内容ID',
					},
				},
				read_date: {
					title: '读书日期',
					search: { show: true },
					column: {
						minWidth: 120,
					},
					form: { show: false },
					component: {
						name: 'el-date-picker',
						type: 'daterange',
						placeholder: '请选择日期范围',
						format: 'YYYYMMDD',
						valueFormat: 'YYYYMMDD',
					},
				},
				read_serial_value: {
					title: '读书流水',
					search: { show: false },
					column: {
						minWidth: 200,
						showOverflow: true,
					},
					form: { show: false },
				},
				read_person: {
					title: '读书人员',
					search: { show: true },
					column: {
						minWidth: 120,
					},
					form: {
						rules: [{ required: true, message: '读书人员必填' }],
						component: {
							placeholder: '请输入读书人员',
							type: 'textarea',
							rows: 10,
						},
					},
				},
				rank: {
					title: '排名序号',
					search: { show: false },
					column: {
						width: 100,
					},
					form: {
						rules: [{ required: true, message: '排名序号必填' }],
						component: {
							placeholder: '请输入排名序号',
							type: 'number',
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
