<script>
import Time from '../../../common/utils/Time';
import storage from "../../../common/utils/storage";
import RoomInput from "../../../components/room/input2.vue";

export default {
	components: {
        RoomInput,
    },
    data() {
        return {
            IS_PAGE                     : true,
            query                       : {
                chat_id                 : '',
                size                    : 50,
                sort                    : 'timestamp desc',
                timestamp_lt            : 0,
            },
            assistant                   : {},
            user                        : {},
            chat                        : null,
            user_map                    : {},

            list                        : [],
            listMap                     : {},
            searching                   : false,

            //消息详情
            messageState                : false,
            messageStep                 : 0,
            message                     : null,

            reception_url               : '',
            reception_url_open          : false,
        };
    },
    watch: {
        '$route.query': {
            async handler() {
                let organization_assistant_id = this.$route.query.organization_assistant_id;
                let key                 = `reception_${organization_assistant_id}`
                let rs                  = await this.$request.post("/common/reception/chat", {
                    organization_assistant_id,
                    chat_id             : storage(key),
                }).finally(()=>this.searching = false );
                Object.assign(this,rs.data);
                storage(key,this.chat._id)
                this.query.chat_id      = this.chat._id;
                console.log(rs)
                this.user_map           = {
                    [this.assistant._id]: this.assistant,
                    [this.user._id]     : this.user,
                }
                this.messageState       = false;
                this.messageStep        = 0;
                this.message            = null;

                this.reception_url      = location.href;

                this.loadMessage(0);
            },
            immediate                   : true,
        },
    },
    methods: {
        get_parameters(){
            let organization_assistant_id   = this.$route.query.organization_assistant_id;
            let chat_id                     = storage(`reception_${organization_assistant_id}`);
            return {organization_assistant_id,chat_id}
        },
        async loadMessage(skip=0){
            if(this.searching){
                return;
            }
            if(skip==0){
                this.list               = [];
                this.listMap            = {};
                this.query.timestamp_lt = 0;
            } else {
                this.query.timestamp_lt = this.list[0]?this.list[0].timestamp:0;
            }
            this.searching              = true;
            let {data}                  = await this.$request.post("/common/reception/messages", {
                ...this.query
            }).finally(()=>this.searching = false );
            if (this.query.timestamp_lt==0){
                this.list               = []
                this.listMap            = {};
            }
            data.list.reverse();
            data.list.forEach(item=>this.messageAppend(item));
        },
        async messageDelete(message,options={}){
            await this.$request.post("/common/reception/messageDel", {
                message_id                  : message._id,
                ...this.get_parameters()
            },options);
            this.listRemoveItem(this.list,message);
            delete this.listMap[message._id];
        },
        messageAppend(message){
            if (!this.listMap[message._id]){
                message.content_html    = message.content
                this.listMap[message._id] = message;
                this.list.push(message)
            } else {
                message.content         = this.listMap[message._id].content + message.content;
                Object.assign(this.listMap[message._id],message);
            }
            this.md2html(message.content,(html)=>{
                this.listMap[message._id].content_html    = html;
                setTimeout(()=>{
                    let scoll           = this.$refs.scoll;
                    if (scoll.scrollTop==0 || Math.abs(scoll.scrollTop + scoll.clientHeight - scoll.scrollHeight)<100){
                        scoll.scrollTop     = scoll.scrollTop + scoll.clientHeight + 999999999;
                    }
                })
            });
        },
        async messagePopup(message){
            this.messageState           = true;
            this.messageStep            = -1;
            this.message                = null;
            let {data}                  = await this.$request.post("/common/reception/messageInfo",{
                message_id:message._id,
                ...this.get_parameters()
            })
            data.message.logs.sort((a,b)=>a.time-b.time)
            for(let log of data.message.logs){
                console.warn(log.list.join('\n\n'))
                log.list                = await this.md2html(log.list.join('\n\n'))
            }
            this.message                = data.message
        },
        async messageResend(message){
            let i                       = this.list.indexOf(message);
            let tasks                   = [];
            while(this.list[i]){
                tasks.push(this.messageDelete(this.list[i],{SUCCESS_TIPS_ENABLE:false,}))
                i++;
            }
            if(tasks.length){
                await Promise.all(tasks);
            }
            await Time.delay(1);
            this.$refs.input.toSend(message);
        },
        addAtUser(u){
            this.$refs.input.addAtUser(u)
        },
        async showMetadata(){
            let {data}                  = await this.$request.post("/common/reception/metadata",{
                ...this.get_parameters()
            });
            let content                 = [];
            Object.entries(data.metadata).forEach(([k,v])=>{
                content.push({label:k,value:v,name:k})
            });
            let metadata = await this.confirm({title:'已保存的数据',content,okText:'保存'});
            if(!metadata || typeof metadata!=='object'){
                return;
            }
            await this.$request.post("/common/reception/metadata_save",{
                metadata,
                ...this.get_parameters(),
            });
        },
    },
};
</script>

