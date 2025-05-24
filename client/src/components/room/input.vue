<script>
import Time from '../../common/utils/Time';
import RecordAudio from '../../common/utils/RecordAudio';


export default {
    components                          : {},
    props                               : {
        chat_id                         : {
            type                        : String,
            default                     : null,
        },
        disabled                        : {
            type                        : Array,
            default                     : [],
        },
    },
    data() {
        return {
            shifting                    : false,
            sending                     : false,
            send_signal                 : null,
            content                     : '',
            files                       : [],
            at_users                    : [],

            autoSize                    : { minRows: 2, maxRows: 26 },
            placeholder                 : '您有什么需要么？点击成员头像即可@他来回复。',
            maxlength                   : 2048,

            file_groups                 : [],
            file_list                   : [],
            file_accept                 : [],
            file_group                  : null,
            file_belong_to              : 'personal',
            file_uploading              : false,


            record_voice_ing            : false,
            record_voice_time           : 0,
        };
    },
    async mounted() {},
    async unmounted() {
        clearInterval(this.record_voice_ing);
    },
    watch: {
        '$route.query': {
            handler() {
                this.files              = [];
                this.at_users           = [];
                this.content            = '';
                this.file_groups        = [];
                this.file_list          = [];
                this.file_group         = null;

                this.stopSend();
            },
            immediate                   : true,
        },
    },
    methods: {
        async stopSend(){
            this.sending                = false;
            if (this.send_signal){
                try {
                    this.send_signal.abort();
                } catch (e) {
                    console.info('stop send:',e.message);
                }
            }
        },
        async toSend(message=null){
            if(this.sending){
                return;
            }
            if(message){
                this.content           = message.content;
                this.files             = message.files;
                this.at_users          = this.at_users.length?this.at_users:message.at_users;
            }
            if(!this.content.trim()){
                return this.aMessage().warn('请输入问题内容');
            }
            let content                 = this.content;
            this.sending                = true;
            await this.$request.post("/client/chat/send", {
                chat_id                 : this.chat_id || this.$route.query.chat_id,
                at_users                : this.at_users,
                files                   : this.files,
                content                 : content,
            },{onStream:(message,signal)=>{
                this.send_signal        = signal;
                this.content            = '';
                if(message.code===undefined && message._id){
                    // this.$emit('message-stream',message);
                }
            }}).finally(()=>{
                this.sending            = null
                this.content            = '';
                this.at_users           = [];
                this.files              = [];
                this.send_signal        = null;
            });
        },

        async addAtUser(user){
            if(user._id==this.user._id){
                return;
            }
            for(let i in this.at_users){
                let u                   = this.at_users[i]
                if(u._id == user._id){
                    return this.listRemoveItem(this.at_users,null,i);
                }
            }
            this.at_users.push({
                _id                     : user._id,
                nickname                : user.nickname,
                gender                  : user.gender,
                avatar                  : user.avatar,
            });
        },

        async file_selection(){
            // let {data}                  = await this.$request.post("/client/file/statistics", {
            //     organization_id         : this.file_belong_to=='organization'?this.organization._id:''
            // });
            // let file_groups             = [];
            // data.list.forEach(g=>['image','document'].indexOf(g.type)>-1?file_groups.push(g):'')
            // this.file_groups            = file_groups;

            this.file_groups            = [
                {
                    "icon": "icon-image",
                    "name": "图片",
                    "supported": "png,jpg,jpeg,gif",
                    "type": "image"
                },
                {
                    "icon": "icon-docs",
                    "name": "文档",
                    "supported": "docx",
                    "type": "document"
                },
                {
                    "icon": "icon-audio",
                    "name": "音频",
                    "supported": "mp3,wav,m4a",
                    "type": "audio"
                }
            ]

            this.file_group             = this.file_groups[0]
            this.file_list              = [];
            this.file_search(0)
        },
        async file_search(skip=0){
            let accept                  = [];
            this.file_group.supported.split(',').forEach(s=>accept.push('.'+s));
            this.file_accept            = accept.join(',');
            let {data}                  = await this.$request.post("/client/file/search", {
                organization_id         : this.file_belong_to=='organization'?this.organization._id:'',
                supported               : this.file_group.supported,
                skip                    : skip,
                size                    : 10,
                sort                    : 'created desc',
            });
            if (skip==0){
                this.file_list          = data.list;
            } else {
                data.list.forEach((item)=>{
                    this.file_list.push(item);
                });
            }
        },
        async file_close(){
            this.file_group             = null;
        },

        async record_voice(){
            this.ra                     = new RecordAudio()
            this.record_voice_time      = 60;
            this.record_voice_ing       = setInterval(() => {
                this.record_voice_time--;
                if(this.record_voice_time<=0){
                    this.record_stop()
                }
            }, 1000);
            this.ra.start(async ({file})=>{
                console.log(file)
                let {data}                  = await this.$request.post("/client/file/upload", {
                    file,
                    private                 : '1',
                    organization_id         : this.file_belong_to=='organization'?this.organization._id:'',
                },{headers:{'Content-Type': 'multipart/form-data'}});
                this.file_list.unshift(data.file)
            })
        },
        async record_stop(){
            if(this.ra){
                this.ra.stop()
            }
            clearInterval(this.record_voice_ing);
            this.record_voice_ing       = false;
        },

        async fileSelect(file){
            this.files                  = [
                file
            ];
            this.file_group             = null;
        },

        async uploadNotice(file){
            this.file_uploading          = false;
            if (file.status=='failed'){
                return this.aMessage().error(file.reason)
            }
            await Time.delay(1);
            this.file_list.unshift(file);
        }
    },
};
</script>

