<script>
export default {
    data() {
        return {
            IS_PAGE                     : true,
            query                       : {
                keyword                 : "",
            },
            list                        : [
                // {icon:'icon-voice',type:'voice_clone',name:'声音复刻',description:'语音克隆时，复刻的原始声音配置数据。'}
            ],
            search_ing                  : false,
        };
    },
    async unmounted(){
    },
    async mounted() {
        if (this.organization){
            this.search(0);
        }
    },
    methods: {
        async search(skip=0){
            this.search_ing             = true;
            let {data}                  = await this.$request.post("/client/database/groups").finally(()=>this.search_ing = false );
            this.list                   = data.list;
        },
        async selectItem(item){
            let query                   = {
                organization_id         : this.query.organization_id,
                type                    : item.type,
            }
            if(/search/.test(this.$route.path)){
                this.link({path:'/console/database/search',query},'replace')
            } else {
                this.link({path:'/console/database/search',query})
            }
        },
    },
};
</script>

<template>
    <div class="c-list c-screen">
        <CHead :right="[{icon:(organization && organization.avatar)?organization.avatar:'icon-menu',event:'navbar-show'}]">
            <a-input-search v-model:value="query.keyword" placeholder="数据库"> </a-input-search>
        </CHead>
        <CList class="c-scoll" :list="list" avatar="icon" name="name" description="description" @checked="selectItem">
            <template #head>
                <a-empty v-if="list.length==0" :description="search_ing?'正在查询数据...':'暂无任何成员数据。'" style="margin-top:20%" />
            </template>
        </CList>
    </div>
    <router-view></router-view>
</template>

<style lang="scss" scoped></style>
