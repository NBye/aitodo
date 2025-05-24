<script>
import Time from "../../../common/utils/Time";

export default {
    data() {
        return {
            V                           : 0,
            IS_PAGE                     : true,
            PAGESHOW                    : false,
            item                        : null,
            loading                     : false,
            menu                        : [
                {icon:'icon-bianji',name:'编辑信息',description:'',style:{},click:()=>this.toEdit()},
                {type:'line'},
                {icon:'icon-shanchu',name:'删除能力',description:'',style:{color:'#f00'},click:this.toRemove},
            ],
        };
    },

    async unmounted() {
        this.$EventBus.off('agent-resave',this.agent_save);


    },
    async mounted() {
        this.$EventBus.on('agent-resave',this.agent_save);
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
        async agent_save(){
            let {data}                  = await this.$request.post("/client/action/saveAgent", {
                action_id               : this.item._id,
                agent_list              : this.item.agent_list,
            });
            this.item.agent_list        = data.action.agent_list;
        },
        async loadInfo(){
            this.item                   = null;
            let action_id               = this.$route.query.action_id;
            let {data}                  = await this.$request.post("/client/action/info", {
                action_id,
            }).finally(()=>this.loading = false);
            this.item                   = data.action;
            if(this.item.agent_list.length==0 && ['','custom'].indexOf(this.item.type)>-1){
                await Time.delay(0.001);
                this.addAgent();
            }
        },
        async toRemove(){
            if(!await this.confirm({title:'确定移除？',content:'删除不可以回复，请确定。'})){
                return;
            }
            await this.$request.post("/client/action/destroy", {
                action_id                : this.item._id,
            });
            this.$EventBus.emit('organization-action-remove', { action:this.item });
            this.link({path:'/console/action',query:{user_id:this.item.user_id}},'replace')
        },
        async toEdit(){
            this.link({path:'/console/action/edit',query:{action_id:this.item._id,user_id:this.item.user_id}})
        },
        async upset(data){
            await this.$request.post("/client/action/upset", Object.assign({
                action_id               : this.item._id,
            },data));
            Object.assign(this.item,data);
            this.$EventBus.emit('organization-action-update', { action:this.item });
        },
        async addAgent(){
            this.$refs.ag.addAgent('添加Agent')
        },
        async merge({action}){
            if(this.item._id==action._id){
                this.item.agent_list    = action.agent_list;
            }
        }
    },
};
</script>

<template>
    <div class="c-body c-screen am faster" :class="{show:PAGESHOW}">
        <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title">能力配置</div>
            <div class="c-options">
                <div class="iconfont icon-more icon-menu" @click="$refs.as.trigger()"></div>
            </div>
        </CHead>
        <div class="c-scoll c-pd c-wd">
            <a-empty v-if="!item && loading" description="数据加载中..." />
            <div class="c-form pr" v-if="item">
                <div class="head">
                    <div class="title">
                        <div>
                            <div class="name">{{item.name}}</div>
                            <div class="description">{{item.description}}</div>
                        </div>
                        <div class="enabled">
                            <a-switch v-model:checked="item.enabled" @change="upset({enabled:item.enabled})" checked-children="已启用" un-checked-children="已禁用" />
                        </div>
                    </div>
                    <div class="settings" :class="FORM_LAYOUT">
                        <div class="tags  no-select">
                            <template v-for="v,k in item.support">
                                <span class="tag hand" v-if="k">{{k}}</span>
                            </template>
                        </div>
                        <a-space :size="16">
                            <a-button type="link" v-if="['','custom'].indexOf(this.item.type)>-1" @click="addAgent()">
                                Agent<template #icon><PlusOutlined /></template>
                            </a-button>
                            <a-button type="link" v-if="['','custom'].indexOf(this.item.type)>-1" @click="$refs.am.show({action_id:item._id},merge)">
                                Merge<template #icon><MergeCellsOutlined /></template>
                            </a-button>
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
                <a-empty v-if="item.agent_list.length==0" description="您还未配置Agent，点击配置。" @click="addAgent()" />
                <!-- <template v-for="(agent,i) in item.agent_list">
                    <Agent ref="ag" :agent="agent" :agent_list="item.agent_list"></Agent>
                </template> -->
                <Agent ref="ag" :agent="{root:true,children:item.agent_list}"></Agent>
                <ActionMerge ref="am" />
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

}
</style>
