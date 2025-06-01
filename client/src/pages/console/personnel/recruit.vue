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
                role                    : 'assistant',
                public                  : true,
            },
            title                       : '',
            list                        : [],
            list_map                    : {},
            menu                        : [],
            accept                      : '',
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
            handler() {
                this.query.keyword          = '';
                this.query.skip             = 0;
                this.search(0);
                this.PAGESHOW               = true;
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
            let {data}                  = await this.$request.post("/client/user/search", {
                ...this.query,
                invited_organization_id : this.organization._id,
            }).finally(()=>this.search_ing = false );
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
    },
};
</script>

<template>
    <div class="c-body c-screen am faster" :class="{show:PAGESHOW}">
        <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title" @click="editKnowledgeBucket">招聘AI员工</div>
            <div class="c-options">
                <div class="iconfont icon-shanchu" v-if="checked_list.length" @click="dels()"></div>
                <div class="iconfont icon-more" @click="showBucket()"></div>
            </div>
        </CHead>
        <CList class="c-scoll c-pd c-wd" @scrollBottom="search(list.length)" style="width:100%">
            <template #head>
                <a-input-search :loading="search_ing" v-model:value="query.keyword" placeholder="搜索用户" style="max-width: 380px;margin: 0 auto;" enter-button @search="search(0)">
                    <template #addonBefore>
                        <a-select v-model:value="query.role" style="width: 100px" @change="search(0)">
                            <a-select-option value="assistant">AI·用户</a-select-option>
                            <a-select-option value="user">人类用户</a-select-option>
                        </a-select>
                    </template>
                </a-input-search>
            </template>
            <template #list>
                <a-list size="small" :loading="search_ing" :data-source="list">
                    <div v-if="list.length==0">
                        <a-empty :description="search_ing?'正在查询数据...':'暂无知识数据。'"></a-empty>
                    </div>
                    <template #renderItem="{ item }">
                        <a-list-item @click="link({path:'/console/personnel/resume',query:{user_id:item._id}})">
                            <template #actions>
                                <div class="iconfont hover icon-yijiaru" v-if="item.join_info"></div>
                                <div class="iconfont hover icon-look a" v-else></div>
                            </template>
                            <a-skeleton avatar :title="true" :loading="false" active>
                                <a-list-item-meta :description="`${item.slogan}`">
                                    <template #title>
                                        <div class="title">
                                            <div>{{ item.nickname }}</div>
                                        </div>
                                    </template>
                                    <template #avatar>
                                        <CoverImage class="avatar" :src="item.avatar" :width="30" :height="30" :alt="item.nickname" :tags="item.tags" />
                                    </template>
                                </a-list-item-meta>
                            </a-skeleton>
                        </a-list-item>
                    </template>
                </a-list>
            </template>
        </CList>

        <ActionSheet ref="as" />
    </div>
</template>

<style lang="scss" scoped>
.iconfont.a{
    color:var(--ant-color-primary)
}
.avatar{
    border: solid 1px #eee;
    border-radius: 50%;
}
.title{
    display: flex;
    justify-content: space-between;
}
</style>
