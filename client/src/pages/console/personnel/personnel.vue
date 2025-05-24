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
        this.$EventBus.off('user-update',this.organization_user_update);
        this.$EventBus.off('user-remove',this.organization_user_remove);
        this.$EventBus.off('organization-user-invite',this.organization_user_invite);
    },
    async mounted() {
        this.$EventBus.on('user-update',this.organization_user_update);
        this.$EventBus.on('user-remove',this.organization_user_remove);
        this.$EventBus.on('organization-user-invite',this.organization_user_invite);
        if (this.organization){
            this.search(0)
        }
    },
    methods: {
        async organization_user_update({user}){
            this.list.forEach(item=>{
                if(item._id == user._id){
                    Object.assign(item,user);
                }
            });
        },
        async organization_user_remove({user}){
            for(let i in this.list){
                let o =                 this.list[i];
                if(o._id==user._id){
                    this.list.splice(i,1);
                    break;
                }
            }
        },
        async organization_user_invite({user}){
            this.list.unshift(user);
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
            let {data}                  = await this.$request.post("/client/user/search", Object.assign({
                organization_id         : this.organization._id,
            },this.query),{}).finally(()=>this.search_ing = false );
            data.list.forEach(item=>{
                item.active             = item._id == this.$route.query.user_id;
                item.tags               = item.role=='assistant'?['icon-ai'] : []
            });
            if (this.query.skip==0){
                this.list               = data.list
                if(this.list.length && !this.$route.query.user_id){
                    // this.selectUser(this.list[0])
                }
            } else {
                data.list.forEach(item=>this.list.push(item))
            }
        },
        async selectUser(item){
            if(/details/.test(this.$route.path)){
                this.link({path:'/console/personnel/details',query:{user_id:item._id}},'replace')
            } else {
                this.link({path:'/console/personnel/details',query:{user_id:item._id}})
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
        <CList class="c-scoll" :list="list" name="join_info.aliasname|nickname" description="join_info.remark|slogan" tags="tags" @checked="selectUser" @scrollBottom="search(list.length)">
            <template #head>
                <a-empty v-if="list.length==0" :description="search_ing?'正在查询数据...':'暂无任何成员数据，点击创建AI员工。'" @click="link({path:'/console/personnel/create'})" style="margin-top:20%" />
                <div class="tac" v-if="list.length>0">
                    <a-button @click="link({path:'/console/personnel/create'})">
                        <template #icon><PlusOutlined /></template>
                        创建AI
                    </a-button>
                    &nbsp;
                    <a-button @click="link({path:'/console/personnel/recruit'})">
                        <template #icon><UserAddOutlined /></template>
                        聘用AI
                    </a-button>
                </div>
            </template>
            <template #avatar="{item}">
                <div class="c-l">
                    <CoverImage class="c-list-item-container-avatar" :class="{gray:isOffline(item)}" :src="item.avatar" :alt="(item.join_info && item.join_info.aliasname)?item.join_info.aliasname:item.nickname" :width="46" :height="46" :tags="item.tags" />
                </div>
            </template>
        </CList>
    </div>
    <router-view></router-view>
</template>

<style lang="scss" scoped>
.c-l{
    display: flex;
    .c-list-item-container-avatar{
        border-radius: .3rem;
    }
}
</style>
