import { createRouter, createWebHistory, createWebHashHistory } from 'vue-router'

const router = createRouter({
    history: createWebHashHistory(),
    routes: [
        {
            path: '/',
            // component: index,
            redirect: '/console/chat',
        },
        {
            name: 'login',
            path: '/login',
            component: () => import('../pages/login.vue'),
            meta: { title: '登录' }
        },
        {
            path: '/reception',
            component: () => import(`../pages/console/chat/reception.vue`),
            meta: { title: '客服' },
        },
        {
            path: '/document/particulars',
            component: () => import(`../pages/console/document/particulars.vue`),
            meta: { title: '客服' },
        },
        {
            path: '/console',
            redirect: '/console/chat',
            component: () => import('../pages/console/console.vue'),
            meta: { title: 'Ai·ToDo 控制台' },
            children: [
                {
                    path: 'file',
                    component: () => import(`../pages/console/file/file.vue`),
                    meta: { title: '文件管理' },
                    children: [
                        {
                            path: 'search',
                            component: () => import(`../pages/console/file/search.vue`),
                            meta: { title: '文件搜索' },
                        },
                    ]
                },
                {
                    path: 'database',
                    component: () => import(`../pages/console/database/database.vue`),
                    meta: { title: '数据管理' },
                    children: [
                        {
                            path: 'search',
                            component: () => import(`../pages/console/database/search.vue`),
                            meta: { title: '数据搜索' },
                        },
                    ]
                },
                {
                    path: 'knowledge',
                    component: () => import(`../pages/console/knowledge/knowledge.vue`),
                    meta: { title: '知识管理' },
                    children: [
                        {
                            path: 'search',
                            component: () => import(`../pages/console/knowledge/search.vue`),
                            meta: { title: '知识搜索' },
                        },
                        {
                            path: 'publish',
                            component: () => import(`../pages/console/knowledge/publish.vue`),
                            meta: { title: '知识创建' },
                        },
                    ]
                },
                {
                    path: 'organization',
                    component: () => import(`../pages/console/organization/organization.vue`),
                    meta: { title: '组织管理' },
                    children: [
                        {
                            path: 'create',
                            component: () => import(`../pages/console/organization/create.vue`),
                            meta: { title: '组织创建' },
                        },
                        {
                            path: 'details',
                            component: () => import(`../pages/console/organization/details.vue`),
                            meta: { title: '组织详情' },
                        },
                        {
                            path: 'edit',
                            component: () => import(`../pages/console/organization/edit.vue`),
                            meta: { title: '组织编辑' },
                        },
                        {
                            path: 'secret',
                            component: () => import(`../pages/console/organization/secret.vue`),
                            meta: { title: 'API密钥管理' },
                        },
                        {
                            path: 'settings',
                            component: () => import(`../pages/console/organization/settings.vue`),
                            meta: { title: '组织设置' },
                        },
                    ]
                },
                {
                    path: 'personnel',
                    component: () => import(`../pages/console/personnel/personnel.vue`),
                    meta: { title: '组织成员管理' },
                    children: [
                        {
                            path: 'recruit',
                            component: () => import(`../pages/console/personnel/recruit.vue`),
                            meta: { title: '招聘AI员工' },
                        },
                        {
                            path: 'resume',
                            component: () => import(`../pages/console/personnel/resume.vue`),
                            meta: { title: '简历' },
                        },
                        {
                            path: 'create',
                            component: () => import(`../pages/console/personnel/create.vue`),
                            meta: { title: '创建AI员工' },
                        },
                        {
                            path: 'details',
                            component: () => import(`../pages/console/personnel/details.vue`),
                            meta: { title: '组织成员详情' },
                        },
                        {
                            path: 'edit',
                            component: () => import(`../pages/console/personnel/edit.vue`),
                            meta: { title: '组织成员编辑' },
                        },
                    ]
                },
                {
                    path: 'action',
                    component: () => import(`../pages/console/action/action.vue`),
                    meta: { title: '赋能管理' },
                    children: [
                        {
                            path: 'create',
                            component: () => import(`../pages/console/action/create.vue`),
                            meta: { title: '创建能力' },
                        },
                        {
                            path: 'details',
                            component: () => import(`../pages/console/action/details.vue`),
                            meta: { title: '能力配置' },
                        },
                        {
                            path: 'edit',
                            component: () => import(`../pages/console/action/edit.vue`),
                            meta: { title: '编辑配置' },
                        }
                    ]
                },
                {
                    path: 'chat',
                    component: () => import(`../pages/console/chat/chat.vue`),
                    meta: { title: '会话管理' },
                    children: [
                        {
                            path: 'room',
                            component: () => import(`../pages/console/chat/room.vue`),
                            meta: { title: '聊天室' },
                        },
                        {
                            path: 'details',
                            component: () => import(`../pages/console/chat/details.vue`),
                            meta: { title: '会话详情' },
                        },
                    ]
                },
                {
                    path: 'task',
                    component: () => import(`../pages/console/task/task.vue`),
                    meta: { title: '任务管理' },
                    children: [
                        {
                            path: 'create',
                            component: () => import(`../pages/console/task/create.vue`),
                            meta: { title: '任务创建' },
                        },
                        {
                            path: 'details',
                            component: () => import(`../pages/console/task/details.vue`),
                            meta: { title: '任务详情' },
                        },
                        {
                            path: 'edit',
                            component: () => import(`../pages/console/task/edit.vue`),
                            meta: { title: '编辑任务' },
                        },
                    ]
                },
                {
                    path: 'document',
                    component: () => import(`../pages/console/document/document.vue`),
                    meta: { title: '帮助文档' },
                    children: [
                        {
                            path: 'create',
                            component: () => import(`../pages/console/document/create.vue`),
                            meta: { title: '新建文档' },
                        },
                        {
                            path: 'edit',
                            component: () => import(`../pages/console/document/edit.vue`),
                            meta: { title: '编辑文档' },
                        },
                        {
                            path: 'details',
                            component: () => import(`../pages/console/document/details.vue`),
                            meta: { title: '文档详情' },
                        },
                    ]
                },
                {
                    path: 'center',
                    component: () => import(`../pages/console/center/center.vue`),
                    meta: { title: '个人中心' },
                    children: [
                        {
                            path: 'home',
                            component: () => import(`../pages/console/center/home.vue`),
                            meta: { title: '我的' },
                        },
                        {
                            path: 'update',
                            component: () => import(`../pages/console/personnel/edit.vue`),
                            meta: { title: '我的' },
                        },
                        {
                            path: 'organization',
                            component: () => import(`../pages/console/organization/details.vue`),
                            meta: { title: '我的' },
                        },
                        {
                            path: 'edit',
                            component: () => import(`../pages/console/organization/edit.vue`),
                            meta: { title: '组织编辑' },
                        },
                        {
                            path: 'secret',
                            component: () => import(`../pages/console/organization/secret.vue`),
                            meta: { title: 'API密钥管理' },
                        },
                        {
                            path: 'settings',
                            component: () => import(`../pages/console/organization/settings.vue`),
                            meta: { title: '组织设置' },
                        },
                    ]
                },
                ...['calendar'].map((path) => ({
                    path,
                    component: () => import(`../pages/console/${path}/${path}.vue`),
                }))
            ]
        }
    ],

});
router.beforeEach((to, from, next) => {
    // 更新页面标题
    if (to.meta.title) {
        document.title = to.meta.title;
    } else {
        document.title = '网音·AiToDo';
    }
    next();
});
export default router;