<template>
    <div class="input c-pd c-wd" :class="{full:file_group}" @click.stop="file_close()">
        <div class="c-form" @click.stop>
            <div class="files" v-if="file_group">
                <div class="groups">
                    <a-radio-group v-model:value="file_group" size="small" button-style="solid" @change="file_search(0)">
                        <template v-for="(g,i) in file_groups">
                            <a-radio-button :value="g" :disabled2="!/doc/.test(g.supported)">{{g.name}}</a-radio-button>
                        </template>
                    </a-radio-group>
                    <a-radio-group size="small" v-model:value="file_belong_to" button-style="solid" @change="file_search(0)">
                        <a-radio-button value="organization">组织的</a-radio-button>
                        <a-radio-button value="personal">个人的</a-radio-button>
                    </a-radio-group>
                </div>
                <CList class="list" @scrollBottom="file_search(file_list.length)" :class="file_group.type">
                    <template #list>
                        <div class="f" v-if="file_group.type=='image'">
                            <CFile ref="file" width="80px" height="80px" private="1" @submit="uploadNotice" @change="file_uploading=true" @cancel="file_uploading=false" :autoSubmit="true" background="none" class="iconfont" :accept="file_accept" :organization_id="file_belong_to=='organization'?this.organization._id:''">
                                <template v-slot:initial> <div class="iconfont icon-upload run" :class="{'icon-loading':file_uploading}"></div></template>
                                <template v-slot:preview> <div class="iconfont icon-upload run" :class="{'icon-loading':file_uploading}"></div></template>
                            </CFile>
                        </div>
                        <div class="f" v-if="file_group.type!='image'">
                            <CFile ref="file" height="30px" private="1" @submit="uploadNotice" @change="file_uploading=true" @cancel="file_uploading=false" :autoSubmit="true" border="none" background="none" class="iconfont" :accept="file_accept" :organization_id="file_belong_to=='organization'?this.organization._id:''">
                                <template v-slot:initial> <div class="iconfont icon-upload run" :class="{'icon-loading':file_uploading}">点击选择文件</div></template>
                                <template v-slot:preview> <div class="iconfont icon-upload run" :class="{'icon-loading':file_uploading}">点击选择文件</div></template>
                            </CFile>
                            <div class="hand" v-if="file_group.type=='audio' && !record_voice_ing" @click="record_voice()"><AudioOutlined />点击录音</div>
                            <div class="hand" v-if="file_group.type=='audio' &&  record_voice_ing" @click="record_stop()"><LoadingOutlined />点击停止({{record_voice_time}})</div>
                        </div>
                        <template v-for="(f,i) in file_list">
                            <div class="f" v-if="file_group.type=='image'" @click.stop="fileSelect(f)">
                                <div class="avatar">
                                    <CoverImage class="avatar iconfont" :src="f.url" :width="80" :height="80" />
                                </div>
                            </div>
                            <div class="f" v-else @click.stop="fileSelect(f)">
                                <div class="avatar">
                                    <div class="avatar icon-other iconfont" :class="'icon-'+f.type"></div>
                                </div>
                                <div class="name no-select">
                                    {{f.name}}
                                </div>
                            </div>
                        </template>
                    </template>
                </CList>
            </div>
            <a-textarea class="textarea" :disabled="sending" v-model:value="content" :autoSize="autoSize" :placeholder="placeholder" @keydown="({keyCode})=>keyCode==16?shifting=true:''" @keyup="({keyCode})=>keyCode==16?shifting=false:''" @pressEnter="shifting || toSend()" :show-count="false" :maxlength="maxlength" />
            <div class="bar">
                <div class="options">
                    <template v-if="disabled.indexOf('file')==-1">
                        <div class="iconfont hover btn icon-upload" v-if="!file_group" @click="file_selection"></div>
                        <div class="iconfont hover btn icon-close" v-else="file_group" @click="file_close"></div>
                    </template>
                </div>
                <div class="at-files">
                    <template v-for="(f,i) in files">
                        <div class="f" @click="listRemoveItem(files,f)">
                            <CoverImage class="pic" v-if="fileIsImage(f)" :src="f.url" :width="30" :height="30" />
                            <div v-else class="icon-other iconfont" :class="'icon-'+f.type"></div>
                            <div class="name">{{f.name}}</div>
                        </div>
                    </template>
                </div>
                <div class="at-users" style="padding-right: 1rem;">
                    <template v-for="(u,i) in at_users">
                        <CoverImage class="u" :src="u.avatar" :width="30" :height="30" :alt="u.nickname" @click="listRemoveItem(at_users,u)" />
                    </template>
                </div>
                <div class="options">
                    <div v-if="sending!=true" class="iconfont hover btn icon-fasong" @click="toSend()"></div>
                    <div v-if="sending==true" class="iconfont hover btn icon-loading run" @click="stopSend"></div>
                </div>
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
#app{
    .files{
        .groups{
            display: flex;
            justify-content: space-between;
        }

        .list{
            width:100%;
            height:260px;
            overflow: auto;
            margin: 7px 0;

            .f{
                display: flex;
                align-items: center;
                justify-content: flex-start;
                min-height: 32px;
                font-size: 13px;
                .avatar{
                    width: 30px;
                    height: 30px;
                    font-size: 28px;
                }
                .name{
                    padding:0 10px;
                    display: -webkit-box;
                    -webkit-box-orient: vertical;
                    -webkit-line-clamp: 2;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }

                .icon-upload {
                    width: 100%;
                    height: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size:0.8rem;
                    &::before{
                        font-size: 18px;
                    }
                }
            }
            &.image{
                display: flex;
                flex-direction: row;
                flex-wrap: wrap;
                align-content: flex-start;
                .avatar{
                    width: 80px;
                    height: 80px;
                }
            }
        }
    }

    .input{
        position: absolute;
        bottom: 0;
        width: 100%;
        display: flex;
        align-items: flex-end;
        &.full{
            height: 100%;
        }

        .c-form{
            background: #f5f5f5;
            padding: 0.5rem;
            border-radius: 0.5rem;
        }
        .textarea{
            background: none;
            border: none;
        }
        .bar{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-direction: row;
            height: 30px;
            flex: 0 0 auto;
            width:100%;
            .options{
                display: flex;
                height: 100%;
                .iconfont{
                    font-size: 1.6rem;
                }
            }
            .at-users{
                flex: 1;
                margin-left:auto;
                text-align: right;
                .u{
                    border-radius: 50%;
                    scale: 0.8;
                    cursor: pointer;
                }
            }

            .at-files{
                flex: 1;
                width: calc(100% - 200px);
                .f{
                    word-break: break-all;
                    margin-left:auto;
                    cursor: pointer;
                    font-size: 0.85rem;
                    display: flex;
                    align-items: center;

                    .pic{
                        scale: 0.8;
                    }

                    .name{
                        word-break: break-all;

                        white-space: nowrap;   /* 不换行 */
                        overflow: hidden;      /* 隐藏超出的文本 */
                        text-overflow: ellipsis;
                    }
                }

            }
        }
    }
}
</style>
