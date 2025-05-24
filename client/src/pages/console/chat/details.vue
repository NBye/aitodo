<script>
export default {
    data() {
        return {
            IS_PAGE                     : true,
            PAGESHOW                    : false,
            loading                     : false,
            menu                        : [
                {icon:'icon-bianji'    ,name:'编辑信息',description:'',style:{},click:()=>this.toEdit()},
                {type:'line'},
                {icon:'icon-tichu',name:'移除成员',description:'',style:{color:'#f00'},click:this.toRemove},
            ],
        };
    },
    async mounted() {
    },
    watch: {
        '$route.query': {
            handler(newQuery, oldQuery) {
                this.loadInfo()
                this.PAGESHOW          = true;
            },
            immediate: true, // 如果需要在组件加载时立即触发
        },
    },
    methods: {
        async loadInfo(){

        },
    },
};
</script>

<template>
    <div class="c-body c-screen am faster" :class="{show:PAGESHOW}">
        <!-- <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title">成员详情</div>
            <div class="c-options">
                <div class="iconfont icon-more icon-menu" @click="$refs.as.trigger()"></div>
            </div>
        </CHead>
        <div class="c-scoll c-pd c-wd">
            <a-empty v-if="!item && loading" description="数据加载中..." />
            <div class="c-form pr" v-if="item">
                <ActionSheet ref="as" :list="menu" />
            </div>
        </div> -->
    </div>
</template>

<style lang="scss" scoped>

.ant-btn-link {
    padding: 0;
}
.c-form{
    display: flex;
    flex-direction: column;
}
</style>
