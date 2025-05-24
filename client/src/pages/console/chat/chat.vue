<script>
export default {
    data() {
        return {
            IS_PAGE                     : true,
            query                       : {
                keyword                 : '',
                role                    : "",  //缺省全部，assistant,user
                skip                    : 0,
                size                    : 200,
                sort                    : 'updated DESC'
            },
            list                        : [],
            search_ing                  : false,
        };
    },
    async unmounted() {
        this.$EventBus.off('chat-update',this.chat_update);
        this.$EventBus.off('chat-create',this.chat_create);
        this.$EventBus.off('chat-destroy',this.chat_destroy);
        this.$EventBus.off('chat-user-leave',this.chat_user_leave);
        this.$EventBus.off('chat-user-join',this.chat_user_join);
    },
    async mounted() {
        this.$EventBus.on('chat-update',this.chat_update);
        this.$EventBus.on('chat-create',this.chat_create);
        this.$EventBus.on('chat-destroy',this.chat_destroy);
        this.$EventBus.on('chat-user-leave',this.chat_user_leave);
        this.$EventBus.on('chat-user-join',this.chat_user_join);
        if (this.organization){
            this.search(0);
        }
    },
    methods: {
        async chat_user_join({chat,user}){
            if(this.user._id!=user._id){
                return;
            }
            for(let i in this.list){
                if(this.list[i]._id==chat._id){
                    return;
                }
            }
            this.chat_create({chat})
        },
        async chat_user_leave({chat,user}){
            if(this.user._id!=user._id){
                return;
            }
            for(let i in this.list){
                if(this.list[i]._id==chat._id){
                    this.list.splice(i,1);
                    break;
                }
            }
        },
        async chat_update({chat}){
            this.list.forEach(item=>{
                if(item._id == chat._id){
                    Object.assign(item,chat);
                }
            });
        },
        async chat_destroy({chat}){
            if(chat.user_ids.indexOf(this.user._id)<0){
                return;
            }
            for(let i in this.list){
                let o =                 this.list[i];
                if(o._id==chat._id){
                    this.list.splice(i,1);
                    break;
                }
            }
        },
        async chat_create({chat}){
            if(chat.user_ids.indexOf(this.user._id)<0){
                return;
            }
            chat.active             = chat._id == this.$route.query.chat_id;
            chat.tags               = chat.role=='assistant'?['icon-ai'] : []
            console.log(chat)
            this.list.unshift(chat);
        },
        async search(skip=0) {
            if(this.search_ing){
                return;
            }
            if(skip==0){
                this.list               = [];
            }
            this.query.skip             = skip;
            this.search_ing             = true;
            let {data}                  = await this.$request.post("/client/chat/search", Object.assign({
                organization_id         : this.organization._id,
            },this.query),{}).finally(()=>this.search_ing = false );
            data.list.forEach(item=>{
                item.active             = item._id == this.$route.query.chat_id;
                item.tags               = item.role=='assistant'?['icon-ai'] : []
            });
            if (this.query.skip==0){
                if(data.list.length==0){
                    this.aMessage().warn('暂无聊天，选择一个成员再发起对话。')
                    return this.link({path:'/console/personnel'},'replace')
                }
                this.list               = data.list
                if(this.list.length && !this.$route.query.chat_id){
                    // this.selectUser(this.list[0])
                }
            } else {
                data.list.forEach(item=>this.list.push(item))
            }
        },
        async selectItem(item){
            if(/(details|room)/.test(this.$route.path)){
                this.link({path:'/console/chat/room',query:{chat_id:item._id}},'replace')
            } else {
                this.link({path:'/console/chat/room',query:{chat_id:item._id}})
            }
        },
    },
};
</script>

<template>
    <div class="c-list c-screen">
        <CHead :right="[{icon:(organization && organization.avatar)?organization.avatar:'icon-menu',event:'navbar-show'}]">
            <a-input v-model:value="query.keyword" placeholder="查询成员" @pressEnter="search(0)">
                <template #addonAfter>
                    <a-select v-model:value="query.role" style="width: 90px" @change="search(0)">
                        <a-select-option value="">全部</a-select-option>
                        <a-select-option value="assistant">AI</a-select-option>
                        <a-select-option value="user">人类</a-select-option>
                    </a-select>
                </template>
            </a-input>
        </CHead>
        <CList class="c-scoll" :list="list" name="name" description="remark" @checked="selectItem" @scrollBottom="search(list.length)">
            <template #head>
                <a-empty v-if="list.length==0" :description="search_ing?'正在查询数据...':'暂无会话，点击成员发起会话。'" @click="link({path:'/console/personnel'})" style="margin-top:20%" />
                <div class="tac" v-if="list.length>0"></div>
            </template>
        </CList>
    </div>
    <router-view></router-view>
</template>

<style lang="scss" scoped></style>
