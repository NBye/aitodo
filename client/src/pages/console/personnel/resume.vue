<script>
import Time from '../../../common/utils/Time';
export default {
    data() {
        return {
            IS_PAGE                     : true,
            PAGESHOW                    : false,
            item                        : null,
            loading                     : false,
            storage_count               : 0,

            introduction_html           : '',

            hire_staff_ok               : false,
            salary_list                 : [
                {m:'y', s:'年'},
                {m:'m', s:'月'},
                {m:'d', s:'日'},
                {m:'h', s:'小时'},
            ]
        };
    },
    async mounted() {
    },
    watch: {
        '$route.query': {
            handler() {
                this.loadInfo()
                this.PAGESHOW          = true;
            },
            immediate: true, // 如果需要在组件加载时立即触发
        },
    },
    methods: {
        async loadInfo(){
            this.item                   = null;
            let user_id                 = this.$route.query.user_id;
            let {data}                  = await this.$request.post("/client/user/info", {
                user_id,
                organization_id         : this.organization._id,
            }).finally(()=>this.loading = false);
            this.item                   = data.user;
            this.storage_count          = data.storage_count;
            this.item.tags              = this.item.role=='assistant' ? ['icon-ai'] : []
            this.introduction_html      = await this.md2html(this.item.introduction)

            for(let t in this.item.salary){
                let b = this.item.salary[t];
                if(b.enable && b.price>=0){
                    this.hire_staff_ok  = true;
                    break;
                }
            }
        },

        async toRemove(){
            let content                 = '移除后可以再次邀约加入。'
            if(!await this.confirm({title:'确定移除',content})){
                return;
            }
            this.loading                = true;
            await this.$request.post("/client/organization/leave", {
                organization_id         : this.organization._id,
                user_id                 : this.item._id,
            });
            this.$EventBus.emit('user-remove', { user:this.item });
            await Time.delay(1);
            this.loadInfo();
            this.loading                = false;
        },
        async inviteOrganization(){
            this.loading                = true;
            await this.$request.post("/client/organization/invite", {
                organization_id         : this.organization._id,
                user_id                 : this.item._id,
            });
            this.$EventBus.emit('organization-user-invite', { user:this.item });
            await Time.delay(1);
            this.loadInfo();
            this.loading                = false;
        },
        async fireStaff(){
            if(this.loading){
                return;
            }
            let content                 = `解除关系后，他将不在继续工作，若重新雇佣则会恢复工作。`;
            if(!await this.confirm({title:'确定解除雇佣关系？',content})){
                return;
            }
            this.loading                = true;
            try {
                await this.$request.post("/client/organization/leave", {
                    organization_id     : this.organization._id,
                    user_id             : this.item._id,
                });
                this.$EventBus.emit('user-remove', { user:this.item });
                await Time.delay(1);
                this.loadInfo();
            } catch(e) {}
            this.loading                = false;
        },


        async hireStaff() {
            let menu                    = [];
            for(let t in this.item.salary){
                let b = this.item.salary[t];
                if(b.enable && b.price>=0){
                    menu.push({
                        after           : 'icon-guyong' ,
                        name            : `${b.price?(b.price.toFixed(2)+'￥'):'免费'}/${this.SALARY_UNIT[t]}`,
                        description     : ``,
                        style           : {},
                        click           :async ()=>{
                            let type    = t;
                            let price   = b.price;
                            if(this.loading){
                                return;
                            }
                            let content                 = `${price.toFixed(2)}￥/${this.SALARY_UNIT[type]}, 系统会按周期自动从组织账户中扣除费用。`;
                            if(!await this.confirm({title:'确定雇佣？',content})){
                                return;
                            }
                            this.loading                = true;
                            try {
                                await this.$request.post("/client/organization/invite", {
                                    organization_id     : this.organization._id,
                                    user_id             : this.item._id,
                                    salary              : {type,price},
                                },{
                                    SUCCESS_TIPS_ENABLE : false,
                                    ERROR_TIPS_ENABLE   : false
                                }).catch(async e=>{
                                    if(e.code==405 && await this.confirm({title:e.message,content:'点击确认查看账户详情？'})){
                                        this.link({path:'/console/center/organization',query:{organization_id:this.organization._id}})
                                    }else if(e.code!=405 && e.code!=1) {
                                        this.aMessage().error(e.message);
                                    }
                                    throw e;
                                });
                                this.$EventBus.emit('organization-user-invite', { user:this.item });
                                await Time.delay(1);
                                this.loadInfo();
                                this.aMessage().success('雇佣成功')
                            } catch(e) {}
                            this.loading                = false;

                        }
                    });
                }
            }
            if(menu.length){
                menu.push({
                    type                : 'description',
                    description         : `雇佣成功后，会从当前组织账户中定期扣除费用，若账户余额不足，AI将不在工作。充值后自动恢复工作。`,
                });
            } else {
                menu.push({
                    type                : 'description',
                    description         : `该AI还未设置雇佣金额，请等待...`,
                });
            }
            this.$refs.as.show(menu,'聘用方式')
        },
        async toSettlement(){
            let menu                   = [];
            for(let t in this.item.salary){
                let b = this.item.salary[t];
                if(b.enable && b.price>=0){
                    menu.push({
                        after           : 'icon-zhangdan' ,
                        name            : `${b.price?(b.price.toFixed(2)+'￥'):'免费'}/${this.SALARY_UNIT[t]}`,
                        description     : ``,
                        style           : {},
                        click           :async (item)=>{
                            let content                     = `支付 ${b.price.toFixed(2)}￥,续期 1${this.SALARY_UNIT[t]} 工作时间，请确定。`;
                            if (!await this.confirm({title:'确定续期？',content})){
                                return;
                            }
                            let rs                          = await this.$request.post("/client/user/salary_settlement", Object.assign({
                                user_id                     : this.item._id,
                                organization_id             : this.organization._id,
                                salary                      : {
                                    type                    : t,
                                    price                   : b.price
                                }
                            }));
                            let {user}                      = rs.data;
                            Object.assign(this.item,user);
                            this.$EventBus.emit('user-update', {user});
                        }
                    });
                }
            }
            if(menu.length){
                menu.push({
                    type                : 'description',
                    description         : `雇佣成功后，会从当前组织账户中定期扣除费用，若账户余额不足，AI将不在工作。充值后自动恢复工作。`,
                });
            } else {
                menu.push({
                    type                : 'description',
                    description         : `该AI还未设置雇佣金额，请等待...`,
                });
            }
            this.$refs.as.show(menu,'续期方式')
        },
    },
};
</script>

