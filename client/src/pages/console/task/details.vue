<script>
import Time from "../../../common/utils/Time";

export default {
    data() {
        return {
            IS_PAGE                     : true,
            PAGESHOW                    : false,
            item                        : null,
            loading                     : false,
            menu                        : [
                
            ],
            chats                       : [],
            chatloading                 : false,
            chat_activeKey              : [],
        };
    },

    watch: {
        '$route.query': {
            handler() {
                this.loadInfo();
                this.loadChats();
                this.PAGESHOW          = true;
            },
            immediate: true, // 如果需要在组件加载时立即触发
        },
    },
    methods: {
        async loadInfo(){
            this.loading                = true;
            this.item                   = null;
            let task_id                 = this.$route.query.task_id;
            let {data}                  = await this.$request.post("/client/task/info", {
                task_id,
            }).finally(()=>this.loading = false);
            this.item                   = data.task;
        },
        async loadChats(skip=0){
            this.chatloading            = true;
            let task_id                 = this.$route.query.task_id;
            let {data}                  = await this.$request.post("/client/chat/search", {
                task_id,
                skip,
                size                    : 15,
            }).finally(()=>this.chatloading = false);
            data.list.forEach(c=>{
                c.messages              = [];
                c.loading               = false;
            });
            if(skip==0){
                this.chats              = data.list;
            }else{
                data.list.forEach(c=>this.chats.push(c));
            }
        },
        async loadMessages(keys){
            if(keys.length==0){
                return;
            }
            let i = parseInt(keys[keys.length-1]);
            let chat                    = this.chats[i]
            chat.loading                = true;
            let {data}                  = await this.$request.post("/client/chat/messages", {
                chat_id                 : chat._id,
                organization_id         : chat.organization_id,
                skip                    : 0,
                size                    : 1000,
                sort                    : 'timestamp ASC'
            }).finally(()=>chat.loading = false);
            data.list.forEach(async m=>m.html= await this.md2html(m.content))
            chat.messages               = data.list;
        },
        async toRemove(){
            if(!await this.confirm({title:'确定移除？',content:'删除不可以回复，请确定。'})){
                return;
            }
            await this.$request.post("/client/task/destroy", {
                task_id                 : this.item._id,
            });
            this.link({path:'/console/task'},'replace')
        },
        async toEdit(){
            this.link({path:'/console/task/edit',query:{task_id:this.item._id}})
        },
        async upset(data){
            await this.$request.post("/client/task/upset", Object.assign({
                task_id                 : this.item._id,
            },data));
            Object.assign(this.item,data);
        },
    },
};
</script>

<template>
    <div class="c-body c-screen am faster" :class="{show:PAGESHOW}">
        <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title">任务详情</div>
            <div class="c-options" v-if="IS_SYSTEM_ADMIN">
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
                            <div class="description">{{item.description}}</div>
                        </div>
                        <div class="enabled" v-if="IS_SYSTEM_ADMIN">
                            <a-switch v-model:checked="item.enabled" @change="upset({enabled:item.enabled})" checked-children="已打开" un-checked-children="已关闭" />
                        </div>
                    </div>
                    <div class="settings" :class="FORM_LAYOUT" v-if="IS_SYSTEM_ADMIN">
                        <div class="cron_expr">
                            <span v-if="item.cron_enabled==true">{{crontabFormat(item.cron_expr)}}</span>
                            <span v-if="item.cron_enabled!=true">{{item.schedule_time}}</span>
                        </div>
                        <a-space :size="16">
                            <a-alert class="stotal" :message="item.success+''" type="success" show-icon title="执行成功"/>
                            <a-alert class="stotal" :message="item.failure+''" type="error" show-icon   title="执行失败"/>
                            <a-select v-model:value="item.status" size="small" :options="Object.entries(TASK_STATUS_MAP).map(([value,label])=>{return {value,label}})" @change="upset({status:item.status})"></a-select>
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
                <div class="status_description">{{item.status_description}}</div>
                <div class="chats">
                    <a-collapse v-model:activeKey="chat_activeKey" @change="loadMessages" ghost>
                        <a-collapse-panel class="caht" v-for="(chat,i) in chats" :key="i" :header="chat.created">
                            <div class="messages">
                                <div class="message" v-for="(m,i) in chat.messages" :key="i">
                                    <div class="content user" v-if="m.role=='user'">
                                        <i class="iconfont icon-wenda2 hand" @click="link({path:'/console/chat/room',query:{chat_id:chat._id}})"></i>
                                        {{m.content}}
                                    </div>
                                    <div class="content" v-else v-html="m.html"></div>
                                </div>
                            </div>
                        </a-collapse-panel>
                    </a-collapse>
                </div>

                <ActionSheet ref="as" :list="menu" />
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>

.ant-btn-link {
    padding: 0;
}
.stotal{
    padding: 1px 10px;
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
            .cron_expr{
                
            }
            &.vertical{
                flex-direction: column;
                align-items: flex-start;
            }
        }
    }
    .chats{
        width:100%;
        .messages{
            .message{
                .content{
                    :deep(audio) {
                        display: block;
                        height: 2.5rem;
                    }
                    :deep(img) {
                        display: block;
                        max-height: 200px;
                        max-width: 100%;
                        margin: 0.6rem 0;
                        object-fit: contain;
                        object-position: left;
                    }
                    :deep(video){
                        display: block;
                        max-width: 100%;
                    }
                    &.user{
                        background: #eee;
                        padding: 2px 6px;
                        border-radius: 4px;
                        display: inline-block;
                    }
                }
            }
        }
    }

}
</style>
