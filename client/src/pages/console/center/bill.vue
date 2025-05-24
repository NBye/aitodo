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
                year                    : '',
                keyword                 : '',
                status                  : '',
                skip                    : 0,
                size                    : 50,
                sort                    : 'month desc',
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
            if(query.year){
                query.year              = dayjs(query.year).format('YYYY');
            }
            let {data}                  = await this.$request.post("/client/commission/search", query,{}).finally(()=>this.search_ing = false );
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

        toDetials(item){
            console.log(item.month)
            let [y,m]                   = item.month.split('-')
            let d                       = new Date(y, m, 0).getDate()
            let stime                   = `${y}-${m}-01 00:00:00`;
            let etime                   = `${y}-${m}-${d>9?d:('0'+d)} 23:59:59`;
            this.link({path:'/console/center/payment',query:{
                time_range      : `${stime},${etime}`,
                status          : 'success',
                scene           : 'commission'
            }});
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
                    <a-form-item label="" name="status">
                        <a-select v-model:value="query.status" @change="search(0)" placeholder="状态" style="width: 100px">
                            <a-select-option value="">状态</a-select-option>
                            <template v-for="(v,k) in COMMISSION_BILL_STATUS">
                                <a-select-option :value="k">{{v}}</a-select-option>
                            </template>
                        </a-select>
                    </a-form-item>
                    <a-form-item label="" name="year">
                        <a-date-picker v-model:value="query.year" picker="year" :locale="locale" @change="search(0)"/>
                    </a-form-item>
                    <a-form-item>
                        <a-button type="primary" html-type="submit">查询</a-button>
                    </a-form-item>
                </a-form>
            </template>
            <template #list>
                <a-list size="small" :loading="search_ing" :data-source="list">
                    <div v-if="list.length==0">
                        <a-empty :description="search_ing?'正在查询数据...':'暂无账单数据'"</a-empty>
                    </div>
                    <template #renderItem="{ item }">
                        <a-list-item>
                            <template #actions>
                                <a @click="toDetials(item)">明细</a>
                            </template>
                            <a-skeleton :title="true" :loading="false" active>
                                <a-list-item-meta :description="COMMISSION_BILL_STATUS[item.status]">
                                    <template #title>
                                        <a class="title">{{item.remark}}</a>
                                    </template>
                                </a-list-item-meta>
                            </a-skeleton>
                            <div class="amount" :class="item.status">{{item.amount.toFixed(2)}}￥</div>
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
    &.unsettled{
        color: var(--ant-color-primary);
    }
    &.settled{
        color:#999999;
    }
}
</style>