<template>
    <div class="c-container" :class="{'is-mobile':IS_MOBILE}">
        <a-modal v-model:open="reception_url_open" :footer="null" :width="220" title="扫码预览">
            <a-qrcode :value="reception_url" />
        </a-modal>
        <div class="c-body c-screen">
            <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>link({path:'/'})}]">
                <div class="c-title">{{chat?chat.name:''}}</div>
                <div class="c-options">
                    <div class="iconfont icon-source" @click="showMetadata()"></div>
                    <div class="iconfont icon-qrcode" @click="reception_url_open=true"></div>
                    <Clipboard class="hand" :text="reception_url" @clipboard-success="()=>aMessage().success('已复制到粘贴板')"><div class="iconfont icon-fenxiang"></div></Clipboard>
                </div>
            </CHead>
            <div class="chat">
                <div class="messages c-scoll pr">
                    <div v-if="messageState && message" class="message-pop">
                        <div class="c-form c-pd c-wd list">
                            <div>
                                <a-radio-group v-model:value="messageStep">
                                    <a-radio-button :value="-1">概览</a-radio-button>
                                    <template v-for="(log,i) in message.logs">
                                        <a-radio-button :value="i">日志{{i+1}}</a-radio-button>
                                    </template>
                                </a-radio-group>
                            </div>
                            <a-button type="primary" @click="messageState=false" style="po">关闭</a-button>
                        </div>
                    </div>
                    <div class="c-scoll" ref="scoll">
                        <a-drawer placement="top" :height="'auto'" :closable="false" :maskClosab="true" v-model:open="messageState" :get-container="false" :maskStyle="{background: 'rgba(255, 255, 255, 0.0)'}">
                            <div class="c-form view-extends" style="padding-top:60px;" v-if="message">
                                <template v-if="messageStep==-1">
                                    <a-descriptions title="一、理解问题" :column="1" size="small">
                                        <a-descriptions-item>{{message.understand}}</a-descriptions-item>
                                    </a-descriptions>
                                    <a-descriptions title="二、安装工具" :column="1" size="small">
                                        <template v-for="(e,i) in message.tools">
                                            <a-descriptions-item :label="`111`">{{e.used?'* ':''}}{{e.function.description}}</a-descriptions-item>
                                        </template>
                                        <a-descriptions-item v-if="message.tools.length==0">无</a-descriptions-item>
                                    </a-descriptions>
                                </template>
                                <template v-for="(log,i) in message.logs">
                                    <a-descriptions v-if="messageStep==i" :title="`${i+1}. ${log.remark}`" :column="1" size="small">
                                        <a-descriptions-item><div v-html="log.list" v-highlight style="background: #f5f5f5;padding: 1rem;width:100%;"></div></a-descriptions-item>
                                    </a-descriptions>
                                </template>
                            </div>
                            <div v-else>
                                <a-empty description="数据加载中..." />
                            </div>
                        </a-drawer>
                        <div class="c-form c-pd c-wd list">
                            <template v-for="(message,i) in list" :key="i">
                                <div class="message view-extends" :class="{self:message.user_id == user._id}">
                                    <div class="avatar" @click="addAtUser({_id:message.user_id,avatar:message.user_avatar,nickname:message.user_nickname,gender:message.user_gender})">
                                        <CoverImage class="img" v-if="user_map[message.user_id]" :src="user_map[message.user_id].avatar" :width="46" :height="46" :alt="user_map[message.user_id].nickname" />
                                        <CoverImage class="img" v-if="!user_map[message.user_id]" :src="message.user_avatar" :width="46" :height="46" :alt="message.user_nickname" />
                                    </div>
                                    <div class="container">
                                        <div class="content">
                                            <div class="inner">
                                                <div class="name">{{ message.user_nickname }}</div>
                                                <div class="html" v-html="message.content_html" v-highlight></div>
                                            </div>
                                        </div>
                                        <div class="bar">
                                            <div v-if="message.role=='user' && message.files.length" class="at-files">
                                                <div class="iconfont icon-fujian"></div>
                                                <div v-for="(f,i) in message.files" class="f" @click="fileDetails(f)">
                                                    <CoverImage v-if="fileIsImage(f)" class="img" :src="f.url" :width="18" :height="18" />
                                                    <div v-else class="icon-other iconfont" :class="'icon-'+f.type"></div>
                                                </div>
                                            </div>
                                            <div v-if="message.role=='user' && message.at_users.length" class="at-users">
                                                <template v-for="(u,i) in message.at_users">
                                                    <CoverImage class="img" :src="u.avatar" :width="18" :height="18" :alt="u.nickname" />
                                                </template>
                                            </div>
                                            <div class="iconfont btn hover icon-at" v-if="message.role!='user'" @click="addAtUser({_id:message.user_id,avatar:message.user_avatar,nickname:message.user_nickname,gender:message.user_gender})"></div>
                                            <div class="iconfont btn hover icon-dengpao" v-if="message.role!='user'" @click="messagePopup(message)"></div>
                                            <div class="iconfont btn hover icon-shuaxin" v-if="message.role=='user'" @click="messageResend(message)"></div>
                                            <div class="iconfont btn hover icon-shanchu" @click="messageDelete(message)"></div>
                                            <div v-if="message.role!='user' && message.at_users && message.at_users.length" class="at-users">
                                                <template v-for="(u,i) in message.at_users">
                                                    <CoverImage class="img" :src="u.avatar" :width="18" :height="18" :alt="u.nickname" />
                                                </template>
                                            </div>
                                            <span class="iconfont icon-shuaxin rotate_animation faster" v-if="message.role!='user' && ['completed','incomplete'].indexOf(message.status)<0"></span>
                                            <div class="st sdesc" v-if="message.status_description">
                                                <span>{{message.status_description}}</span>
                                            </div>
                                            <div class="st ctime">{{message.created}}</div>
                                        </div>
                                    </div>
                                </div>
                            </template>
                        </div>
                    </div>
                    <RoomInput v-if="chat" ref="input" @message-stream="messageAppend" :chat_id="chat._id" :chat="chat" />
                </div>
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.ant-btn-link {
    padding: 0;
}
.c-container{
    background:none;
    .c-body{
        height: 100vh;
        display: flex;
        flex-direction: column;
        max-width: 710px;
        margin: 0 auto;
        .c-head{
            width:100%;
            justify-content: space-between;
            height: 40px;
        }
        .c-form{
            width: 100%;
        }
    }
    .chat{
        display: flex;
        flex-direction: row;
        flex: 1;
        flex-shrink: 0;
        flex-grow: 1;
        overflow: hidden;

        .messages{
            flex-direction: column;
            flex-shrink: 0;
            flex-grow: 1;
            padding-bottom: 8rem;

            .list{
                .message{
                    margin-top:1rem;
                    display: flex;

                    &.self{
                        flex-direction: row-reverse;

                        .content{
                            justify-content: flex-end;

                            .name{
                                justify-content: flex-end;
                            }
                        }
                        .bar{
                            justify-content: flex-end;
                        }
                    }
                    .avatar{
                    .img{
                            border-radius: 50%;
                            border: solid 1px #ddd;
                            scale: 0.8;
                    }
                    }
                    .container{
                        width:calc(100% - 92px);
                        .content{
                            padding: 0.5rem;
                            display: flex;
                            overflow:auto;

                            .inner{
                                display: flex;
                                flex-direction: column;
                                .name{
                                    display: flex;
                                    font-weight: bold;
                                    padding-bottom: 0.5rem;
                                }
                                .html{

                                }
                            }
                        }
                        .bar{
                            align-items: center;
                            display: flex;
                            flex-direction: row;
                            .btn{}
                            .st{
                                font-size: 0.9rem;
                                color:#999;
                                margin: 0 0.5rem;
                                &.sdesc{}
                                &.ctime{}
                            }

                            .at-users{
                                display: flex;
                                align-items: center;
                                background: #eee;
                                padding: 4px;
                                border-radius: 5px;
                                color: #999;
                                margin-right: 5px;
                                &:before{
                                    content: '@';
                                }
                                .img{
                                    border-radius: 50%;
                                    margin: 0 4px;
                                }
                            }
                            .at-files{
                                display: flex;
                                align-items: center;
                                background: #eee;
                                padding: 4px;
                                border-radius: 5px;
                                .iconfont.icon-fujian{
                                    color: #999;
                                }
                                margin-right: 5px;
                                .f{
                                    word-break: break-all;
                                    font-size: 0.85rem;
                                    display: flex;
                                    align-items: center;

                                    .img{
                                        // scale: 0.5;
                                        margin: 0 4px;
                                    }
                                }

                            }
                        }
                    }
                }
            }

        }

        .message-pop{
            position: fixed;width: 100%;z-index: 100000;text-align: right;
            .c-form{
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding-left: 0;
            }
        }
    }

    .view-extends{
        :deep(audio) {
            display: block;
            height: 2.5rem;
        }
        :deep(img) {
            display: block;
            max-height: 200px;
            max-width: 100%;
            margin: 0.6rem 0;
        }
        :deep(video){
            display: block;
            max-width: 100%;
        }
    }
}
</style>
