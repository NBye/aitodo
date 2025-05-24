<script>
import Time from '../common/utils/Time';
export default {
    props: {
        closable                        : {
            type                        : Boolean,
            default                     : true,
        },
        height                          : {
            type                        : String,
            default                     : '80%',
        },
    },
    data() {
        return {
			col: [4, 0],
            title                       : 'Agent合并',
            open                        : false,
            item                        : null,
            btnText                     : '保存',
            submiting                   : false,
            loading                     : false,
            search_ing                  : false,

            users                       : [],
            select_user_id              : null,
            select_action_id            : null,

            actions                     : [],

            titles                      : ['', ''],
            mockData                    : [],
            targetKeys                  : [],
            selectedKeys                : [],

            action                      : {agent_list:[]},
            action2                     : {agent_list:[]},

            callback                    : null,
        };
    },
    async mounted() {

    },
    methods: {
        async show({action_id},callback){
            this.callback               = callback;
            this.open                   = true;
            let action                  = await this.infoAction(action_id);
            this.action                 = action;

            this.searchUser();
            this.initMockData()

        },
        hide(){
            this.open                   = false;
            this.submiting              = false;
        },
        initMockData(){
            this.mockData               = [];
            this.targetKeys             = [];
            this.selectedKeys           = [];
            this.action.agent_list.forEach((item)=>{
                this.mockData.push({
                    key                 : item.name,
                    title               : item.description,
                    disabled            : false,
                });
            });
            this.action2.agent_list.forEach((item)=>{
                this.targetKeys.push(item.name)
                this.mockData.push({
                    key                 : item.name,
                    title               : item.description,
                    disabled            : false,
                });
            });
        },
        async infoAction(action_id){
            let {data}                  = await this.$request.post("/client/action/info", {
                action_id,
            }).finally(()=>this.loading = false);
            return data.action
        },
        async searchUser() {
            this.search_ing             = true;
            let {data}                  = await this.$request.post("/client/user/search", {
                creator_organization_id : this.organization._id,
                organization_id         : this.organization._id,
                keyword                 : '',
                role                    : "assistant",
                skip                    : 0,
                size                    : 200,
                sort                    : 'updated DESC'
            }).finally(()=>this.search_ing = false );
            this.users                  = data.list.filter(u=>u._id!=this.action.user_id);
        },
        async searchAction(){
            this.search_ing             = true;
            this.select_action_id       = null;
            let {data}                  = await this.$request.post("/client/action/search",{
                user_id                 : this.select_user_id,
            }).finally(()=>this.search_ing = false );
            this.actions                = data.list.filter(a=>a.organization_id!=this.organization.id)
        },
        async changeAction(){
            this.action2                = await this.infoAction(this.select_action_id);
            this.initMockData()
        },
        async onSubmit(t){
            if(!await this.confirm({title:'确定合并？',content:t==1?`注意: 保存当前智能体的能力`:'注意: 保存'})){
                return ;
            }
            let action_id,action;
            let agent_list              = [];
            this.action.agent_list.concat(this.action2.agent_list).forEach(a=>{
                if((t==1 && this.targetKeys.indexOf(a.name)<0) || (t!=1 && this.targetKeys.indexOf(a.name)>-1)){
                    agent_list.push(a);
                }
            });
            if(t==1){
                action                  = this.action;
                action_id               = this.action._id;
            } else {
                action_id               = this.select_action_id;
                action                  = this.action2;
            }
            await this.$request.post("/client/action/saveAgent", {
                action_id,
                agent_list,
            });
            Object.assign(action,await this.infoAction(action_id))
            if(typeof this.callback=='function'){
                this.callback({action})
            }
        }
    },
}
</script>

<template>
    <a-drawer :title="title" :height="height" placement="bottom" :closable="closable" :maskClosable="closable" v-model:open="open" :get-container="false" :maskStyle="{background: 'rgba(255, 255, 255, 0.0)'}">
        <template #extra> </template>
        <div class="action-merge-body">
            <div class="searchs">
                <div class="b l">当前: {{action.name}}</div>
                <div class="c"></div>
                <div class="b r">
                    <a-select v-model:value="select_user_id" style="width: 50%" :options="users.map(u=>({label:u.nickname,value:u._id}))" @change="searchAction()" placeholder="选择智能体"></a-select>
                    <a-select v-model:value="select_action_id" style="width: 50%" :options="actions.map(a=>({label:a.name,value:a._id}))" @change="changeAction()" placeholder="选择能力"></a-select>
                </div>
            </div>
            <a-transfer v-model:target-keys="targetKeys" v-model:selected-keys="selectedKeys" :data-source="mockData" :titles="titles" :render="item => item.title" />

            <div class="searchs">
                <div class="b l">
                    <a-button type="primary" @click="onSubmit(1)" :loading="submiting" size="small">{{btnText}}</a-button>
                </div>
                <div class="c"></div>
                <div class="b r">
                    <a-button :disabled="!select_action_id" type="primary" @click="onSubmit(2)" :loading="submiting" size="small">{{btnText}}</a-button>
                </div>
            </div>
        </div>
    </a-drawer>
</template>

<style lang="scss" scoped>
.action-merge-body {
    height:100%;
    .searchs{
        display: flex;
        justify-content: space-between;
        height: 40px;
        align-items: center;
        .b{
            width: calc(50% - 20px);
            text-align: center;
        }
    }

    :deep(.ant-transfer) {
        height: calc(100% - 40px * 2);
        .ant-transfer-list {
            width: calc(50% - 20px);
            flex: none;
            height:100%;
        }
    }
}
</style>
