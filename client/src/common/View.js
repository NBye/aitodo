
import storage from "./utils/storage";
import global from "./utils/global"
import Time from "./utils/Time";
import IDate from "./utils/IDate";
import Vditor from "vditor";
import router from "./router";
import { HOST } from "./utils/request";

import { v4 as uuid4 } from 'uuid';

import { createVNode } from 'vue';
import { Modal, message as Message } from 'ant-design-vue';
import {
	ExclamationCircleOutlined, SolutionOutlined, SearchOutlined,
	PlusOutlined, MessageOutlined, DownOutlined, MergeCellsOutlined,
	CloudUploadOutlined, UserDeleteOutlined, DeleteOutlined,
	EditOutlined, EnterOutlined, SelectOutlined, UsergroupAddOutlined,
	VerticalAlignBottomOutlined, MoreOutlined, UserAddOutlined,
	KeyOutlined, ShareAltOutlined, ExpandOutlined, InfoCircleOutlined,
	AudioOutlined, LoadingOutlined,
} from '@ant-design/icons-vue';
import { h as H } from 'vue';

import CoverImage from "../components/CoverImage.vue";
import Empty from "../components/Empty.vue";
import CFile from "../components/CFile.vue";
import ActionSheet from "../components/ActionSheet.vue";
import ActionMerge from "../components/ActionMerge.vue";

import CList from "../components/CList.vue";
import CHead from "../components/CHead.vue";
import Markdown from "../components/Markdown.vue";

import AgentForm from "../components/AgentForm.vue";
import Agent from "../components/Agent.vue";
import AgentFormPropertie from "../components/AgentFormPropertie.vue";
import AgentFormProperties from "../components/AgentFormProperties.vue";

import ModalSearchUser from "../components/ModalSearchUser.vue";
import Clipboard from "../components/Clipboard.vue";
import McpGrid from "../components/McpGrid.vue";

import html2canvas from "html2canvas";

import MarkdownIt from 'markdown-it'
import mermaid from 'mermaid';
import markdownItMermaidPlus from 'markdown-it-mermaid-plus';


const md = new MarkdownIt({
	html: true,        // 允许HTML标签
	linkify: true,     // 自动转换URL为链接
	typographer: true  // 启用一些语言中立的替换和引号美化
});

