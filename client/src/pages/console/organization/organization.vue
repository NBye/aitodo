<script>
export default {
    components: {},
    data() {
        return {
            IS_PAGE                     : true,
            query:{
                keyword                 : "",
                group                   : "2",  //1 我创建的,  2我参与的，缺省2
                skip                    : 0,
                size                    : 50,
            },
            list                        : [],
            search_ing                  : false,
        };
    },

    async unmounted() {
        this.$EventBus.off('organization-created',this.organization_created);
        this.$EventBus.off('organization-update',this.organization_update);
        this.$EventBus.off('organization-leave',this.organization_leave);
    },
    async mounted() {
        this.$EventBus.on('organization-created',this.organization_created);
        this.$EventBus.on('organization-update',this.organization_update);
        this.$EventBus.on('organization-leave',this.organization_leave);
        this.search(0)
    },
    methods: {
        async organization_created({organization}){
            this.list.unshift(organization)
        },
        async organization_update({organization}){
            for(let o of this.list){
                if(o._id==organization._id){
                    Object.assign(o,organization);
                }
            }
        },
        async organization_leave({organization}){
            for(let i in this.list){
                let o =                 this.list[i];
                if(o._id==organization._id){
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
            let {data}                  = await this.$request.post("/client/organization/search", this.query,{}).finally(()=>this.search_ing = false );
            data.list.forEach(item=>{
                item.active=item._id == this.$route.query.organization_id
            });
            if (this.query.skip==0){
                this.list               = data.list
                if(this.list.length && !this.$route.query.organization_id){
                    this.selectOrganization(this.list[0])
                }
            } else {
                data.list.forEach(item=>this.list.push(item))
            }
        },
        selectOrganization(organization){
            if(/details/.test(this.$route.path)){
                this.link({path:'/console/organization/details',query:{organization_id:organization._id}},'replace')
            } else {
                this.link({path:'/console/organization/details',query:{organization_id:organization._id}})
            }
        },
    },
};
</script>

<template>
    <div class="c-list c-screen">
        <CHead :right="[{icon:(organization && organization.avatar)?organization.avatar:'icon-menu',event:'navbar-show'}]">
            <a-input v-model:value="query.keyword" placeholder="查询我的组织" @pressEnter="search(0)">
                <template #addonAfter>
                    <a-select v-model:value="query.group" style="width: 90px" @change="search(0)">
                        <a-select-option value="2">参与的</a-select-option>
                        <a-select-option value="1">创建的</a-select-option>
                    </a-select>
                </template>
            </a-input>
        </CHead>
        <CList class="c-scoll" :list="list" description="slogan" @checked="selectOrganization" @scrollBottom="search(list.length)">
            <template #head>
                <a-empty v-if="list.length==0" :description="search_ing?'正在查询数据...':'暂无任何组织，点击创建。'" @click="link({path:'/console/organization/create'})" style="margin-top:20%" />
                <div class="tac" v-if="list.length>0">
                    <a-button @click="link({path:'/console/organization/create'})">
                        <template #icon><PlusOutlined /></template>
                        新建组织
                    </a-button>
                </div>
            </template>
        </CList>
    </div>
    <router-view></router-view>
</template>

<style lang="scss" scoped>
.c-scoll{

}
</style>
