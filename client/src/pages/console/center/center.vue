<script>
export default {
    data() {
        const self = this;
        return {
            IS_PAGE                     : true,
            list                        : [],
            storage                     : {count:0,limit:0,size:0},
            search_ing                  : false,
            query                       : {
                keyword                 : '',
            },
        };
    },
    async unmounted(){
    },
    async mounted() {
        let list                        = [
            {name:'我的主页',path:'/console/center/home',icon:'icon-photo'},
            {name:'当前组织',path:'/console/center/organization',icon:'icon-qiye',query:{organization_id:this.organization._id}},
            {name:'修改密码',path:'/console/center/update',icon:'icon-mima',query:{user_id:this.user._id,tab:'account'}},
        ]
        if(this.organization.user_id == this.user._id){
            list.push({name:'密钥管理',path:'/console/center/secret',icon:'icon-miyao'});
            list.push({name:'组织设置',path:'/console/center/settings',icon:'icon-setting-gear'});
        }
        list.forEach(item=>{
            item.active                 = item.path == this.$route.path;
        });
        this.list                       = list;
    },
    methods: {
        async selectItem(item){
            this.link({path:item.path,query:item.query || {}},/center$/.test(this.$route.path)?'push':'replace')
        },
        async search(){},
    },
};
</script>

<template>
    <div class="c-list c-screen">
        <CHead :right="[{icon:(organization && organization.avatar)?organization.avatar:'icon-menu',event:'navbar-show'}]">
            <a-input-search v-model:value="query.keyword" placeholder="搜索" @search="search(0)"> </a-input-search>
        </CHead>
        <CList class="c-scoll" avatar="true" :list="list" name="name" description="description" @checked="selectItem" :go="true">
            <template #avatar="{item}">
                <i class="iconfont" :class="item.icon" />
            </template>
        </CList>
        <div class="tac">
            <a-button type="link" @click="logout">退出登录</a-button>
        </div>
    </div>
    <router-view></router-view>
</template>

<style lang="scss" scoped></style>
