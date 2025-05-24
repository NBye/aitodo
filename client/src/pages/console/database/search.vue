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
                skip                    : 0,
                type                    : '',
                size                    : 50,
                sort                    : 'created desc'
            },
            list                        : [],
            menu                        : [],
            uploading                   : false,
            deling                      : false,

            checked_list                : [],
        };
    },
    async mounted() {
    },
    watch: {
        '$route.query': {
            handler(newQuery, oldQuery) {
                this.query.type             = newQuery.type;
                this.query.skip             = 0;
                this.PAGESHOW               = true;
                this.search(0);
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
            let {data}                  = await this.$request.post("/client/database/search", this.query,{}).finally(()=>this.search_ing = false );
            data.list.forEach((item)=>{
                item.checked            = false;
                if(item.type=='voice_clone'){
                    item.icon           = 'icon-voice'
                }else{
                    item.icon           = 'icon-database'
                }
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
                let { data } = await this.$request.post("/client/database/info", {
                    data_id: item._id,
                });
                let h = this.aH();
                let content = JSON.stringify(JSON.parse(data.content),null,4)
                this.aModal().info({
                    okText: '确定',
                    title: '数据详情',
                    content: h('div', { style: { display: 'flex', 'width': '100%', 'margin-left': '-30px' } }, [
                        h('div', {}, [
                            h('div', { class: 'iconfont ' + item.icon, style: { width: '40px', fontSize: '42px', display: 'flex', justifyContent: 'center' } })
                        ]),
                        h('div', { style: { padding: '0.5rem',width: '100%'} }, [
                            h('p', '数据ID ：' + item._id),
                            h('pre', { style: { padding: '0.5rem',width: '100%'} }, content),
                        ]),
                    ]),
                });
            }});

            menu.push({icon:'icon-bianji'    ,name:'编辑名称',description:'',style:{},click:async ()=>{
                let data = await this.confirm({title:'编辑名称',content:[
                    {name:'remark',value:item.remark,label:'数据名称',placeholder:'名称不超过20个字符',reg:'/^.{10}$/'},
                ]});
                if(!data){
                    return false;
                }
                await this.$request.post("/client/database/upset", {
                    data_id         : item._id,
                    ...data
                });
                Object.assign(item,data);
            }});
            menu.push({type:'line'});
            menu.push({icon:'icon-tichu',name:'删除数据',description:'',style:{color:'#f00'},click:async ()=>{
                if(!await this.confirm({title:'确认删除',content:'此数据可能在其他地方被使用，请谨慎删除！',okText:'删除'})){
                    return false;
                }
                if(!await this.confirm({title:'确认删除',content:'再次确认是否删除？',okText:'删除'})){
                    return false;
                }
                await this.$request.post("/client/database/destroy", {
                    data_id         : item._id,
                    organization_id : this.query.organization_id,
                });
                let i               = this.list.indexOf(item);
                this.list.splice(i,1);
            }});
            this.$refs.as.show(menu);
        },
        async checkedItme(){
            let checked_list       = []
            this.list.forEach(item=>{
                if(item.checked){
                    checked_list.push(item);
                }
            });
            this.checked_list      = checked_list;
        },
        async dels(){
            this.deling                 = true;
            if(!await this.confirm({title: `确认删除(${this.checked_list.length})个数据`,content:'这些数据可能在其他地方被使用，请谨慎删除！',okText:'删除'})){
                this.deling             = false;
                return false;
            }
            let count                   = 0;
            let error                   = 0;
            for(let item of this.checked_list){
                try{
                    await this.$request.post("/client/database/destroy", {
                        data_id         : item._id,
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
        }
    },
};
</script>

<template>
    <div class="c-body c-screen am faster" :class="{show:PAGESHOW}">
        <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title">数据管理</div>
            <div class="c-options">
                <div class="iconfont icon-shanchu" v-if="checked_list.length" @click="dels()"></div>
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
                                <a-list-item-meta :description="item.updated">
                                    <template #title>
                                        <a class="title" @click="checkedItme(item.checked=!item.checked)">{{ item.remark }}</a>
                                    </template>
                                    <template #avatar>
                                        <a-checkbox v-model:checked="item.checked" @change="checkedItme"> </a-checkbox>
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
