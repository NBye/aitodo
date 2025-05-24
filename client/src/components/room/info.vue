<script>
import Time from '../../common/utils/Time';
import {HOST} from '../../common/utils/request';
export default {
    components                          : {},
    data() {
        return {
            HOST,
            loading                     : false,
            chat                        : null,
            users                       : [],
            menu                        : [],
            user_ids                    : [],
            user_map                    : {},

            showd                       : false,
        };
    },
    async unmounted() {
        this.$EventBus.off('chat-user-join',this.chat_user_join);
        this.$EventBus.off('chat-user-leave',this.chat_user_leave);
    },
    async mounted() {
        this.$EventBus.on('chat-user-join',this.chat_user_join);
        this.$EventBus.on('chat-user-leave',this.chat_user_leave);
    },
    watch: {
        '$route.query': {
            handler() {
                if(this.organization && this.user){
                    this.loadInfo()
                }
            },
            immediate                   : true,
        },
    },
    methods: {
        async chat_user_leave({chat,user}){
            if(chat._id == this.chat._id){
                this.delUser(user);
            }
        },
        async chat_user_join({chat,user}){
            if(chat._id == this.chat._id){
                this.addUser(user);
            }
        },
        async delUser(u){
            for(let i in this.users){
                let o =                 this.users[i];
                if(o._id==u._id){
                    this.users.splice(i,1);
                    delete this.user_map[u._id];
                    this.user_ids       = Object.keys(this.user_map);
                    break;
                }
            }
        },
        async addUser(u){
            if(!this.user_map[u._id]){
                this.users.push(u);
            }
            this.user_map[u._id]        = Object.assign(this.user_map[u._id] || {},u);
            this.user_ids               = Object.keys(this.user_map);
        },
        async loadInfo(){
            this.loading                = true;
            let {data}                  = await this.$request.post("/client/chat/info", Object.assign({
                organization_id         : this.organization._id,
                chat_id                 : this.$route.query.chat_id,
            },this.query),{}).finally(()=>this.loading = false );
            this.chat                   = data.chat;
            this.users                  = [];
            this.user_map               = {};
            data.users.forEach(u=>this.addUser(u));
        },
        async toEdit(){
            let data = await this.confirm({title:'编辑信息',content:[
                {name:'name',value:this.chat.name,label:'会话名称',maxlength:10,placeholder:'名称1~10个字符',reg:'/^.{10}$/'},
                {name:'remark',value:this.chat.remark,label:'会话备注',maxlength:20,type: 'textarea',placeholder:'备注1~20个文字',reg:'/^.{20}$/'},
            ]});
            if(data==false){
                return;
            }
            let rs                      = await this.$request.post("/client/chat/upset", {
                chat_id                 : this.chat._id,
                ...data
            });
            this.$EventBus.emit('chat-update', { chat:rs.data.chat });
            Object.assign(this.chat,rs.data.chat);
        },
        async toDestroy(){
            if (!await this.confirm({title:'确认解散',content:'解散后不可恢复，确认是否删除？'})){
                return;
            }
            await this.$request.post("/client/chat/destroy", {
                chat_id                 : this.chat._id,
            });
            this.$EventBus.emit('chat-destroy', { chat:this.chat });
            this.link({ path: '/console/chat' },'replace');
        },
        async removeUser(user){
            this.$refs.as.show([
                {icon:'icon-tichu',name:'移除成员',description:user.nickname,click:()=>{
                    this.$request.post("/client/chat/leave", {
                        chat_id                 : this.chat._id,
                        user_id                 : user._id,
                    }).then(async ({data})=>{
                        this.$EventBus.emit('chat-user-leave', { chat:this.chat, user });
                        await Time.delay(1);
                        Object.assign(this.chat,data.chat);
                        this.$EventBus.emit('chat-update', { chat:data.chat });
                    });
                    return true;
                }},
            ])
        },
        async inviteUser(users){
            if(!users.length){
                return this.$refs.msu.hide();
            }
            let user_ids                = [];
            users.forEach(u=>{
                user_ids.push(u._id);
            });
            let {data} = await this.$request.post("/client/chat/invite", {
                chat_id                 : this.chat._id,
                user_ids                : user_ids,
            }).finally(()=>{
                this.$refs.msu.hide();
            });
            users.forEach(user=>{
                this.$EventBus.emit('chat-user-join', { chat: this.chat, user });
            });
            await Time.delay(1);
            Object.assign(this.chat,data.chat);
            this.$EventBus.emit('chat-update', { chat: data.chat });
            data.messages.forEach(message=>{
                this.$emit('addMessage',message)
            });
        },
        addAtUser(u){
            if(this.isOffline(u) || this.user._id==u._id){
                return;
            }
            this.$emit('addAtUser',{_id:u._id,avatar:u.avatar,nickname:u.nickname,gender:u.gender})
        },
        show(){
            this.showd=true;
            this.loadInfo();
        },
        hide(){this.showd=false;},
        toggle(){this.showd?this.hide():this.show()},

        async selectavatar({target}){
            let file = target.files[0]
            let reader                  = new FileReader();
            reader.onload=(e)=> {
                this.chat.avatar        = e.target.result;
            };
            reader.readAsDataURL(file);
            let {data}                  = await this.$request.post("/client/chat/up_avatar", {
                chat_id                 : this.chat._id,
                organization_id         : this.organization._id,
                avatar                  : file,
            });
            await Time.delay(1)
            this.chat = data.chat
            this.$EventBus.emit('chat-update', { chat:data.chat });
        },
    },
};
</script>

