import storage from './storage';
import { EventBus } from './EventBus';
import { Modal, message as Message } from 'ant-design-vue';

let host;
if (process.env.NODE_ENV === 'development') {
	host = 'http://localhost:6100';
} else {
	host = 'http://localhost:6100';
}

const domain = host.split('.').slice(-2).join('.');

import router from "../router";
export const HOST = host;

export class MError extends Error {
	constructor(code, message, data = {}) {
		super(message);
		this.code = code;
		this.data = data;
	}
	static from(code, message, data = {}) {
		return new MError(code, message, data);
	}
}

const interaction = function (message) {
	let match, regex = /(.*)<route\s+link="([^"]+)">([^<]+)<\/route>/g, find = false;
	while ((match = regex.exec(message)) !== null) {
		find = true;
		const content = match[1].trim();
		const link = match[2].trim();
		const okText = match[3].trim();
		Modal.confirm({
			title: '温馨提示',
			content,
			onOk: () => {
				location.hash = link
			},
			okText,
			cancelText: '取消',
		});
	}
	return find
}

const ERROR_BUFFER = { list: [], runing: false }
const tipMessageError = function (message) {
	if (interaction(message)) {
		return;
	}
	if (ERROR_BUFFER.list.indexOf(message) < 0) {
		ERROR_BUFFER.list.push(message)
	}
	if (ERROR_BUFFER.runing) {
		clearTimeout(ERROR_BUFFER.runing)
	}
	ERROR_BUFFER.runing = setTimeout(() => {
		Message.warn(ERROR_BUFFER.list.join('\n'));
		ERROR_BUFFER.list = [];
	}, 500)
}

const SUCCESS_BUFFER = { list: [], runing: false }
const tipMessageSuccess = function (message) {
	if (interaction(message)) {
		return;
	}
	if (SUCCESS_BUFFER.list.indexOf(message) < 0) {
		SUCCESS_BUFFER.list.push(message)
	}
	if (SUCCESS_BUFFER.runing) {
		clearTimeout(SUCCESS_BUFFER.runing)
	}
	SUCCESS_BUFFER.runing = setTimeout(() => {
		Message.success(SUCCESS_BUFFER.list.join('\n'));
		SUCCESS_BUFFER.list = [];
	}, 500)
}

/**
 * POST 请求
 * @param {String} url 
 * @param {Object} data 
 * @param {Object} options 
 */
export async function post(url, data = {}, options = {
	ERROR_TIPS_ENABLE: true,
	SUCCESS_TIPS_ENABLE: true,
	headers: {},
}) {
	let headers = {
		'content-type': 'application/json',
		'token': storage('token') || '',
	};
	Object.entries(options.headers || {}).forEach(([k, v]) => headers[k.toLowerCase()] = v);
	let body = null;
	for (let [k, v] of Object.entries(data)) {
		if (v instanceof File) {
			headers['content-type'] = 'multipart/form-data';
			break;
		}
	}
	if (/json/.test(headers['content-type'])) {
		body = JSON.stringify(data);
	} else if (/form-data/.test(headers['content-type'])) {
		body = new FormData();
		Object.entries(data).forEach(([k, v]) => {
			body.append(k, v);
		});
		delete headers['content-type'];
	} else {
		body = JSON.stringify(data);
	}
	let controller = new AbortController();
	return fetch(host + url, {
		method: 'POST',
		headers,
		body,
		credentials: 'same-origin',
		signal: controller.signal,
	}).then(async response => {
		if (!response.ok) {
			throw new MError(500, `HTTP error! status: ${response.status}`);
		}
		const reader = response.body.getReader();
		const decoder = new TextDecoder("utf-8");
		let result = "", text = '', i = 0;
		while (true) {
			const { done, value } = await reader.read();
			if (done) {
				break;
			}
			// console.log(i++,decoder.decode(value))
			decoder.decode(value).split("\n").forEach((line) => {
				text += line;
				result += line;
				try {
					let data = JSON.parse(result);
					result = "";
					typeof options.onStream == "function" && options.onStream(data, controller);
				} catch (e) {
					// console.log(e)
				}
			});
		}
		let response_headers = {}
		for (const [key, value] of response.headers.entries()) {
			response_headers[key.toLowerCase()] = value;
		}
		if (/json/.test(response_headers['content-type'])) {
			let { code, message, data } = JSON.parse(text);
			if (code == 1) {
				if (options.SUCCESS_TIPS_ENABLE !== false && message) {
					tipMessageSuccess(message)
				}
				if (headers.token) {
					document.cookie = `token=${headers.token}; Domain=${domain}; Max-Age=2592000; Path=/`;
				}
				return { code, data, message }
			}
			if (options.ERROR_TIPS_ENABLE !== false) {
				tipMessageError(message)
			}
			if (code == 401) {
				router.push({ path: '/login' });
			} else if (code == 405) {
				EventBus.emit('organization-forbid', {});
			}
			throw new MError(code, message, data);
		} else {
			return text;
		}
	});
}

export default {
	install(app) {
		// 注册全局方法
		app.config.globalProperties.$request = {
			post,
			host,
			domain,
		}
		// 注册全局组件（可选）
		app.component('MyComponent', {
			template: '<div>Hello from MyComponent!</div>'
		});
	},
};