<template>
    <div class="c-body c-screen am faster" :class="{show:PAGESHOW}">
        <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title">成员详情</div>
            <div class="c-options">
                <div class="iconfont icon-more icon-menu"></div>
            </div>
        </CHead>
        <div class="c-scoll c-pd c-wd">
            <a-empty v-if="!item && loading" description="数据加载中..." />
            <div class="c-form pr" v-if="item">
                <div class="head">
                    <div>
                        <CoverImage class="logo" :src="item.avatar" :width="100" :height="100" :alt="item.nickname" :tags="item.tags" />
                    </div>
                    <div class="name">{{item.nickname}}</div>
                    <div class="slogan">{{item.slogan || (item.join_info?item.join_info.remark:'')}}</div>
                    <div>
                        <a-space :size="16">
                            <template v-if="item.role=='user'">
                                <a-button v-if="item.join_info" type="link" @click="toRemove()" :loading="loading">
                                    移除<template #icon><UserDeleteOutlined /></template>
                                </a-button>
                                <a-button v-else type="link" @click="inviteOrganization()" :loading="loading">
                                    邀请<template #icon><UserAddOutlined /></template>
                                </a-button>
                            </template>
                            <template v-if="item.role!='user'">
                                <a-button v-if="item.join_info" type="link" @click="fireStaff()" :loading="loading" :disabled="item.creator_organization_id==organization._id">
                                    解雇<template #icon><UserDeleteOutlined /></template>
                                </a-button>
                                <a-button v-else type="link" @click="hireStaff()" :disabled="!hire_staff_ok" :loading="loading">
                                    雇佣<template #icon><UserAddOutlined /></template>
                                </a-button>
                            </template>
                        </a-space>
                    </div>
                </div>
                <a-divider class="line" />
                <a-row class="info">
                    <a-col :span="8" class="tal"><p>生日</p></a-col>
                    <a-col :span="8"><p>性别</p></a-col>
                    <a-col :span="8" class="tar"><p>角色</p></a-col>
                </a-row>
                <a-row class="info">
                    <a-col :span="8" class="tal">
                        <p>{{item.birthday || '未知'}}</p>
                    </a-col>
                    <a-col :span="8">
                        <p>{{genderFormat(item.gender)}}</p>
                    </a-col>
                    <a-col :span="8" class="tar">
                        <p>{{roleFormat(item.role)}}</p>
                    </a-col>
                </a-row>
                <template v-if="item.role=='assistant' && item.join_info && item.join_info.expired">
                    <a-divider class="line" />
                    <a-descriptions title="雇佣信息" :column="2">
                        <a-descriptions-item label="薪资信息">{{salaryFormat(item.join_info.salary)}}</a-descriptions-item>
                        <a-descriptions-item label="结算方式">{{item.join_info.salary.settlement=='auto'?'账户自动扣除':'人工手动结算'}}</a-descriptions-item>
                        <a-descriptions-item label="工作截至" v-if="item.join_info.expired >currentTime()">{{item.join_info.expired}}</a-descriptions-item>
                        <a-descriptions-item label="工作截至" v-if="item.join_info.expired<=currentTime()"> 已到期，<a @click="toSettlement()">点击续期</a> </a-descriptions-item>
                        <a-descriptions-item label="加入时间">{{item.join_info.created}}</a-descriptions-item>
                    </a-descriptions>
                </template>

                <a-divider class="line">个人简介</a-divider>
                <div v-if="item.introduction!=''" class="introduction" v-html="introduction_html" v-highlight></div>
                <div v-if="item.introduction==''" class="introduction">
                    <a-empty description="未展示个人简介" />
                </div>
                <ActionSheet ref="as" />
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>

.ant-btn-link {
    padding: 0;
}
.c-form{
    display: flex;
    flex-direction: column;
    align-items: center;
    min-height: 100%;
    .head{
        display: flex;
        flex-direction: column;
        align-items: center;
        .logo{
            border-radius: 50%;
        }
        .name{
            font-weight: bold;
            font-size:1.2rem;
            line-height: 2rem;
        }
        .slogan{
            opacity: 0.5;
            font-size: .8rem;
            line-height: 1.2rem;
        }
    }

    .line{

    }
    .info{
        width:100%;
        text-align: center;
    }

    .join-settings{
        font-size: 14px;
        display: flex;
        flex-direction: column;
        width: 100%;
        .setting{
            display: flex;
            justify-content: space-between;
            align-items: center;
            height: 2.5rem;
            .name{}
            .exte{

            }
            .enable{}
        }
    }

    .introduction{
        margin-top:2rem;
        width: 100%;
    }
}
</style>