<template>
    <div class="info c-scoll am faster" :class="{show:showd}">
        <div v-if="chat" class="basis c-pd c-wd">
            <a-descriptions title="基础信息" :column="1">
                <a-descriptions-item label="chat_id">{{chat._id}}</a-descriptions-item>
                <a-descriptions-item label="图标">
                    <CFile ref="file" @change="selectavatar" :autoSubmit="false" border="none" background="none">
                        <template v-slot:initial>
                            <CoverImage class="img" :src="chat.avatar" :width="100" :height="100" :alt="chat.name" />
                        </template>
                        <template v-slot:preview>
                            <CoverImage class="img" :src="chat.avatar" :width="100" :height="100" :alt="chat.name" />
                        </template>
                    </CFile>
                </a-descriptions-item>
                <a-descriptions-item label="名称">{{chat.name}}</a-descriptions-item>
                <a-descriptions-item label="时间">{{chat.created}}</a-descriptions-item>
            </a-descriptions>
            <a-space :size="8">
                <a-button type="link" @click="toDestroy">
                    解散<template #icon><DeleteOutlined /></template>
                </a-button>
                <a-button type="link" @click="$refs.msu.show()">
                    邀请<template #icon><UsergroupAddOutlined /></template>
                </a-button>
                <a-button type="link" @click="toEdit">
                    编辑<template #icon><EditOutlined /></template>
                </a-button>
            </a-space>
        </div>
        <div class="users">
            <div v-if="chat" class="basis c-pd c-wd">
                <a-descriptions title="成员信息" :column="1"> </a-descriptions>
            </div>
            <a-list item-layout="horizontal" :data-source="users" size="small" :split="false">
                <template #renderItem="{ item }">
                    <a-list-item>
                        <template #actions>
                            <MoreOutlined v-if="item._id != user._id" @click="removeUser(item)" />
                        </template>
                        <a-skeleton avatar :title="false" :loading="false" active>
                            <a-list-item-meta>
                                <template #title>
                                    {{ item.nickname }}
                                </template>
                                <template #avatar>
                                    <a-avatar :class="{gray:isOffline(item)}" :src="cutImgUrl(item.avatar,{w:100,h:100,alt:item.nickname})" @click="addAtUser(item)" />
                                </template>
                            </a-list-item-meta>
                        </a-skeleton>
                    </a-list-item>
                </template>
            </a-list>
        </div>
        <template v-if="organization">
            <ActionSheet ref="as" :list="menu" />
            <ModalSearchUser ref="msu" :query="{organization_id:organization._id,size:5}" :disabled-user-id-list="user_ids" @submit="inviteUser" />
        </template>
    </div>
</template>

<style lang="scss" scoped>
.ant-btn-link {
    padding: 0;
}

.info.c-scoll{
    max-width: 260px;
    min-width: 200px;
    border-left: solid 1px #ddd;
    background: #f5f5f5;
    display: none;
    &.show{
        display: flex;
    }
    .basis{}
    .users{}
}

.is-mobile{
    .chat{
        .info{
            width:100vw;
            min-width: 100vw;
            max-width: 100vw;
            margin-right: -100vw;
            display: flex;
            &.show{
                margin-right: 0;
            }
        }
    }
}
</style>
