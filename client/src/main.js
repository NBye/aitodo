import { createApp } from 'vue'

import App from './App.vue'
import View from "./common/View";
import router from './common/router'

import request from "./common/utils/request";
import EventBus from "./common/utils/EventBus";

import "./common/scss/global.scss"
import "./common/scss/am.scss"
import "./common/scss/adapter.scss"
import "./common/scss/extend.scss"


import { ConfigProvider } from 'ant-design-vue';
import Antd from 'ant-design-vue';
import 'ant-design-vue/dist/reset.css';

// import io from "socket.io-client";
// import vuesax, { SxPluginSocketIO } from 'vue-socket.io-extended';
// const socket = io('http://123.57.30.84:6030'); // 你的服务器地址
// socket.on('connect', function () {
//     console.log('Connected to the server');
// });


import Prism from 'prismjs'
import 'prismjs/themes/prism.css'
import 'prismjs/components/prism-python'
import 'prismjs/components/prism-java'
import 'prismjs/components/prism-markdown'
import 'prismjs/components/prism-bash'
import 'prismjs/components/prism-json'
import 'prismjs/components/prism-mermaid'

const app = createApp(App)
app.directive('highlight', {
    mounted(el) {
        const blocks = el.querySelectorAll('code')
        blocks.forEach((block) => {
            Prism.highlightElement(block)
        })
    },
    updated(el) {
        const blocks = el.querySelectorAll('code')
        blocks.forEach((block) => {
            Prism.highlightElement(block)
        })
    }
})

app.mixin(View)
app.use(Antd)
app.use(router)
app.use(request)
app.use(EventBus)
// app.use(vuesax, {
//     sockets: [new SxPluginSocketIO(socket)]
// })
app.mount('#app')

