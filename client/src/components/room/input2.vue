<script>
import Time from '../../common/utils/Time';
import {HOST} from '../../common/utils/request';
export default {
    components                          : {},
    props                               : {
        chat_id                         : {
            type                        : String,
            default                     : null,
        },
        chat                            : {
            type                        : Object,
            default                     : null,
        },
        disabled                        : {
            type                        : Array,
            default                     : [],
        },
    },
    data() {
        return {
            HOST,
            shifting                    : false,
            sending                     : false,
            send_signal                 : null,
            content                     : '',
            files                       : [],
            at_users                    : [],

            autoSize                    : { minRows: 2, maxRows: 26 },
            placeholder                 : '您有什么需要么？点击成员头像即可@他来回复。',
            maxlength                   : 2048,

            file_uploading              : false,
        };
    },
    async mounted() {},
    watch: {
        '$route.query': {
            handler() {
                this.files              = [];
                this.at_users           = [];
                this.content            = '';

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
            await this.$request.post("/common/reception/send", {
                chat_id                 : this.chat_id || this.$route.query.chat_id,
                at_users                : this.at_users,
                files                   : this.files,
                content                 : content,
            },{onStream:(message,signal)=>{
                this.send_signal        = signal;
                this.content            = '';
                if(message.code===undefined && message._id){
                    // this.$EventBus.emit('chat-message-stream',message);
                    this.$emit('message-stream',message);
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

        async uploadNotice(file){
            if (file.status=='failed'){
                return this.aMessage().error(file.reason)
            }
            await Time.delay(1);
            this.file_uploading          = false;
            this.files.unshift(file);
        },

        async uploadSubmit({file}){
            this.file_uploading         = true;
            if(file.status=="done"){
                if(file.response.code!=1){
                    this.aMessage(file.response.message)
                } else {
                    await Time.delay(1)
                    this.files          = [
                        file.response.data.file
                    ]
                }
                this.file_uploading     = false;
            }
        },
    },
};
</script>

<template>
    <div class="input c-pd c-wd" @click.stop="file_close()">
        <div class="c-form" @click.stop>
            <a-textarea class="textarea" :disabled="sending" v-model:value="content" :autoSize="autoSize" :placeholder="placeholder" @keydown="({keyCode})=>keyCode==16?shifting=true:''" @keyup="({keyCode})=>keyCode==16?shifting=false:''" @pressEnter="shifting || toSend()" :show-count="false" :maxlength="maxlength" />
            <div class="bar">
                <div class="options">
                    <a-upload name="file" :showUploadList="false" :max-count="1" :action="HOST+'/common/reception/upload'" :data="{chat_id:chat._id}" @change="uploadSubmit">
                        <div class="iconfont hover btn icon-upload run" :class="{'icon-loading':file_uploading}"></div>
                    </a-upload>
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
