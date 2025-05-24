<script>
import Time from "../../../common/utils/Time";

export default {
    data() {
        return {
            IS_PAGE                     : true,
            PAGESHOW                    : false,
            item                        : null,
            html                        : '',
            loading                     : false,
            menu                        : [
                {icon:'icon-zhishi2',name:'收藏文档',description:''},
                {type:'line'},
            ],
        };
    },

    watch: {
        '$route.query': {
            handler() {
                this.loadInfo()
                this.PAGESHOW          = true;
            },
            immediate: true, // 如果需要在组件加载时立即触发
        },
    },
    methods: {
        async loadInfo(){
            this.item                   = null;
            let document_id             = this.$route.query.document_id;
            let {data}                  = await this.$request.post("/common/document/info", {
                document_id,
            }).finally(()=>this.loading = false);
            this.item                   = data.document;
            this.html                   = await this.md2html(data.document.text);
        },
    },
};
</script>

<template>
    <div class="c-body c-screen am faster" :class="{show:PAGESHOW}">
        <CHead class="head c-line" :right="[{icon:'icon-back',event:()=>link({path:'/'})}]">
            <div class="c-title">{{item?item.title:''}}</div>
            <div class="c-options">
                <div class="iconfont icon-more icon-menu"></div>
            </div>
        </CHead>
        <div class="c-scoll c-pd c-wd">
            <a-empty v-if="!item && loading" description="数据加载中..." />
            <div class="c-form pr" v-if="item">
                <div class="head">
                    <div class="title">
                        <div>
                            <div class="description">{{item.abstract}}</div>
                        </div>
                    </div>
                    <div class="settings" :class="FORM_LAYOUT" v-if="IS_SYSTEM_ADMIN">
                        <div class="tags  no-select">
                            <template v-for="v,k in item.support">
                                <span class="tag hand" v-if="k">{{k}}</span>
                            </template>
                        </div>
                    </div>
                </div>
                <a-divider class="line" />
                <div class="html" v-html="html" v-highlight></div>
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>

.ant-btn-link {
    padding: 0;
}
.c-body{
    padding-left:18px;
    padding-right:18px;
    height: 100vh;
    .c-form{
        height: calc(100vh - 100px);
        overflow: auto;
    }
}
.head{
    justify-content: space-between;
}
.c-form{
    display: flex;
    flex-direction: column;
    align-items: center;
    min-height: 100%;
    .head{
        width: 100%;
        .title{
            display: flex;
            width: 100%;
            justify-content: space-between;
            .name{
                font-size: 1.2rem;
                line-height: 3rem;
            }
            .description{
                color:#999;
            }
        }
    }
    .html{
        width: 100%;
    }

}
</style>
