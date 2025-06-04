<script>
import CoverImage from '../../../components/CoverImage.vue';
import Empty from '../../../components/Empty.vue';
import Time from '../../../common/utils/Time';
export default {
    components: {CoverImage, Empty},
    data() {
        return {
            IS_PAGE                     : true,
            PAGESHOW                    : false,
            search_ing                  : false,
            query                       : {
                keyword                 : '',
                skip                    : 0,
                size                    : 50,
                sort                    : 'created desc',
                knowledge_bucket_id     : '',
            },
            title                       : '',
            list                        : [],
            list_map                    : {},
            menu                        : [],
            accept                      : '',
            uploading                   : false,
            deling                      : false,

            checked_list                : [],
        };
    },
    async unmounted(){
        this.$EventBus.off('knowledge-create',this.knowledge_create);
        this.$EventBus.off('knowledge-remove',this.knowledge_remove);
        this.$EventBus.off('knowledge-update',this.knowledge_update);
    },
    async mounted() {
        this.$EventBus.on('knowledge-create',this.knowledge_create);
        this.$EventBus.on('knowledge-remove',this.knowledge_remove);
        this.$EventBus.on('knowledge-update',this.knowledge_update);
    },
    watch: {
        '$route.query': {
            handler(newQuery, oldQuery) {
                this.query.knowledge_bucket_id  = newQuery.knowledge_bucket_id;
                this.title                  = newQuery.name;
                this.query.keyword          = '';
                this.query.skip             = 0;
                this.search(0);
                this.PAGESHOW               = true;
            },
            immediate: true, // 如果需要在组件加载时立即触发
        },
    },
    methods: {
        async knowledge_create({knowledge}){
            this.list.unshift(knowledge);
        },
        async knowledge_remove({knowledge}){
            for(let i in this.list){
                let o =                 this.list[i];
                if(o._id==knowledge._id){
                    this.list.splice(i,1);
                    break;
                }
            }
        },
        async knowledge_update({knowledge}){
            this.list.forEach(item=>{
                if(item._id == knowledge._id){
                    Object.assign(item,knowledge);
                }
            })
        },
        async search(skip=0){
            if(this.search_ing){
                return;
            }
            this.query.skip             = skip;
            this.search_ing             = true;
            let {data}                  = await this.$request.post("/client/knowledge/search", this.query,{}).finally(()=>this.search_ing = false );
            data.list.forEach((item)=>{
                item.checked            = false;
            });
            if (this.query.skip==0){
                this.list               = data.list;
            } else {
                data.list.forEach((item)=>{
                    this.list.push(item);
                });
            }
        },
        async toAddKnowledge(){
            this.link({path:'/console/knowledge/publish',query:{knowledge_bucket_id:this.query.knowledge_bucket_id}})
        },
        async editKnowledgeBucket(){
            let {data}                  = await this.$request.post("/client/knowledge/bucketInfo", {
                knowledge_bucket_id     : this.query.knowledge_bucket_id,
            });
            let {_id='',name='',description=''} = data.knowledge_bucket
            data = await this.confirm({title:'编辑知识库',content:[
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
            let rs                      = await this.$request.post("/client/knowledge/bucketUpset", {
                knowledge_bucket_id:_id,...data
            });
            this.title                  = data.name;
            this.$EventBus.emit('knowledge-bucket-update', { knowledge_bucket:rs.data.knowledge_bucket });
        },
        async showBucket(){
            this.$refs.as.show([
                {icon:'icon-zhishi2'     ,name:'添加文本知识',description:'',style:{},click:async ()=>{
                    this.toAddKnowledge()
                }},
                {icon:'icon-bianji'      ,name:'编辑库名称',description:'',style:{},click:async ()=>{
                    this.editKnowledgeBucket()
                }},
                {type:'line'},
                {icon:'icon-dissolution',name:'销毁当前知识库',description:'',style:{color:'#f00'},click:async ()=>{
                    if(! await this.confirm({title:'确认删除当前知识库？',content:'删除知识库，会将旗下所有知识内容全部清空，请确认删除？'})){
                        return;
                    }
                    await this.$request.post("/client/knowledge/bucketDestroy", {knowledge_bucket_id:this.query.knowledge_bucket_id});
                    this.$EventBus.emit('knowledge-bucket-remove', { knowledge_bucket:{_id:this.query.knowledge_bucket_id} });
                    this.linkBack()
                }},
            ])
        },
        async showMenu(item){
            this.$refs.as.show([
                {icon:'icon-bianji'    ,name:'编辑知识',description:'',style:{},click:async ()=>{
                    let rs              = await this.$request.post("/client/knowledge/info", {
                        knowledge_id    : item._id
                    });
                    let {_id,text}          = rs.data.knowledge;
                    let data = await this.confirm({title:'修改知识片段',content:[
                        {
                            name:'text',value:text,label:'片段文本',type:'textarea',style:{height:'400px'},
                            maxlength:256,type:'textarea',placeholder:'片段文本需要1~256个字符',reg:'/^.{0,256}$/'
                        },
                    ]});
                    if(data == false){
                        return;
                    }
                    rs                  = await this.$request.post("/client/knowledge/upset", {
                        knowledge_id    : _id,
                        ...data
                    });
                    this.$EventBus.emit('knowledge-update', { knowledge:rs.data.knowledge });
                }},
                {type:'line'},
                {icon:'icon-tichu',name:'删除知识片段',description:'',style:{color:'#f00'},click:async ()=>{
                    this.delKnowledge(item)
                }},
            ]);
        },
        async delKnowledge(item,options={}){
            if(options.ERROR_TIPS_ENABLE===undefined && !await this.confirm({title:'确认删除',content:'删除不可恢复，请谨慎操作。',okText:'删除'})){
                return false;
            }
            await this.$request.post("/client/knowledge/destroy", {
                knowledge_id    : item._id,
            },options);
            this.$EventBus.emit('knowledge-remove', {knowledge:item});
        },
        async checkedItme(){
            let checked_list       = []
            this.list.forEach(item=>{
                if(item.checked){
                    checked_list.push(item);
                }
            });
            this.checked_list           = checked_list;
        },
        async dels(){
            this.deling                 = true;
            if(!await this.confirm({title: `确认删除(${this.checked_list.length})个知识片段？`,content:'删除不可恢复，请谨慎删除！',okText:'删除'})){
                this.deling             = false;
                return false;
            }
            let count                   = 0;
            let error                   = 0;
            for(let item of this.checked_list){
                try{
                    await this.delKnowledge(item,{
                        ERROR_TIPS_ENABLE       : false,
	                    SUCCESS_TIPS_ENABLE     : false,
                    })
                    count++;
                }catch(e){
                    error++;
                }
            }
            this.deling                 = false;
            this.aMessage().info(`成功删除 ${count} 个，失败 ${error} 个。`)
            this.checked_list           = []
        },

        async beforeUpload(){
            return true;
        },
        async uploadSubmit({ file, onSuccess, onError }){
            console.log(file)
            this.uploading              = true
            let {data}                  = await this.$request.post("/client/knowledge/upload", {
                file,
                knowledge_bucket_id     : this.query.knowledge_bucket_id,
            },{headers:{'Content-Type': 'multipart/form-data'}}).finally(()=>{
                this.uploading           = false;
                this.search();
            })
        },
    },
};
</script>

<template>
    <div class="c-body c-screen am faster" :class="{show:PAGESHOW}">
        <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title" @click="editKnowledgeBucket">知识管理：{{title}}</div>
            <div class="c-options">
                <div class="iconfont icon-shanchu" v-if="checked_list.length" @click="dels()"></div>
                
                <a-upload v-if="!uploading" name="file" :showUploadList="false" :action="''" :before-upload="beforeUpload" :max-count="1" :custom-request="uploadSubmit" accept=".docx,.pdf">
                    <div class="iconfont icon-upload" title="导入文件docx,pdf"></div>
                </a-upload>
                <div v-if="uploading" class="iconfont icon-loading run"></div>

                <div class="iconfont icon-fabu" @click="toAddKnowledge()"></div>
                <div class="iconfont icon-more" @click="showBucket()"></div>
            </div>
        </CHead>
        <CList class="c-scoll c-pd c-wd" @scrollBottom="search(list.length)" style="width:100%">
            <template #head>
                <a-input-search :loading="search_ing" v-model:value="query.keyword" placeholder="文本向量检索" style="max-width: 380px;margin: 0 auto;" enter-button @search="search(0)" />
            </template>
            <template #list>
                <a-list size="small" :loading="search_ing" :item-layout="FORM_LAYOUT" :data-source="list">
                    <div v-if="list.length==0" class="tac">
                        <a-upload v-if="!uploading" name="file" :showUploadList="false" :action="''" :before-upload="beforeUpload" :max-count="1" :custom-request="uploadSubmit" accept=".docx,.pdf">
                            <a-empty :description="search_ing?'正在查询数据...':'暂无知识数据，点击添加。'"></a-empty>
                        </a-upload>
                        <a-empty v-else :description="search_ing?'正在查询数据...':'正在上传中...'"></a-empty>
                    </div>
                    <template #renderItem="{ item }">
                        <a-list-item>
                            <template #actions>
                                <div class="iconfont hover icon-more" @click="showMenu(item)"></div>
                            </template>
                            <a-skeleton avatar :title="true" :loading="false" active>
                                <a-list-item-meta :description="`Tokens: ${item.query_tokens} Size: ${byteFormat(item.size)} ${agoFormat(item.updated)}`">
                                    <template #title>
                                        <a class="title">{{ item.text }}</a>
                                    </template>
                                    <template #avatar>
                                        <a-checkbox v-model:checked="item.checked" @change="checkedItme"></a-checkbox>
                                    </template>
                                </a-list-item-meta>
                            </a-skeleton>
                        </a-list-item>
                    </template>
                </a-list>
            </template>
        </CList>

        <ActionSheet ref="as" :list="menu" />
    </div>
</template>

<style lang="scss" scoped>

.title{
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    overflow: hidden;
    text-overflow: ellipsis;
    word-wrap: break-word;
}
.avatar.iconfont{
    width: 30px;
    height: 30px;
    font-size: 30px;
    margin-top: 6px;
    display: flex;
    align-items: center;
    justify-content: flex-start;
}
</style>
