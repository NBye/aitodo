<script>
import theme from "./common/theme";
import locale from 'ant-design-vue/es/date-picker/locale/zh_CN';

import "./common/iconfont/iconfont"
// import "./common/safe"

if (process.env.NODE_ENV!=='development'){
    document.addEventListener('contextmenu', function(event) {
        event.preventDefault();
    });
    document.addEventListener('keydown', function(event) {
        if (event.key === 'F12' || (event.ctrlKey && event.shiftKey && event.key === 'I')) {
            event.preventDefault();
        }
    });
}

export default {
    components: {},
    data() {
        return {
            locale,
            theme
        };
    },
    async beforeMount(){
        const root = document.documentElement;
        Object.entries(theme.token).forEach(([k,v])=>{
            // console.log(`--ant-${k.replace(/([a-z])([A-Z])/g, '$1-$2').toLowerCase()}`,v)
            root.style.setProperty(`--ant-${k.replace(/([a-z])([A-Z])/g, '$1-$2').toLowerCase()}`, v);
        });
        root.addEventListener('click',(e)=>{
            if(e.target.tagName=='ROUTE'){
                this.link({path:e.target.getAttribute('link')})
            }
        })
    },
    async mounted() {

    },
    methods: {
    },
};
</script>

<template>
    <a-config-provider :theme="theme" :locale="locale">
        <router-view></router-view>
    </a-config-provider>
</template>

<style lang="scss" scoped></style>

<style>
@import "./common/iconfont/iconfont.css";

/*每个页面公共css */
@import "vditor/dist/index.css";
</style>
