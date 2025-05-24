<script>
import CoverImage from '../../../components/CoverImage.vue';
import Empty from '../../../components/Empty.vue';
import Time from '../../../common/utils/Time';
import locale from 'ant-design-vue/es/date-picker/locale/zh_CN';
import dayjs, { Dayjs } from 'dayjs';
export default {
    components: {CoverImage, Empty},
    data() {
        return {
            locale,
            IS_PAGE                     : true,
            PAGESHOW                    : false,
            search_ing                  : false,
            query                       : {
                time_range              : [],
                keyword                 : '',
                scene                   : '',
                status                  : 'success',
                skip                    : 0,
                size                    : 50,
                sort                    : 'created desc',
            },
            title                       : '账户明细',
            list                        : [],
            menu                        : [],
        };
    },
    async unmounted(){
    },
    async mounted() {
        
    },
    watch: {
        '$route.query': {
            handler() {
                this.query.scene            = this.$route.query.scene || '';
                this.query.status           = this.$route.query.status || 'success';
                if (this.$route.query.time_range){
                    let [s,e]               = this.$route.query.time_range.split(',');
                    this.query.time_range   = [
                        dayjs(s, 'YYYY-MM-DD HH:mm:ss'),
                        dayjs(e, 'YYYY-MM-DD HH:mm:ss'),
                    ];
                }
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
            let query                   = JSON.parse(JSON.stringify(this.query))
            if(query.time_range && query.time_range[0]){
                query.time_range[0]     = dayjs(query.time_range[0]).format('YYYY-MM-DD HH:mm:ss');
            }
            if(query.time_range && query.time_range[1]){
                query.time_range[1]     = dayjs(query.time_range[1]).format('YYYY-MM-DD HH:mm:ss');
            }
            let {data}                  = await this.$request.post("/client/payment/search", query,{}).finally(()=>this.search_ing = false );
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
            <div class="c-title">{{title}}</div>
            <div class="c-options">
                <div class="iconfont icon-more"></div>
            </div>
        </CHead>
        <CList class="c-scoll c-pd c-wd" @scrollBottom="search(list.length)" style="width:100%;">
            <template #head>
                <a-form @submit="search(0)" :model="query" name="basic" autocomplete="off" layout="inline" style="justify-content: center;text-align:center;">
                    <a-form-item label="" name="time_range">
                        <a-range-picker style="width: 220px" v-model:value="query.time_range" 
                        show-time
                       :locale="locale" @change="search(0)" />
                    </a-form-item>
                    <a-form-item label="" name="status">
                        <a-select v-model:value="query.status" style="width: 100px">
                            <a-select-option value="">全部</a-select-option>
                            <template v-for="(v,k) in PAYMENT_STATUS">
                                <a-select-option :value="k">{{v}}</a-select-option>
                            </template>
                        </a-select>
                    </a-form-item>
                    <a-form-item>
                        <a-button type="primary" html-type="submit">查询</a-button>
                    </a-form-item>
                </a-form>
            </template>
            <template #list>
                <a-list size="small" :loading="search_ing" :data-source="list">
                    <div v-if="list.length==0">
                        <a-empty :description="search_ing?'正在查询数据...':'暂无交易数据'"</a-empty>
                    </div>
                    <template #renderItem="{ item }">
                        <a-list-item>
                            <template #actions>
                                <div class="tar">
                                    <div class="amount" :class="(item.amount>0?'jia ':'jin ') + item.status">{{item.amount.toFixed(2)}}￥</div>
                                    <div v-if="item.data.after">余额 {{(item.data.after).toFixed(2)}}￥</div>
                                </div>
                            </template>
                            <a-skeleton :title="true" :loading="false" active>
                                <a-list-item-meta :description="`${item.created} ${item.remark}`">
                                    <template #title>
                                        <a class="title">{{PAYMENT_STATUS[item.status]}} {{item.status_description}}</a>
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
.amount{
    color:#999;
    &.jia{
        &.success{
            color:#d9363e;
        }
        &::before{content: '+';}
    }
    &.jin{
        &.success{
            color:#5dca28;
        }
        &::before{content: '';}
    }
}
</style>
