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

            reception_url               : '',
        };
    },
    async mounted() {
    },
    watch: {
        '$route.query': {
            handler(newQuery, oldQuery) {
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
            data.user.settings          = {
                visionmodel             : [],
                textmodel               : [],
                ...data.user.settings
            }
            this.item                   = data.user;
            this.storage_count          = data.storage_count;
            this.item.tags              = this.item.role=='assistant' ? ['icon-ai'] : []
            this.introduction_html      = await this.md2html(this.item.introduction)

            this.reception_url          = `https://${location.hostname}/#/reception?organization_assistant_id=${this.item.join_info._id}`


        },
        preview_reception(){
            let [width, height]         = [350,700];
            this.windowOpen({url:this.reception_url,width,height});
        },
        showMenu(){
            let menu                    = [
                {icon:'icon-bianji' ,name:'编辑信息',description:'',style:{},click:()=>this.toEdit()},
                {type:'line'},
                {icon:'icon-tichu'  ,name:'移除成员',description:'',style:{color:'#f00'},click:this.toRemove},
            ]
            this.$refs.as.show(menu)
        },
        async selectavatar({target}){
            let file = target.files[0]
            let reader                  = new FileReader();
            reader.onload=(e)=> {
                this.item.avatar        = e.target.result;
            };
            reader.readAsDataURL(file);
            await this.$request.post("/client/user/upset", {
                user_id                 : this.item._id,
                organization_id         : this.organization._id,
                avatar                  : file,
                group                   : 'base',
            });
            this.$EventBus.emit('user-update', { user:this.item });
        },

        async toRemove(){
            let content                 = ''
            if(this.item.role=='user'){
                content                 = '移除后可以再次邀约加入。'
            } else {
                content                 = '移除后该AI的所有数据会被清除，且不可恢复。'
            }
            if(!await this.confirm({title:'确定移除',content})){
                return;
            }
            await this.$request.post("/client/organization/leave", {
                organization_id         : this.organization._id,
                user_id                 : this.item._id,
            });
            this.$EventBus.emit('user-remove', { user:this.item });
            await Time.delay(1);
            this.linkBack();
        },
        async inviteOrganization(){
            await this.$request.post("/client/organization/invite", {
                organization_id         : this.organization._id,
                user_id                 : this.item._id,
            });
            this.$EventBus.emit('organization-user-invite', { user:this.item });
        },
        async update(data){
            await this.$request.post("/client/user/upset", Object.assign({
                organization_id         : this.organization._id,
                user_id                 : this.item._id,
            },data));
            Object.assign(this.item,data);
            this.$EventBus.emit('user-update', { user:this.item });
        },
        async toEdit(){
            this.link({path:'/console/personnel/edit',query:{user_id:this.item._id}})
        },
        async reception_status_change(status){
            await this.$request.post("/client/user/upset", {
                group                   : 'join',
                organization_id         : this.organization._id,
                user_id                 : this.item._id,
                reception_status        : status,
            });
        },
        async disabledUser(disabled){
            if(disabled){
                let data = await this.confirm({title:'请输入封禁原因',content:[
                    {name:'reason',value:'',label:'请输入原因',placeholder:'不超过20个文字',reg:'/^.{20}$/'}
                ]});
                if (data==false){
                    return this.item.join_info.disabled=false;
                }
                await this.$request.post("/client/user/disabled", Object.assign({
                    organization_id         : this.organization._id,
                    user_id                 : this.item._id,
                    disabled                : true,
                    disabled_reason         : data.reason,
                }));
                this.item.join_info.disabled_reason = data.reason;
            } else {
                await this.$request.post("/client/user/disabled", Object.assign({
                    organization_id         : this.organization._id,
                    user_id                 : this.item._id,
                    disabled                : false,
                }));
            }
        },
        async salary_settlement_update(settlement){
            await this.$request.post("/client/user/salary_settlement_update", Object.assign({
                user_id                     : this.item._id,
                organization_id             : this.organization._id,
                settlement
            }));
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
        async saveModel(){
            let post                = Object.assign({
                group               : 'settings',
                user_id             : this.item._id,
                organization_id     : this.organization._id,
            },this.item.settings);
            await this.$request.post("/client/user/upset", post);
        }
    },
};
</script>

<template>
    <div class="c-body c-screen am faster" :class="{show:PAGESHOW}">
        <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title">成员详情</div>
            <div class="c-options">
                <div class="iconfont icon-more icon-menu" @click="showMenu()"></div>
            </div>
        </CHead>
        <div class="c-scoll c-pd c-wd">
            <a-empty v-if="!item && loading" description="数据加载中..." />
            <div class="c-form pr" v-if="item && organization">
                <div class="c-id">
                    <Clipboard class="hand" :text="item._id" @clipboard-success="()=>aMessage().success('已复制到粘贴板')"> {{item.role=='user'?'':'AI'}}用户ID: {{item._id}} </Clipboard>
                </div>
                <div class="head">
                    <div v-if="user._id!=item._id">
                        <CoverImage class="logo" :src="item.avatar" :width="100" :height="100" :alt="item.nickname" :tags="item.tags" />
                    </div>
                    <div v-if="user._id==item._id">
                        <CFile ref="file" @change="selectavatar" :autoSubmit="false" border="none" background="none">
                            <template v-slot:initial>
                                <CoverImage class="logo" :src="item.avatar" :width="100" :height="100" :alt="item.nickname" :tags="item.tags" />
                            </template>
                            <template v-slot:preview>
                                <CoverImage class="logo" :src="item.avatar" :width="100" :height="100" :alt="item.nickname" :tags="item.tags" />
                            </template>
                        </CFile>
                    </div>
                    <div class="name">{{item.nickname}}</div>
                    <div class="slogan">{{item.slogan}}</div>
                    <div class="remark">{{item.join_info.remark}}</div>
                    <div>
                        <a-space :size="16">
                            <a-button type="link" @click="toEdit()">
                                编辑<template #icon><EditOutlined /></template>
                            </a-button>
                            <a-button type="link" @click="chatCreate(item._id)">
                                对话<template #icon><MessageOutlined /></template>
                            </a-button>
                            <a-button v-if="item.creator_organization_id==organization._id" type="link" @click="link({path:'/console/action',query:{user_id:item._id}})">
                                赋能<template #icon><SolutionOutlined /></template>
                            </a-button>
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
                <a-divider class="line" />
                <template v-if="item.role=='assistant' && item.creator_organization_id!=organization._id">
                    <a-descriptions title="雇佣信息" :column="isMobile()?1:2">
                        <a-descriptions-item label="薪资信息">{{salaryFormat(item.join_info.salary)}}</a-descriptions-item>
                        <a-descriptions-item label="结算方式">
                            <a-switch @change="salary_settlement_update" v-model:checked="item.join_info.salary.settlement" checked-children="账户自动扣除" un-checked-children="人工手动结算" checkedValue="auto" unCheckedValue="manual" />

                            <!-- {{item.join_info.salary.settlement=='auto'?'账户自动扣除':'人工手动结算'}} -->
                        </a-descriptions-item>
                        <a-descriptions-item label="工作截至" v-if="item.join_info.expired >currentTime()">{{item.join_info.expired}}</a-descriptions-item>
                        <a-descriptions-item label="工作截至" v-if="item.join_info.expired<=currentTime()"> 已到期，<a @click="toSettlement()">点击续期</a> </a-descriptions-item>
                        <a-descriptions-item label="加入时间">{{item.join_info.created}}</a-descriptions-item>
                    </a-descriptions>
                    <a-divider class="line" />
                </template>
                <template v-if="item.role=='assistant' && item.creator_organization_id==organization._id">
                    <a-descriptions title="参数信息" :column="isMobile()?1:2" v-if="item.role=='assistant' && item.creator_organization_id==organization._id">
                        <!-- <a-descriptions-item label="思考深广">{{item.settings.thoughtful}}</a-descriptions-item> -->
                        <a-descriptions-item label="消息轮次">{{item.settings.message_size}}条</a-descriptions-item>
                        <!-- <a-descriptions-item label="上下文长">{{item.settings.num_ctx}}</a-descriptions-item> -->
                        <a-descriptions-item label="迭代深度">最多 {{item.settings.max_iterations || 1}} 次</a-descriptions-item>
                        <a-descriptions-item label="创意温度">{{item.settings.temperature}}</a-descriptions-item>

                        <a-descriptions-item label="意图模型">
                            <a-cascader size="small" :bordered="false" :allowClear="false" v-model:value="item.settings.model" @change="saveModel()" :options="modelsFilter('tools')" />
                        </a-descriptions-item>
                        <a-descriptions-item label="视觉模型">
                            <a-cascader size="small" :bordered="false" :allowClear="false" v-model:value="item.settings.visionmodel" @change="saveModel()" :options="modelsFilter('vision')" />
                        </a-descriptions-item>
                        <a-descriptions-item label="语言模型">
                            <a-cascader size="small" :bordered="false" :allowClear="false" v-model:value="item.settings.textmodel" @change="saveModel()" :options="modelsFilter('text')" />
                        </a-descriptions-item>
                    </a-descriptions>
                    <a-divider class="line" />
                </template>

                <div class="join-settings">
                    <div class="setting" v-if="item.role=='assistant'">
                        <div class="name">外部接待</div>
                        <div class="exte" style="margin-left: auto;padding-right:0.5rem;color: #999;">
                            <!-- <Clipboard v-if="item.join_info.reception_status" class="hand" :text="reception_url" @clipboard-success="()=>aMessage().success('已复制到粘贴板')">复制连接</Clipboard> -->
                            <a-button v-if="item.join_info.reception_status" type="link" @click="preview_reception"><MessageOutlined />预览</a-button>
                            <span v-if="!item.join_info.reception_status">已关闭</span>
                        </div>
                        <div class="enable"><a-switch v-model:checked="item.join_info.reception_status" @change="reception_status_change(item.join_info.reception_status)" /></div>
                    </div>
                    <div class="setting">
                        <div class="name">禁言状态</div>
                        <div class="exte" style="margin-left: auto;padding-right:0.5rem;color: #999;">
                            {{item.join_info.disabled_reason}}
                        </div>
                        <div class="enable"><a-switch v-model:checked="item.join_info.disabled" @change="disabledUser(item.join_info.disabled)" /></div>
                    </div>
                    <div class="setting" v-if="item.role=='assistant' && item.creator_organization_id==organization._id">
                        <div class="name">全网公开</div>
                        <div class="exte" style="margin-left: auto;padding-right:0.5rem;color: #999;">
                            {{item.public?'已公开':'未公开'}}
                        </div>
                        <div class="enable">
                            <a-switch v-model:checked="item.public" @change="update({public:item.public,group:'base'})" />
                        </div>
                    </div>
                </div>

                <a-divider class="line">成员简介</a-divider>

                <div v-if="item.introduction!=''" class="introduction" v-html="introduction_html" v-highlight></div>
                <div v-if="item.introduction==''" class="introduction">
                    <a-empty description="未编辑成员简介" @click="toEdit()" />
                </div>

                <ActionSheet ref="as" />
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
a {
  text-decoration: none; /* 去除下划线 */
  color: inherit; /* 让链接颜色继承父元素的颜色 */
}

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
        .remark{
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
