<script>
import Time from '../../../common/utils/Time';
import locale from 'ant-design-vue/es/date-picker/locale/zh_CN';
import dayjs, { Dayjs } from 'dayjs';

export default {
    components: {},
    data() {
        return {
            locale,
            IS_PAGE                     : true,
            PAGESHOW                    : false,
            form                        : {
                task_id                 : '',
                title                   : '',
                description             : '',

                executor_user_id        : '',
                
                schedule_time           : '',
                cron_expr               : '',
                cron_enabled            : false,
                
            },
            cron_expr                   : [['*'],['*'],['*'],['*'],['*']],
            submit_ing                  : false,
            users                       : [],
        };
    },
    async mounted() {
        this.PAGESHOW                   = true;
        let {data}                      = await this.$request.post("/client/user/search", {
            organization_id             : this.organization._id,
            role                        : "assistant",  //缺省全部，assistant,user
            skip                        : 0,
            size                        : 200,
            sort                        : 'updated DESC'
        }).finally(()=>this.search_ing = false );
        data.list.forEach(item=>{
            this.users.push({
                label                   : item.nickname,
                value                   : item._id,
            })
        });
        this.loadInfo();
    },
    methods: {
        async loadInfo(){
            let task_id                 = this.$route.query.task_id;
            let {data}                  = await this.$request.post("/client/task/info", {
                task_id,
            }).finally(()=>this.loading = false);
            this.form.task_id           = data.task._id;
            this.form.title             = data.task.title;
            this.form.description       = data.task.description;
            this.form.executor_user_id  = data.task.executor_user_id;
            this.form.cron_enabled      = data.task.cron_enabled;
            this.form.schedule_time     = dayjs(data.task.schedule_time);
            this.cron_expr              = data.task.cron_expr.split(' ').map(s=>s.split(','))
        },
        async submit(data){
            this.submit_ing             = true;
            try{
                this.form.cron_expr     = this.cron_expr.map(v=>v.length?v.join(','):'*').join(' ')
                data                    = await this.$request.post("/client/task/upset",{
                    ...this.form,
                    schedule_time       : this.form.schedule_time?dayjs(this.form.schedule_time).format('YYYY-MM-DD HH:mm:ss'):'',
                });
                let task                = data.data.task;
                this.submit_ing         = false;
                this.link({path:'/console/task/details',query:{task_id:task._id}},'replace')
            } catch (e){
                this.submit_ing         = false;
                console.error(e)
            }
        },
        selectPlan(e,i){
            if(e=='*'){
               this.cron_expr[i]=['*'] 
            } else if(this.cron_expr[i].indexOf('*')>-1){
                let s = this.cron_expr[i].indexOf('*');
                this.cron_expr[i].splice(s,1)
            }
        }
    },
};
</script>

<template>
    <div class="c-body c-screen" :class="{show:PAGESHOW}">
        <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title">添加文档</div>
            <div class="c-options">
                <div class="iconfont icon-more icon-menu"></div>
            </div>
        </CHead>
        <div class="c-scoll c-pd c-wd">
            <a-form class="c-form" :layout="FORM_LAYOUT" :model="form" name="basic" :label-col="{ span: col[0] }" :wrapper-col="{ span: col[1] }" autocomplete="off" @finish="submit">
                <a-form-item label="标题" name="title" :rules="[{ required: true, pattern: /^.{4,200}$/, message: '名称需要4~200个字!' }]">
                    <a-input v-model:value="form.title" :maxlength="200" placeholder="名称需要4~200个字!" />
                </a-form-item>
                <a-form-item label="描述" name="description" :rules="[{ required: true, pattern: /^.{0,2000}$/,message: '描述需要2000个字以内!' }]">
                    <a-textarea v-model:value="form.description" :rows="4" :maxlength="2000" placeholder="描述需要2000个字以内" />
                </a-form-item>
                <a-form-item label="执行者" name="executor_user_id" :rules="[{ required: true}]">
                    <a-select 
                        show-search
                        :filter-option="(input,item)=>item.label.toLowerCase().includes(input.toLowerCase())"
                        placeholder="执行者"
                        v-model:value="form.executor_user_id"
                        :options="users"
                        >
                    </a-select>
                </a-form-item>
                
                <a-form-item label="执行时间" name="schedule_time" :rules="[{ required: true}]">
                    <a-date-picker v-model:value="form.schedule_time" 
                        show-time
                       :locale="locale"/>
                </a-form-item>
                <a-form-item label="计划" name="cron_enabled">
                    <a-switch v-model:checked="form.cron_enabled" />
                </a-form-item>
                <a-form-item v-if="form.cron_enabled" label="周期设置" help="分 时 日 月 周, 遵循 linux crontab 规则。">
                    <div class="plans">
                        <a-select class="plan"
                            @select="(e)=>selectPlan(e,0)"
                            placeholder="分钟"
                            v-model:value="cron_expr[0]"
                            :options="[{value:'*'},...Array.from({length:60}).map((_, i) => ({ value: i+''}))]"
                            mode="multiple" size="small">
                        </a-select>
                        <a-select class="plan"
                            @select="(e)=>selectPlan(e,1)"
                            placeholder="小时"
                            v-model:value="cron_expr[1]"
                            :options="[{value:'*'},...Array.from({length:24}).map((_, i) => ({ value: i+''}))]"
                            mode="multiple" size="small">
                        </a-select>
                        <a-select class="plan"
                            @select="(e)=>selectPlan(e,2)"
                            placeholder="日期"
                            v-model:value="cron_expr[2]"
                            :options="[{value:'*'},...Array.from({length:31}).map((_, i) => ({ value: (i+1)+''}))]"
                            mode="multiple" size="small">
                        </a-select>
                        <a-select class="plan"
                            @select="(e)=>selectPlan(e,3)"
                            placeholder="月份"
                            v-model:value="cron_expr[3]"
                            :options="[{value:'*'},...Array.from({length:12}).map((_, i) => ({ value: (i+1)+''}))]"
                            mode="multiple" size="small">
                        </a-select>
                        <a-select class="plan"
                            @select="(e)=>selectPlan(e,4)"
                            placeholder="星期"
                            v-model:value="cron_expr[4]"
                            :options="[{value:'*'},...Array.from({length:7}).map((_, i) => ({ value: (i)+''}))]"
                            mode="multiple" size="small">
                        </a-select>
                    </div>
                </a-form-item>
                <a-form-item :wrapper-col="{ offset: col[0], span: col[1] }">
                    <a-button type="primary" html-type="submit" :loading="submit_ing">提交</a-button>
                </a-form-item>
            </a-form>
        </div>
    </div>
</template>

<style lang="scss" scoped>

.ant-btn-link {
    padding: 0;
}
.c-form{
    padding-top:10%;
}

.plans{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 5px;
    .plan{
        
    }
}
</style>
