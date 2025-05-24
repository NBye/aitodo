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
                organization_id         : '',
                skip                    : 0,
                size                    : 50,
                sort                    : 'created desc'
            },
            list                        : [],
            list_map                    : {},
            menu                        : [],
            accept                      : '',
            uploading                   : false,
            deling                      : false,

            checked_file_list           : [],
        };
    },
    async mounted() {
    },
    watch: {
        '$route.query': {
            handler(newQuery, oldQuery) {
                this.query.organization_id  = newQuery.organization_id;
                this.query.supported        = newQuery.supported;
                this.query.keyword          = '';
                this.query.skip             = 0;
                this.search(0);
                this.PAGESHOW               = true;

                if (newQuery.supported!='other'){
                    let accept              = [];
                    newQuery.supported.split(',').forEach(s=>accept.push('.'+s));
                    this.accept             = accept.join(',');
                }else{
                    this.accept             = '';
                }
            },
            immediate: true, // 如果需要在组件加载时立即触发
        },
    },
    methods: {
        async search(skip=0){
            if(this.search_ing){
                return;
            }
            this.query.skip             = skip;
            this.search_ing             = true;
            let {data}                  = await this.$request.post("/client/file/search", this.query,{}).finally(()=>this.search_ing = false );
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
        async showMenu(item){
            let menu                    = [];
            menu.push({icon:'icon-details'    ,name:'查看详情',description:'',style:{},click:async ()=>{
                this.fileDetails(item);
            }});
            menu.push({icon:'icon-download'    ,name:'下载文件',description:'',style:{},click:async ()=>{
                window.open(this.cutImgUrl(item.url))
            }});
            menu.push({icon:'icon-bianji'    ,name:'编辑名称/备注',description:'',style:{},click:async ()=>{
                let data = await this.confirm({title:'编辑名称/备注',content:[
                    {name:'name',value:item.name,label:'文件名称',placeholder:'名称1~20个字符',reg:'/^.{20}$/'},
                    {name:'remark',value:item.remark,label:'文件备注',placeholder:'备注不超过10个字符',reg:'/^.{10}$/'},
                ]});
                if(!data){
                    return false;
                }
                await this.$request.post("/client/file/upset", {
                    file_id         : item._id,
                    organization_id : this.query.organization_id,
                    ...data
                });
                Object.assign(item,data);
            }});
            // if('pdf,doc,docx,txt,xlsx,md,ppt,pptx'.indexOf(item.type)>-1){
            //     menu.push({icon:'icon-zhishi'    ,name:'导入知识库',description:'',style:{},click:async ()=>{

            //     }});
            // }
            menu.push({type:'line'});
            menu.push({icon:'icon-tichu',name:'删除文件',description:'',style:{color:'#f00'},click:async ()=>{
                if(!await this.confirm({title:'确认删除',content:'此文件可能在其他地方被使用，请谨慎删除！',okText:'删除'})){
                    return false;
                }
                if(!await this.confirm({title:'确认删除',content:'再次确认是否删除？',okText:'删除'})){
                    return false;
                }
                await this.$request.post("/client/file/destroy", {
                    file_id         : item._id,
                    organization_id : this.query.organization_id,
                });
                let i               = this.list.indexOf(item);
                this.list.splice(i,1);
                await Time.delay(1);
                this.$EventBus.emit('file-statistics-refresh', {});
            }});
            this.$refs.as.show(menu);
        },
        async uploadNotice(file){
            this.uploading              = false;
            if (file.status=='failed'){
                return this.aMessage().error(file.reason)
            }
            await Time.delay(1);
            this.list.unshift(file);
            this.$EventBus.emit('file-statistics-refresh', {});
        },
        async checkedItme(){
            let checked_file_list       = []
            this.list.forEach(item=>{
                if(item.checked){
                    checked_file_list.push(item);
                }
            });
            this.checked_file_list      = checked_file_list;
        },
        async dels(){
            this.deling                 = true;
            if(!await this.confirm({title: `确认删除(${this.checked_file_list.length})个文件`,content:'这些文件可能在其他地方被使用，请谨慎删除！',okText:'删除'})){
                this.deling             = false;
                return false;
            }
            let count                   = 0;
            let error                   = 0;
            for(let item of this.checked_file_list){
                try{
                    await this.$request.post("/client/file/destroy", {
                        file_id         : item._id,
                    },{
                        ERROR_TIPS_ENABLE       : false,
	                    SUCCESS_TIPS_ENABLE     : false,
                    });
                    let i               = this.list.indexOf(item);
                    this.list.splice(i,1);
                    count++;
                }catch(e){
                    error++;
                }
            }
            this.deling                 = false;
            this.aMessage().info(`成功删除 ${count} 个，失败 ${error} 个。`)
            await Time.delay(1);
            this.$EventBus.emit('file-statistics-refresh', {});
        }
    },
};
</script>

<template>
    <div class="c-body c-screen am faster" :class="{show:PAGESHOW}">
        <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title">文件管理</div>
            <div class="c-options">
                <div class="iconfont icon-shanchu" v-if="checked_file_list.length" @click="dels()"></div>
                <div class="iconfont">
                    <CFile v-if="accept" ref="file" private="1" @submit="uploadNotice" @change="uploading=true" :autoSubmit="true" border="none" background="none" class="iconfont" :accept="accept" :organization_id="query.organization_id">
                        <template v-slot:initial> <div class="iconfont icon-upload run" :class="{'icon-loading':uploading}"></div></template>
                        <template v-slot:preview> <div class="iconfont icon-upload run" :class="{'icon-loading':uploading}"></div></template>
                    </CFile>
                </div>
            </div>
        </CHead>
        <CList class="c-scoll c-pd c-wd" @scrollBottom="search(list.length)" style="width:100%">
            <template #head>
                <a-input-search v-model:value="query.keyword" placeholder="请输入关键词" style="max-width: 380px;margin: 0 auto;" enter-button @search="search(0)" />
            </template>
            <template #list>
                <a-list size="small" :loading="search_ing" :item-layout="FORM_LAYOUT" :data-source="list">
                    <template #renderItem="{ item }">
                        <a-list-item>
                            <template #actions>
                                <div class="iconfont hover icon-more" @click="showMenu(item)"></div>
                            </template>
                            <a-skeleton avatar :title="true" :loading="false" active>
                                <a-list-item-meta :description="byteFormat(item.size)+ ' '+ agoFormat(item.updated) + ' ' + item.remark">
                                    <template #title>
                                        <a class="title">{{ item.name }}</a>
                                    </template>
                                    <template #avatar>
                                        <a-checkbox v-model:checked="item.checked" @change="checkedItme">
                                            <CoverImage class="avatar iconfont" v-if="['jpg','jpeg','png','gif'].indexOf(item.type)>-1" :src="item.url" :width="30" :height="30" />
                                            <div v-else class="avatar icon-other iconfont" :class="'icon-'+item.type"></div>
                                        </a-checkbox>
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
    overflow: hidden;
    display: block;
    white-space: nowrap;
    text-overflow: ellipsis;
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
