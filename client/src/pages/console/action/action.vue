<script>
export default {
    data() {
        return {
            IS_PAGE                     : true,
            query                       : {
                user_id                 : '',
                support                 : '',
                keyword                 : '',
                skip                    : 0,
                size                    : 50,
                sort                    : 'updated DESC'
            },
            list                        : [],
            search_ing                  : false,
        };
    },
    async unmounted(){
        this.$EventBus.off('organization-action-create',this.organization_action_create);
        this.$EventBus.off('organization-action-update',this.organization_action_update);
        this.$EventBus.off('organization-action-remove',this.organization_action_remove);
    },
    async mounted() {
        this.$EventBus.on('organization-action-create',this.organization_action_create);
        this.$EventBus.on('organization-action-update',this.organization_action_update);
        this.$EventBus.on('organization-action-remove',this.organization_action_remove);
        this.query.user_id              = this.$route.query.user_id;
        this.search(0)
    },
    methods: {
        async organization_action_create({action}){
            this.list.unshift(action);
        },
        async organization_action_update({action}){
            this.list.forEach(item=>{
                if(item._id == action._id){
                    Object.assign(item,action);
                }
            });
        },
        async organization_action_remove({action}){
            for(let i in this.list){
                let o =                 this.list[i];
                if(o._id==action._id){
                    this.list.splice(i,1);
                    break;
                }
            }
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
            let {data}                  = await this.$request.post("/client/action/search",this.query,{}).finally(()=>this.search_ing = false );
            data.list.forEach(item=>{
                item.active             = item._id == this.$route.query.action_id;
            });
            if (this.query.skip==0){
                this.list               = data.list
                if(this.list.length && !this.$route.query.action_id){
                    // this.selectItem(this.list[0])
                }
            } else {
                data.list.forEach(item=>this.list.push(item))
            }
        },
        async selectItem(item){
            if(/details/.test(this.$route.path)){
                this.link({path:'/console/action/details',query:{action_id:item._id,user_id:this.query.user_id}},'replace')
            } else {
                this.link({path:'/console/action/details',query:{action_id:item._id,user_id:this.query.user_id}})
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
                    <a-select v-model:value="query.support" style="width: 90px" @change="search(0)">
                        <a-select-option value="">全部</a-select-option>
                        <a-select-option value="PC">PC</a-select-option>
                        <a-select-option value="Mac">Mac</a-select-option>
                        <a-select-option value="Web">Web</a-select-option>
                        <a-select-option value="Android">Android</a-select-option>
                        <a-select-option value="IOS">IOS</a-select-option>
                    </a-select>
                </template>
            </a-input>
        </CHead>
        <CList class="c-scoll" avatar :list="list" name="name" description="description" @checked="selectItem" @scrollBottom="search(list.length)">
            <template #mark="{item}">
                <div v-if="!item.enabled" class="iconfont icon-jinyong"></div>
            </template>
            <template #head>
                <a-empty v-if="list.length==0" :description="search_ing?'正在查询数据...':'暂无任何能力数据，点击添加。'" @click="link({path:'/console/action/create',query:{user_id:query.user_id}})" style="margin-top:20%" />
                <div class="tac" v-if="list.length>0">
                    <a-button @click="link({path:'/console/action/create',query:{user_id:query.user_id}})">
                        <template #icon><PlusOutlined /></template>
                        添加赋能
                    </a-button>
                </div>
            </template>
        </CList>
    </div>
    <router-view></router-view>
</template>

<style lang="scss" scoped></style>
