<script>
import Time from '../../../common/utils/Time';
import IDate from '../../../common/utils/IDate';
import RoomInfo from "../../../components/room/info.vue";
import RoomInput from "../../../components/room/input.vue";
import handleExportWord from "xh-htmlword";

export default {
	components: {
        RoomInfo,RoomInput,
    },
    data() {
        return {
            IS_PAGE                     : true,
            PAGESHOW                    : false,
            query                       : {
                chat_id                 : '',
                size                    : 20,
                sort                    : 'timestamp desc',
                timestamp_lt            : 0,
            },
            list                        : [],
            listMap                     : {},

            searching                   : false,

            //消息详情
            messageState                : false,
            messageStep                 : 0,
            message                     : null,
        };
    },
    async unmounted() {
        this.$EventBus.off('chat-message-stream',this.on_message_stream);
        this.$EventBus.off('chat-message-remove',this.on_message_remove);
        
    },
    async mounted() {
        this.$EventBus.on('chat-message-stream',this.on_message_stream);
        this.$EventBus.on('chat-message-remove',this.on_message_remove);

        let scoll                       = this.$refs.scoll;
        let stop                        = 0;
        scoll.addEventListener('scroll', ()=> {
            if (scoll.scrollTop==0 && scoll.scrollTop<stop){
                this.loadMessage(false);
            }
            stop                        = scoll.scrollTop;
        });
        scoll.addEventListener('click', async (e)=> {
            if (e.target.tagName.toLowerCase() === 'img') {

                if(await this.confirm({ title :'确认下载此图片？',  okText:'下载', })){
                    window.open(e.target.getAttribute('src'))
                    // fetch(e.target.getAttribute('src'))
                    // .then(response => response.blob())
                    // .then(blob => {
                    //     const url = window.URL.createObjectURL(blob); // 创建一个临时 URL
                    //     const link = document.createElement('a');
                    //     link.href = url;
                    //     link.download = 'download-aitodo-'+IDate.format('yyyymmddhhiiss')+'.jpg'; // 设置文件名
                    //     link.click(); // 自动触发下载
                    // }).catch(error => {
                    //     console.error('图片下载失败', error);
                    // });
                }
            }
        });
    },
    watch: {
        '$route.query': {
            async handler(){
                this.PAGESHOW           = true;
                this.searching          = false;
                this.query.chat_id      = this.$route.query.chat_id;
                this.messageState       = false;
                this.messageStep        = 0;
                this.message            = null;
                if (this.organization && this.user){
                    await this.loadMessage();
                }
            },
            immediate                   : true,
        },
    },
    methods: {
        async on_message_stream(message){
            if(message.chat_id==this.query.chat_id){
                await this.messageAppend(message)
                message                 = this.listMap[message._id]
                this.$refs.input.sending = ['incomplete','completed',null].indexOf(message.status)<0;
            }
        },
        async on_message_remove(message){
            for(let m of this.list){
                if(m._id == message._id){
                    this.listRemoveItem(this.list,m);
                    delete this.listMap[m._id];
                    break;
                }
            }
        },
        async loadMessage(reload=true){
            if(this.searching){
                return;
            }
            if(reload){
                this.list               = [];
                this.listMap            = {};
            }
            this.searching              = true;
            let {data}                  = await this.$request.post("/client/chat/messages", {
                ...this.query,
                organization_id         : this.organization._id,
                timestamp_lt            : this.list[0]?this.list[0].timestamp:0,
            },{}).finally(()=>this.searching = false );
            if (reload){
                this.list               = []
                this.listMap            = {};
            }
            data.list.reverse();
            data.list.forEach(item=>this.messageAppend(item,reload?'push':'unshift'));
            this.list.sort((a, b) => a.timestamp - b.timestamp);

            if(reload && this.list.length && ['incomplete','completed'].indexOf(this.list[this.list.length-1].status)<0){
                this.$refs.input.sending=true;
            }
        },
        async messageDelete(message,options={}){
            await this.$request.post("/client/chat/messageDel", {
                message_id              : message._id,
            },options);
            // this.listRemoveItem(this.list,message);
            // delete this.listMap[message._id];
        },
        messageAppend(message,offset='push'){
            if (!this.listMap[message._id]){
                message.content_html    = message.content
                this.listMap[message._id] = message;
                this.list[offset](message)
            } else {
                message.content         = this.listMap[message._id].content + message.content;
                Object.assign(this.listMap[message._id],message);
            }
            this.md2html(message.content,(html)=>{
                this.listMap[message._id].content_html    = html;
                if(offset=='push'){
                    setTimeout(()=>{
                        let scoll       = this.$refs.scoll;
                        if (message.role=='user' || scoll.scrollTop==0 || Math.abs(scoll.scrollTop + scoll.clientHeight - scoll.scrollHeight)<100){
                            scoll.scrollTop = scoll.scrollTop + scoll.clientHeight + 999999999;
                        }
                    })
                }
            });
            if(this.summarying){
                clearTimeout(this.summarying)
            }
            this.summarying=setTimeout(()=>{
                if(this.listMap[message._id] && this.listMap[message._id].status == 'completed' && this.$refs.info.chat && !this.$refs.info.chat.remark){
                    this.$request.post("/client/chat/summary",{chat_id:this.query.chat_id}).then(({data})=>{
                        this.$EventBus.emit('chat-update', { chat: data.chat });
                    });
                }
            },1000*2)
        },
        async messagePopup(message){
            this.messageState           = true;
            this.messageStep            = -1;
            this.message                = null;
            let {data}                  = await this.$request.post("/client/chat/messageInfo",{message_id:message._id})
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
        async messagePrompt(message,prompt){
            this.$refs.input.toSend({
                content                 : prompt,
                files                   : [],
                at_users                : [{
                    _id                 : message.user_id,
                    nickname            : message.user_nickname,
                    gender              : message.user_gender,
                    avatar              : message.user_avatar,
                }]
            });
        },
        addAtUser(u){
            this.$refs.input.addAtUser(u)
        },
        async showMetadata(){
            let {data}                  = await this.$request.post("/client/chat/metadata",{
                organization_id         : this.organization._id,
                chat_id                 : this.$route.query.chat_id,
            });
            let content                 = [];
            Object.entries(data.metadata).forEach(([k,v])=>{
                content.push({label:k,value:v,name:k})
            });
            let metadata = await this.confirm({title:'已保存的数据',content,okText:'保存'});
            if(!metadata || typeof metadata!=='object'){
                return;
            }
            await this.$request.post("/client/chat/metadata_save",{
                organization_id         : this.organization._id,
                chat_id                 : this.$route.query.chat_id,
                metadata,
            });
        },

        async download(type,message){
            let name = `${message.user_nickname}-${message._id}`
            if(type=='html'){
                let dom = document.getElementById('m'+message._id)
                const blob              = new Blob([dom.innerHTML], { type: 'text/plain' });
                const link              = document.createElement('a');
                link.href               = URL.createObjectURL(blob);
                link.download           = `${name}.html`,
                link.click();
                URL.revokeObjectURL(link.href);
            } else if(type=='markdown'){
                const blob              = new Blob([message.content], { type: 'text/plain' });
                const link              = document.createElement('a');
                link.href               = URL.createObjectURL(blob);
                link.download           = `${name}.md`,
                link.click();
                URL.revokeObjectURL(link.href);
            } else if(type=='docx'){
                handleExportWord({
                    dom: '#m'+message._id,
                    fileName: `${name}.docx`,
                });
            }
        },

    },
};
</script>

<template>
    <div class="c-body c-screen am faster" :class="{show:PAGESHOW}">
        <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title" @click="$refs.info.toEdit()">{{(this.$refs.info && this.$refs.info.chat)?this.$refs.info.chat.name:'聊天'}}</div>
            <div class="c-options">
                <div class="iconfont icon-source" @click="showMetadata()"></div>
                <div class="iconfont icon-more icon-menu" @click="$refs.info.toggle()"></div>
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
                        <div class="view-extends c-form" style="padding-top:60px;" v-if="message">
                            <template v-if="messageStep==-1">
                                <a-descriptions title="一、理解问题" :column="1" size="small">
                                    <a-descriptions-item>{{message.understand}}</a-descriptions-item>
                                </a-descriptions>
                                <a-descriptions title="二、安装工具" :column="1" size="small">
                                    <template v-for="(e,i) in message.tools">
                                        <a-descriptions-item :label="``">{{e.used?'* ':''}}{{e.function.description}}</a-descriptions-item>
                                    </template>
                                    <a-descriptions-item v-if="message.tools.length==0">无</a-descriptions-item>
                                </a-descriptions>
                                <a-descriptions title="三、嵌入数据" :column="1" size="small">
                                    <template v-for="(e,i) in message.embeddings">
                                        <a-descriptions-item :label="`${i+1}`">
                                            <div>
                                                <div>use {{e.usetime}}ms {{e.description}}</div>
                                                <pre style="max-height: 200px;overflow: auto;">{{e.output}}</pre>
                                            </div>
                                        </a-descriptions-item>
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
                        <!-- <a-empty v-if="searching || list.length==0" :description="searching?'数据加载中...':'暂无消息'" /> -->
                        <template v-for="(message,i) in list" :key="i">
                            <div class="message view-extends" :class="{self:message.user_id == user._id}">
                                <div class="avatar" @click="addAtUser({_id:message.user_id,avatar:message.user_avatar,nickname:message.user_nickname,gender:message.user_gender})">
                                    <CoverImage class="img" v-if="$refs.info.user_map[message.user_id]" :src="$refs.info.user_map[message.user_id].avatar" :width="46" :height="46" :alt="$refs.info.user_map[message.user_id].nickname" />
                                    <CoverImage class="img" v-if="!$refs.info.user_map[message.user_id]" :src="message.user_avatar" :width="46" :height="46" :alt="message.user_nickname" />
                                </div>
                                <div class="container">
                                    <div class="content">
                                        <div class="inner">
                                            <div class="name" v-if="$refs.info.users.length>2">{{ message.user_nickname }}</div>
                                            <div class="html" :id="'m'+message._id" v-html="message.content_html" v-highlight></div>
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

                                        <a-popover title="导出为：">
                                            <template #content>
                                                <p><a-button type="link" size="small" @click="download('markdown',message)">markdown</a-button></p>
                                                <p><a-button type="link" size="small" @click="download('html',message)">html</a-button></p>
                                                <p><a-button type="link" size="small" @click="download('docx',message)">docx</a-button></p>
                                            </template>
                                            <div class="iconfont btn hover icon-download" v-if="message.role!='user'"></div>
                                        </a-popover>

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
                                    <div class="prompts">
                                        <div v-for="p in message.prompts">
                                            <div class="prompt hand" @click="messagePrompt(message,p)">{{p}}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </template>
                    </div>
                </div>
                <RoomInput ref="input"/>
                <!-- <RoomInput ref="input" @message-stream="messageAppend" /> -->
            </div>
            <RoomInfo ref="info" @addAtUser="addAtUser"/>
            <!-- <RoomInfo ref="info" @addAtUser="addAtUser" @addMessage="messageAppend" /> -->
        </div>
    </div>
</template>

<style lang="scss" scoped>

.ant-btn-link {
    padding: 0;
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
                    .prompts{
                        display: flex;
                        flex-direction: column;
                        .prompt{
                            border: solid 1px #eee;
                            display: inline-block;
                            padding: 4px 8px;
                            border-radius: 4px;
                            margin: 4px 0;
                            &:hover{
                                background-color:#f5f5f5;
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
            object-fit: contain;
            object-position: left;
        }
        :deep(video){
            display: block;
            max-width: 100%;
        }
    }
}
</style>
