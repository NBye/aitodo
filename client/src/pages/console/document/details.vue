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
                {icon:'icon-bianji',name:'编辑文档',description:'',style:{},click:()=>this.toEdit()},
                {type:'line'},
                {icon:'icon-shanchu',name:'删除文档',description:'',style:{color:'#f00'},click:this.toRemove},
            ],
            share_url                   : '',
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
            let {data}                  = await this.$request.post("/client/document/info", {
                document_id,
            }).finally(()=>this.loading = false);
            this.item                   = data.document;
            this.html                   = await this.md2html(data.document.text);
            this.share_url              = `https://${location.hostname}/#/document/particulars?document_id=${data.document._id}`
        },
        async toRemove(){
            if(!await this.confirm({title:'确定移除？',content:'删除不可以回复，请确定。'})){
                return;
            }
            await this.$request.post("/client/document/destroy", {
                document_id                : this.item._id,
            });
            this.$EventBus.emit('document-remove', { document:this.item });
            this.link({path:'/console/document'},'replace')
        },
        async toEdit(){
            this.link({path:'/console/document/edit',query:{document_id:this.item._id}})
        },
        async upset(data){
            await this.$request.post("/client/document/upset", Object.assign({
                document_id               : this.item._id,
            },data));
            Object.assign(this.item,data);
            this.$EventBus.emit('document-update', { document:this.item });
        },
    },
};
</script>

<template>
    <div class="c-body c-screen am faster" :class="{show:PAGESHOW}">
        <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title">文档详情</div>
            <div class="c-options" v-if="IS_SYSTEM_ADMIN">
                <Clipboard class="hand" :text="share_url" @clipboard-success="()=>aMessage().success('已复制到粘贴板')">
                    <div class="iconfont icon-fenxiang"></div>
                </Clipboard>
                <div class="iconfont icon-more icon-menu" @click="$refs.as.trigger()"></div>
            </div>
        </CHead>
        <div class="c-scoll c-pd c-wd">
            <a-empty v-if="!item && loading" description="数据加载中..." />
            <div class="c-form pr" v-if="item">
                <div class="head">
                    <div class="title">
                        <div>
                            <div class="name">{{item.title}}</div>
                            <div class="description">{{item.abstract}}</div>
                        </div>
                        <div class="enabled" v-if="IS_SYSTEM_ADMIN">
                            <a-switch v-model:checked="item.enabled" @change="upset({enabled:item.enabled})" checked-children="已启用" un-checked-children="已禁用" />
                        </div>
                    </div>
                    <div class="settings" :class="FORM_LAYOUT" v-if="IS_SYSTEM_ADMIN">
                        <div class="tags  no-select">
                            <template v-for="v,k in item.support">
                                <span class="tag hand" v-if="k">{{k}}</span>
                            </template>
                        </div>
                        <a-space :size="16">
                            <a-button type="link" @click="toEdit()">
                                编辑<template #icon><EditOutlined /></template>
                            </a-button>
                            <a-button type="link" @click="toRemove()">
                                删除<template #icon><DeleteOutlined /></template>
                            </a-button>
                        </a-space>
                    </div>
                </div>
                <a-divider class="line" />
                <div class="html" v-html="html" v-highlight></div>

                <ActionSheet ref="as" :list="menu" />
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>

.ant-btn-link {
    padding: 0;
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
            .enabled{
                width: 80px;
                text-align: right;
                padding-top: 9px;
                flex-shrink: 0;
            }
        }
        .settings{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 1rem;
            .tags{
                .tag{
                    display: inline-block;
                    background: #ddd;
                    border-radius: 1rem;
                    padding: 0.2rem 1rem;
                    font-size: 0.8rem;
                    margin-right: 0.5rem;
                }
            }
            &.vertical{
                flex-direction: column;
                align-items: flex-start;
            }
        }
    }
    .html{
        width: 100%;
    }

}
</style>
