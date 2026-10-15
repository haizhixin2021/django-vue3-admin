import { request } from '/@/utils/service';
import { UserPageQuery, AddReq, DelReq, EditReq, InfoReq } from '@fast-crud/fast-crud';

export const apiPrefix = '/api/wenyuan/read_sign/';

export function GetList(query: UserPageQuery) {
	return request({
		url: apiPrefix,
		method: 'get',
		params: query,
	});
}

export function GetReadContentList(query: UserPageQuery) {
	return request({
		url: '/api/wenyuan/read_content/',
		method: 'get',
		params: query,
	});
}

export function GetObj(id: InfoReq) {
	return request({
		url: apiPrefix + id,
		method: 'get',
	});
}

export function AddObj(obj: AddReq) {
	return request({
		url: apiPrefix,
		method: 'post',
		data: obj,
	});
}

export function UpdateObj(obj: EditReq) {
	return request({
		url: apiPrefix + obj.id + '/',
		method: 'put',
		data: obj,
	});
}

export function DelObj(id: DelReq) {
	return request({
		url: apiPrefix + id + '/',
		method: 'delete',
		data: { id },
	});
}

export function GetStatistics(params: { start_date?: string; end_date?: string }) {
	return request({
		url: apiPrefix + 'statistics/',
		method: 'get',
		params,
	});
}

export function ExportStatistics(params: { start_date?: string; end_date?: string }) {
	return request({
		url: apiPrefix + 'export_statistics/',
		method: 'get',
		params,
		responseType: 'blob',
	});
}
