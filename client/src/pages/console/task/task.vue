<script>
export default {
    data() {
        return {
            IS_PAGE                     : true,
            query                       : {
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
        this.$EventBus.off('task-create',this.task_create);
        this.$EventBus.off('task-remove',this.task_remove);
        this.$EventBus.off('task-update',this.task_update);
    },
    async mounted() {
        this.$EventBus.on('task-create',this.task_create);
        this.$EventBus.on('task-remove',this.task_remove);
        this.$EventBus.on('task-update',this.task_update);

        if (this.organization){
            this.search(0);
        }
    },
    methods: {
        async task_create({task}){
            this.list.unshift(task);
        },
        async task_remove({task}){
            for(let i in this.list){
                let o =                 this.list[i];
                if(o._id==task._id){
                    this.list.splice(i,1);
                    break;
                }
            }
        },
        async task_update({task}){
            this.list.forEach(item=>{
                if(item._id == task._id){
                    Object.assign(item,task);
                }
            });
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
            let {data}                  = await this.$request.post("/client/task/search", Object.assign({
                organization_id         : this.organization._id,
            },this.query),{}).finally(()=>this.search_ing = false );
            data.list.forEach(item=>{
                item.active             = item._id == this.$route.query.task_id;
            });
            if (this.query.skip==0){
                this.list               = data.list
                if(this.list.length && !this.$route.query.task_id){
                }
            } else {
                data.list.forEach(item=>this.list.push(item))
            }
        },
        async onPanelChange(e){

        },
        async toAddTask(){
            this.link({path:'/console/task/create'})
        },
        async selectTask(item){
            if(/details/.test(this.$route.path)){
                this.link({path:'/console/task/details',query:{task_id:item._id}},'replace')
            } else {
                this.link({path:'/console/task/details',query:{task_id:item._id}})
            }
        },
    },
};
</script>

<template>
    <div class="c-list c-screen">
        <CHead :right="[{icon:(organization && organization.avatar)?organization.avatar:'icon-menu',event:'navbar-show'}]">
            <a-input-search v-model:value="query.keyword" placeholder="日程任务" @pressEnter="search(0)">
                <template #enterButton>
                    <a-button type="primary" @click="toAddTask()">
                        <template #icon>
                            <PlusOutlined />
                        </template>
                        任务
                    </a-button>
                </template>
                </a-input-search>
            </CHead>

        <CList class="c-scoll" :list="list" name="title" @checked="selectTask" @scrollBottom="search(list.length)">
            <template #mark="{item}">
                <div v-if="!item.enabled" class="iconfont icon-jinyong"></div>
            </template>
            <template #desc="{item}">
                <span v-if="item.cron_enabled==true">{{crontabFormat(item.cron_expr)}}</span>
                <span v-if="item.cron_enabled!=true">{{item.schedule_time}}</span>
            </template>
            <template #head>
                <a-empty v-if="list.length==0" :description="search_ing?'正在查询数据...':'暂无任何任务数据，点击创建任务。'" @click="link({path:'/console/task/create'})" style="margin-top:20%" />
                <div class="tac" v-if="list.length>0">
                    <a-button @click="link({path:'/console/task/create'})">
                        <template #icon><PlusOutlined /></template>
                        创建任务
                    </a-button>
                </div>
            </template>
            <template #avatar="{item}">
                <div class="c-l">
                    <CoverImage class="c-list-item-container-avatar" :src="item.executor.avatar" :alt="item.executor.nickname" :width="46" :height="46"/>
                </div>
            </template>
        </CList>
    </div>
    <router-view></router-view>
</template>

<style lang="scss" scoped>
.c-l{
    display: flex;
    .c-list-item-container-avatar{
        border-radius: .3rem;
    }
}
</style>
