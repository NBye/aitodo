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
        this.$EventBus.off('document-create',this.document_create);
        this.$EventBus.off('document-update',this.document_update);
        this.$EventBus.off('document-remove',this.document_remove);
    },
    async mounted() {
        this.$EventBus.on('document-create',this.document_create);
        this.$EventBus.on('document-update',this.document_update);
        this.$EventBus.on('document-remove',this.document_remove);
        this.query.user_id              = this.$route.query.user_id;

        this.search(0)
    },
    methods: {
        async document_create({document}){
            this.list.unshift(document);
        },
        async document_update({document}){
            this.list.forEach(item=>{
                if(item._id == document._id){
                    Object.assign(item,document);
                }
            });
        },
        async document_remove({document}){
            for(let i in this.list){
                let o =                 this.list[i];
                if(o._id==document._id){
                    this.list.splice(i,1);
                    break;
                }
            }
        },
        async toAdd(){
            this.link({path:'/console/document/create'})
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
            let {data}                  = await this.$request.post("/client/document/search",this.query,{}).finally(()=>this.search_ing = false );
            data.list.forEach(item=>{
                item.active             = item._id == this.$route.query.document_id;
            });
            if (this.query.skip==0){
                this.list               = data.list
                if(this.list.length && !this.$route.query.document_id){
                    // this.selectItem(this.list[0])
                }
            } else {
                data.list.forEach(item=>this.list.push(item))
            }
        },
        async selectItem(item){
            if(/details/.test(this.$route.path)){
                this.link({path:'/console/document/details',query:{document_id:item._id}},'replace')
            } else {
                this.link({path:'/console/document/details',query:{document_id:item._id}})
            }
        },
    },
};
</script>

<template>
    <div class="c-list c-screen">
        <CHead :right="[{icon:(organization && organization.avatar)?organization.avatar:'icon-menu',event:'navbar-show'}]">
            <a-input-search v-model:value="query.keyword" placeholder="搜索文档" @pressEnter="search(0)">
                <template v-if="IS_SYSTEM_ADMIN" #enterButton>
                    <a-button type="primary" @click="toAdd()">
                        <template #icon><PlusOutlined /></template>
                        文档
                    </a-button>
                </template>
            </a-input-search>
        </CHead>
        <CList class="c-scoll" avatar :list="list" name="title" description="abstract" @checked="selectItem" @scrollBottom="search(list.length)">
            <template #mark="{item}">
                <div v-if="!item.enabled" class="iconfont icon-jinyong"></div>
            </template>
            <template #head>
                <a-empty v-if="list.length==0" :description="search_ing?'正在查询数据...':'暂无任数据。'" style="margin-top:20%" />
                <div class="tac" v-if="list.length>0 && IS_SYSTEM_ADMIN">
                    <a-button @click="link({path:'/console/document/create',query:{user_id:query.user_id}})">
                        <template #icon><PlusOutlined /></template>
                        创建文档
                    </a-button>
                </div>
            </template>
        </CList>
    </div>
    <router-view></router-view>
</template>

<style lang="scss" scoped></style>