// 自定义 mermaid 渲染插件
// md.use(markdownItMermaidPlus);
md.use((md) => {
	const defaultHtmlBlock = md.renderer.rules.html_block
	md.renderer.rules.html_block = function (tokens, idx, options, env, self) {
		// console.log(tokens[idx])
		let { info, content } = tokens[idx];
		if (content.startsWith('<think') && content.endsWith('/think>')) {

		}
		return defaultHtmlBlock(tokens, idx, options, env, self);
	};
	const defaultFence = md.renderer.rules.fence;
	md.renderer.rules.fence = (tokens, idx, options, env, self) => {
		// console.log(tokens[idx])
		let { info, content } = tokens[idx];
		if (info.trim() === '') {
			return md.render(content);
		} else if (info.trim() === 'html') {
			// return md.render(content);
		} else if (['svg', 'xml'].indexOf(info.trim()) > -1) {
			return md.render(content);
		} else if (info.trim() === 'mermaid') {
			let id = `mermaid-${uuid4()}`;
			let html = `<div ><pre id="${id}" style="width:70%;" class="language-mermaid" tabindex="0"><code class="language-mermaid">${content}</code></pre></div>`;
			setTimeout(async () => {
				let dom = document.getElementById(id);
				// content = dom.innerText;
				let id2 = 'd' + (id.replaceAll('-', ''));
				try {
					let { svg } = await mermaid.render(id2, content.trim())
					dom.innerHTML = svg;
				} catch (e) {
					let edom = document.getElementById(id2);
					edom && edom.remove();
				}
			}, 400);
			return html;
		}
		return defaultFence(tokens, idx, options, env, self);
	};
});
export default {
	components: {
		CoverImage, Empty, CFile, ActionSheet, ActionMerge,
		CList, CHead, Markdown, ModalSearchUser, McpGrid,
		Clipboard,

		Agent, AgentForm, AgentFormPropertie, AgentFormProperties,

		PlusOutlined, MessageOutlined, DeleteOutlined, DownOutlined, UsergroupAddOutlined,
		CloudUploadOutlined, UserDeleteOutlined, SolutionOutlined, MoreOutlined,
		EditOutlined, EnterOutlined, SelectOutlined, VerticalAlignBottomOutlined,
		UserAddOutlined, KeyOutlined, ShareAltOutlined, ExpandOutlined, InfoCircleOutlined,
		SearchOutlined, MergeCellsOutlined, AudioOutlined, LoadingOutlined,
	},
	beforeMount() {
		window.addEventListener('resize', () => {
			this.IS_MOBILE = this.isMobile();
			this.FORM_LAYOUT = this.IS_MOBILE ? 'vertical' : 'horizontal';
		});
	},
	// computed: {
	// 	isMobile() {
	// 		return window.innerWidth <= 768;
	// 	}
	// },
	data() {
		let IS_MOBILE = this.isMobile();
		return {
			IS_MOBILE,
			col: [5, 0],
			FORM_LAYOUT: IS_MOBILE ? 'vertical' : 'horizontal',
			TASK_STATUS_MAP:{
				pending					: '等待中',
				running					: '执行中',
				completed				: '完成',
				failed					: '失败'
			},
			AGENT_TYPE_MAP: {
				'knowledge': '知识',
				'request': '接口',
				'generate': '引导',
				'modelcall': '模型',
				'mcp': 'MCP',
			},
			SALARY_UNIT: { y: '年', m: '月', d: '天', h: '小时', },
			PAYMENT_STATUS: {
				paying: '待支付', fail: '交易失败', success: '交易成功'
			},
			COMMISSION_BILL_STATUS: {
				unsettled: '待结算', settled: '已结算',
			},
			MODEL_LIST: global.MODEL_LIST || storage('MODEL_LIST'),
			IS_SYSTEM_ADMIN: global.IS_SYSTEM_ADMIN || storage('IS_SYSTEM_ADMIN'),
			user: global.USER || storage('USER'),
			organization: global.ORGANIZATION || storage('ORGANIZATION'),
			constant: global,
		}
	},
	async mounted() {
		if (!this.IS_PAGE) {
			return
		}
		// console.log(this.$route.path)
		if (this.user == null && /^\/console/.test(this.$route.path) && this.$route.name != 'login') {
			this.link({ name: 'login' });
		}
	},
	methods: {
		isMobile() {
			return window.innerWidth <= 768;
		},
		isAdmin() {
			return this.user._id == this.organization.user_id;
		},
		isOffline(item) {
			if (item.role == 'assistant' && item.join_info) {
				if (!item.join_info.expired) {
					return false;
				}
				return IDate.format('yyyy-mm-dd hh:ii:ss') > item.join_info.expired;
			}
			return false;
		},
		link(data, mode = 'push') {
			router[mode](data);
		},
		async linkBack(n = -1) {
			this.PAGESHOW = false;
			// await Time.delay(0.3);
			router.go(n)
		},
		async refishCache() {
			await this.refishMyInfo()
			this.refishModels()
			this.refishTemplates()

		},
		async refishModels() {
			if (this.organization) {
				let { data } = await this.$request.post("/client/organization/models", {});
				this.MODEL_LIST = global.MODEL_LIST = data.models;
				storage('MODEL_LIST', data.models);
			} else {
				this.MODEL_LIST = []
				storage('MODEL_LIST', []);
			}
		},
		async refishTemplates() {
			let { data } = await this.$request.post("/common/constant/templates", {})
			this.constant.templates = data
		},
		async refishMyInfo() {
			let { data } = await this.$request.post("/client/user/info", {});
			this.user = global.USER = data.user;
			storage('USER', data.user);

			this.organization = global.ORGANIZATION = data.organization;
			storage('ORGANIZATION', data.organization);

			this.IS_SYSTEM_ADMIN = global.IS_SYSTEM_ADMIN = data.is_system_admin;
			storage('IS_SYSTEM_ADMIN', this.IS_SYSTEM_ADMIN);
		},
		modelsFilter(support) {
			if (typeof support == 'string') {
				support = RegExp('^' + support + '$')
			}
			let platforms = []
			this.MODEL_LIST.forEach((platform) => {
				let models = []
				platform.children.forEach(m => {
					for (let s of m.support) {
						if (support.test(s)) {
							models.push({ ...m })
							break;
						}
					}
				});
				if (models.length) {
					platforms.push({
						value: platform.value,
						label: platform.label,
						children: models,
					});
				}
			});
			return platforms;
		},
		async logout() {
			if (!await this.confirm({ title: '退出登录?' })) {
				return false;
			}
			await this.$request.post("/client/user/logout", {}).finally(() => {
				storage('user', null)
				storage('token', null)
				storage('organization', null)
			});
		},
		async chatCreate(...user_ids) {
			if (this._chatCreateing) {
				return false;
			}
			this._chatCreateing = true;
			Message.info('正在发起会话...');
			let { data } = await this.$request.post("/client/chat/create", { user_ids });
			await Time.delay(1);
			this.link({ path: '/console/chat/room', query: { chat_id: data.chat._id } })
			this._chatCreateing = false;
		},
		isEmpty(obj) {
			if (obj instanceof Array) {
				return obj.length;
			} else {
				return Object.keys(obj).length === 0;
			}
		},
		fileIsImage(file) {
			return ['png', 'jpg', 'jpeg', 'gif'].indexOf(file.type) > -1
		},
		windowOpen({ url, width = 350, height = 700 }) {
			if (/^\//.test(url)) {
				url = '/#' + url;
			}
			let screenWidth = window.screen.width;
			let screenHeight = window.screen.height;
			let left = (screenWidth - width) / 2;
			let top = (screenHeight - height) / 2;
			window.open(url, '', `width=${width},height=${height},top=${top},left=${left}`);
		},
		async fileDetails(item) {
			let { data } = await this.$request.post("/client/file/info", {
				file_id: item._id,
			});
			let { file, user, organization } = data;
			let h = this.aH();
			let icon = null;
			if (this.typeIsImage(item.type)) {
				icon = h('img', { src: this.cutImgUrl(file.url, { w: 40 }), style: { width: '40px', 'margin-top': '1rem' } });
			} else {
				icon = h('div', { class: 'iconfont icon-other icon-' + item.type, style: { width: '40px', fontSize: '42px', display: 'flex', justifyContent: 'center' } });
			}
			this.aModal().info({
				okText: '确定',
				title: '文件详情',
				content: h('div', { style: { display: 'flex', 'width': '100%', 'margin-left': '-30px' } }, [
					h('div', {}, [
						icon
					]),
					h('div', { style: { padding: '0.5rem' } }, [
						h('p', '文 件 ID ：' + file._id),
						h('p', '文件名称：' + file.name),
						h('p', '所属组织：' + (organization ? organization.name : '无')),
						h('p', '所属用户：' + (user ? ((user.join_info && user.join_info.aliasname) ? user.join_info.aliasname : user.nickname) : '未知')),
						h('p', '文件大小：' + this.byteFormat(file.size)),
						h('p', '上传时间：' + file.created),
					]),
				]),
			});
		},
		async md2html(markdown, callback = null) {
			markdown = markdown.replace(/<think>([\s\S]*?)<\/think>/g, (match, content) => {
				return `<div class="think"><div>${content}</div></div>`;
			});
			let html = md.render(markdown);
			html = html.replace(/<a /g, '<a target="_blank" ');
			callback && callback(html);
			return html;
			// markdown = markdown.replace(/<route link="(.*)">([\s\S]*?)<\/route>/g, (match, href, content) => {
			// 	return `<a href="#${href}">${content}</a>`;
			// });
			// let html = await Vditor.md2html(markdown, {
			// 	mode: "markdown",
			// 	cdn: '/static/vditor',
			// 	customRender: {
			// 		'mermaid': (str) => {
			// 			console.log('--------------------')
			// 			console.log(str)
			// 			// const h = await mermaid.render('mermaidGraph', str.replace(/```mermaid|```/g, '').trim());
			// 			// return h.svg
			// 		},
			// 	},
			// });
		},
		async listRadioChecked(list, each) {
			list.forEach((item) => each(item))
		},
		async listRemoveItem(list, item, i = null) {
			if (i === null) {
				i = list.indexOf(item)
			}
			list.splice(i, 1);
		},
		async confirm({ title = null, content = null, icon = null, okText = '确定', cancelText = '取消' }) {
			let data = {}, node = H('div', { class: 'c-confirm' }, []);
			if (content instanceof Array) {
				content.forEach(({ type = 'input', inputType = '', name, value, placeholder, style, maxlength = 1000, children, label, reg, onInput = Function() }) => {
					let item = H('div', { class: 'c-item' }, []);
					if (label) {
						item.children.push(H('div', { class: 'c-label' }, label));
					}
					data[name] = value;
					let attrs = {
						name, value: data[name], maxlength: maxlength,
						style: Object.assign({ width: '100%', borderWidth: '2px', borderStyle: 'inset', borderRadius: '6px' }, style),
						placeholder, onInput: (event) => {
							if (event.target.type == 'datetime-local') {
								let [date, time] = event.target.value.split('T');
								data[name] = `${date} ${time}${time.length < 8 ? ':00' : ''}`;
							} else {
								data[name] = event.target.value;
							}
							onInput(data);
						}
					}
					if (/^input:/.test(type)) {
						[type, inputType] = type.split(':');
					}
					if (type == 'input' && inputType) {
						attrs['type'] = inputType;
					}
					item.children.push(H('div', { class: 'c-input' }, H(type, attrs)));
					node.children.push(item);
				})
				content = node;
			}
			return new Promise((resolve, reject) => {
				Modal.confirm({
					title,
					content,
					icon: icon || createVNode(ExclamationCircleOutlined),
					onOk: () => {
						if (node.children.length) {
							resolve(data)
						} else {
							resolve(true)
						}
					},
					onCancel: () => resolve(false),
					okText,
					cancelText,
				});
			});
		},
		aModal() {
			return Modal;
		},
		aMessage() {
			return Message;
		},
		aH() {
			return H;
		},
		cutImgUrl(url, opt = {}) {
			let { w = 0, h = 0, mode = 1, alt = '' } = opt || {}
			if (/^data:/.test(url)) {
				return url;
			} else if (/^\/upload/.test(url)) {
				return `${HOST}${url}?w=${w * 2}&h=${h * 2}&m=${mode}`;
			} else if (/^\/static/.test(url)) {
				return `${HOST}${url}`;
			} else if (/^icon-/.test(url)) {
				return null;
			} else if (url) {
				return `${url}?w=${w}&h=${h}&m=${mode}`;
			} else if (alt) {
				let canvas = document.createElement('canvas');
				let ctx = canvas.getContext('2d');
				canvas.width = 200;
				canvas.height = 200;
				ctx.fillStyle = '#ffffff'; // 背景颜色
				ctx.fillRect(0, 0, canvas.width, canvas.height);
				ctx.font = '81px Arial';
				ctx.fillStyle = '#1677ff'; // 文字颜色
				ctx.textAlign = 'center';
				ctx.textBaseline = 'middle';
				ctx.fillText(alt.substring(0, 2), canvas.width / 2, canvas.height / 2);
				return canvas.toDataURL('image/png');
			} else {
				return `/img.svg`;
			}
		},
		typeIsImage(type) {
			if (type[0] == '.') {
				type = type.substring(1);
			}
			return ['png', 'jpg', 'jpeg', 'jpg'].indexOf(type) > -1
		},
		// Format
		byteFormat(byte) {
			const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
			for (let i = 0; i < units.length; i++) {
				if (Math.floor(byte / Math.pow(1024, i + 1)) === 0) {
					if (i === 0) {
						return `${byte.toFixed(1)}${units[i]}`;
					} else {
						return `${(byte / Math.pow(1024, i)).toFixed(1)}${units[i]}`;
					}
				}
			}
			return '∞';
		},
		genderFormat(gender) {
			return { 'xx': '女', 'xy': '男' }[gender] || '未知'
		},
		roleFormat(gender) {
			return { 'user': '用户', 'assistant': 'AI' }[gender] || '未知'
		},
		salaryFormat({ type, price }) {
			let unit = { 'y': '年', 'm': '月', 'd': '日', 'h': '小时' }[type];
			let mony = (price * 1).toFixed(2)
			return `￥${mony}/${unit}`
		},
		expiredFormat(time) {
			const now = new Date();
			const inputTime = new Date(time.replace(/-/g, '/'));
			const diff = inputTime - now; // 时间差，单位毫秒

			const seconds = Math.floor(diff / 1000); // 转换为秒
			const minutes = Math.floor(seconds / 60); // 转换为分钟
			const hours = Math.floor(minutes / 60); // 转换为小时
			const days = Math.floor(hours / 24); // 转换为天数
			const month = Math.floor(days / 31); // 月份
			const year = Math.floor(days / 365); // 年份
			if (year > 0) {
				return `${year}年`;
			} if (month > 0) {
				return `${month}月`;
			} if (days > 0) {
				return `${days}天`;
			} if (hours > 0) {
				return `${hours}小时`;
			} if (minutes > 0) {
				return `${minutes}分钟`;
			} if (seconds > 0) {
				return `${seconds}秒`;
			} else {
				return '已过期';
			}
		},
		agoFormat(time) {
			const now = new Date();
			const inputTime = new Date(time.replace(/-/g, '/'));
			const diff = now - inputTime; // 时间差，单位毫秒

			const seconds = Math.floor(diff / 1000); // 转换为秒
			const minutes = Math.floor(seconds / 60); // 转换为分钟
			const hours = Math.floor(minutes / 60); // 转换为小时
			const days = Math.floor(hours / 24); // 转换为天数

			if (seconds < 60) {
				return '刚刚';
			} else if (minutes < 60) {
				return `${minutes}分钟前`;
			} else if (hours < 24) {
				return `${hours}小时前`;
			} else if (days < 30) {
				return `${days}天前`;
			} else {
				return inputTime.toISOString().split('T')[0]; // 返回日期字符串（yyyy-mm-dd）
			}
		},
		timeFormat(time, format = 'yyyy-mm-dd hh:ii:ss') {
			return IDate.format(format, time)
		},
		currentTime() {
			return IDate.format('yyyy-mm-dd hh:ii:ss')
		},
		crontabFormat(cronExpr) {
			const [minute, hour, day, month, week] = cronExpr.trim().split(/\s+/);
			const convertField = (field, name, min, max, unit) => {
				if (field === '*') return `每${unit}`;
				if (/^\d+$/.test(field)) return `在第${field}${unit}`;
				if (/^\d+-\d+$/.test(field)) {
					const [start, end] = field.split('-');
					return `从第${start}到第${end}${unit}`;
				}
				if (/^\*\/\d+$/.test(field)) return `每隔${field.slice(2)}${unit}`;
				return `${name}字段较复杂: ${field}`;
			};
			return [
				convertField(minute, '分钟', 0, 59, '分钟'),
				convertField(hour, '小时', 0, 23, '小时'),
				convertField(day, '日', 1, 31, '天'),
				convertField(month, '月份', 1, 12, '月'),
				convertField(week, '星期', 0, 7, '星期')  // 0和7都表示星期天
			].join('，');
		},
	}
}