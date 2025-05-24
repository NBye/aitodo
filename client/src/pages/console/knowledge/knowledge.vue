<script>
export default {
    data() {
        return {
            IS_PAGE                     : true,
            query                       : {
                keyword                 : "",
                skip                    : 0,
                size                    : 20,
                sort                    : 'updated DESC'
            },
            list                        : [],
            storage                     : {count:0,limit:0,size:0},
            search_ing                  : false,
        };
    },
    async unmounted(){
        this.$EventBus.off('knowledge-bucket-create',this.knowledge_bucket_create);
        this.$EventBus.off('knowledge-bucket-remove',this.knowledge_bucket_remove);
        this.$EventBus.off('knowledge-bucket-update',this.knowledge_bucket_update);
    },
    async mounted() {
        this.$EventBus.on('knowledge-bucket-create',this.knowledge_bucket_create);
        this.$EventBus.on('knowledge-bucket-remove',this.knowledge_bucket_remove);
        this.$EventBus.on('knowledge-bucket-update',this.knowledge_bucket_update);
        if (this.organization){
            this.search(0);
        }
    },
    methods: {
        async knowledge_bucket_create({knowledge_bucket}){
            knowledge_bucket.active     = false;
            this.list.unshift(knowledge_bucket);
        },
        async knowledge_bucket_remove({knowledge_bucket}){
            for(let i in this.list){
                let o =                 this.list[i];
                if(o._id==knowledge_bucket._id){
                    this.list.splice(i,1);
                    break;
                }
            }
        },
        async knowledge_bucket_update({knowledge_bucket}){
            this.list.forEach(item=>{
                if(item._id == knowledge_bucket._id){
                    Object.assign(item,knowledge_bucket);
                }
            })
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
            let {data}                  = await this.$request.post("/client/knowledge/bucketSearch", this.query).finally(()=>this.search_ing = false );
            data.list.forEach(item=>{
                item.active             = item._id == this.$route.query.knowledge_bucket_id;
            });
            if (this.query.skip==0){
                this.list               = data.list
                if(this.list.length && !this.$route.query.knowledge_bucket_id){
                    //可以执行默认打开
                }
            } else {
                data.list.forEach(item=>this.list.push(item))
            }
        },
        async selectItem(item){
            let query                   = {
                knowledge_bucket_id     : item._id,
                name                    : item.name,
            }
            if(/search/.test(this.$route.path)){
                this.link({path:'/console/knowledge/search',query},'replace')
            } else {
                this.link({path:'/console/knowledge/search',query})
            }
        },
        async toAddbucket(bucket={}){
            let {_id='',name='',description=''} = bucket
            let data = await this.confirm({title:'新建知识库',content:[
                {
                    name:'name',value:name,label:'名称',
                    maxlength:20,placeholder:'类型名称需要4~20个字符',reg:'/^.{4,20}$/'
                },
                {
                    name:'description',value:description,label:'描述',
                    maxlength:200,type:'textarea',placeholder:'描述需要0~200个字符',reg:'/^.{0,200}$/'
                },
            ]});
            if(data == false){
                return;
            }
            if (_id){
                let rs                      = await this.$request.post("/client/knowledge/bucketUpset", {knowledge_bucket_id:_id,...data});
                this.$EventBus.emit('knowledge-bucket-update', { knowledge_bucket:rs.data.knowledge_bucket });
            } else {
                let rs                      = await this.$request.post("/client/knowledge/bucketCreate", data);
                this.$EventBus.emit('knowledge-bucket-create', { knowledge_bucket:rs.data.knowledge_bucket });
            }
        },
    },
};
</script>

<template>
    <div class="c-list c-screen">
        <CHead :right="[{icon:(organization && organization.avatar)?organization.avatar:'icon-menu',event:'navbar-show'}]">
            <a-input-search v-model:value="query.keyword" placeholder="查询知识库" @search="search(0)">
                <template #enterButton>
                    <a-button type="primary" @click="toAddbucket()">
                        <template #icon>
                            <PlusOutlined />
                        </template>
                        库
                    </a-button>
                </template>
            </a-input-search>
        </CHead>
        <CList class="c-scoll" avatar :list="list" name="name" description="description" @checked="selectItem">
            <template #head>
                <a-empty @click="toAddbucket()" v-if="list.length==0" :description="search_ing?'正在查询数据...':'暂无任何数据。'" style="margin-top:20%" />
            </template>
        </CList>
    </div>
    <router-view></router-view>
</template>

<style lang="scss" scoped></style>
