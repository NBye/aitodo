<script>
export default {
    data() {
        return {
            IS_PAGE                     : true,
            query                       : {
                organization_id         : "",
            },
            list                        : [],
            storage                     : {count:0,limit:0,size:0},
            search_ing                  : false,
        };
    },
    async unmounted(){
        this.$EventBus.off('file-statistics-refresh',this.file_statistics_refresh);
    },
    async mounted() {
        this.$EventBus.on('file-statistics-refresh',this.file_statistics_refresh);
        if (this.organization){
            this.query.organization_id      = this.organization._id;
            this.search(0);
        }
    },
    methods: {
        async file_statistics_refresh(){
            this.search(0);
        },
        async search() {
            if(this.search_ing){
                return;
            }
            this.search_ing             = true;
            let {data}                  = await this.$request.post("/client/file/statistics", Object.assign({},this.query),{}).finally(()=>this.search_ing = false );
            data.list.forEach(item=>{
                item.active             = this.$route.query.supported==item.supported;
            });
            this.list                   = data.list;
            this.storage                = data.storage;
        },
        async selectItem(item){
            let query                   = {
                organization_id         : this.query.organization_id,
                supported               : item.supported,
            }
            if(/search/.test(this.$route.path)){
                this.link({path:'/console/file/search',query},'replace')
            } else {
                this.link({path:'/console/file/search',query})
            }
        },
        async switchGroup(){
            this.link({path:'/console/file'},'replace');
            this.search();
        }
    },
};
</script>

<template>
    <div class="c-list c-screen">
        <CHead :right="[{icon:(organization && organization.avatar)?organization.avatar:'icon-menu',event:'navbar-show'}]">
            <div class="w100 tac" v-if="organization">
                <a-radio-group v-model:value="query.organization_id" @change="switchGroup" class="w100">
                    <a-radio-button :value="organization._id">组织的</a-radio-button>
                    <a-radio-button :value="''">个人的</a-radio-button>
                </a-radio-group>
                <a-progress :percent="Math.ceil((storage.limit?storage.size/storage.limit:0)*100)" />
            </div>
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
