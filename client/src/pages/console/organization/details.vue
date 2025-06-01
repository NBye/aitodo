<script>
import CoverImage from '../../../components/CoverImage.vue';
import Empty from '../../../components/Empty.vue';
export default {
    components: {CoverImage, Empty},
    data() {
        return {
            IS_PAGE                     : true,
            PAGESHOW                    : false,
            item                        : null,
            user_count                  : 0,
            storage_count               : 0,
            loading                     : false,

            introduction_html           : '',

            recharge_show               : false,
            recharge_url                : '',
            recharge_amount             : 0,
            recharge_count_down         : 0,
        };
    },
    async mounted() {
    },
    watch: {
        '$route.query': {
            handler(newQuery, oldQuery) {
                this.PAGESHOW          = true;
                this.item              = null;
                this.loadInfo()
            },
            immediate: true, // 如果需要在组件加载时立即触发
        },
    },
    methods: {
        async showMenu(){
            this.$refs.as.show([
                {icon:'icon-bianji'     ,name:'编辑信息',description:'',style:{},click:()=>this.toEdit()},
                {icon:'icon-bianji'     ,name:'组织设置',description:'',style:{},click:()=>this.toSettings()},
                {icon:'icon-join'       ,name:'进入组织',description:'',style:{},click:this.intoOrganization},
                {type:'line'},
                {icon:'icon-leave',name:'退出组织',description:'',style:{color:'#f00'},click:this.leave},
                {icon:'icon-dissolution',name:'解算组织',description:'',style:{color:'#f00'},click:this.dissolution},
            ])
        },
        async loadInfo(){
            let organization_id         = this.$route.query.organization_id;
            if(!organization_id){
                return;
            }
            let {data}                  = await this.$request.post("/client/organization/info", {
                organization_id
            }).finally(()=>this.loading = false);
            this.item                   = data.organization;
            this.user_count             = data.user_count;
            this.storage_count          = data.storage_count;
            this.introduction_html      = await this.md2html(this.item.introduction)
        },
        async selectavatar({target}){
            let file = target.files[0]
            let reader                  = new FileReader();
            reader.onload=(e)=> {
                this.item.avatar        = e.target.result;
            };
            reader.readAsDataURL(file);
            await this.$request.post("/client/organization/upavatar", {
                organization_id         : this.item._id,
                avatar                  : file,
            });
            this.$EventBus.emit('organization-update', { organization:this.item });
        },
        async dissolution(){
            if(!await this.confirm({title:'确定删除？',content:'删除后不可恢复，组织内文件也将清除。'})){
                return;
            }
            await this.$request.post("/client/organization/destroy", {
                organization_id         : this.item._id,
            });
            this.$EventBus.emit('organization-leave', { organization:this.item });
            this.linkBack();
        },
        async leave(){
            if(!await this.confirm({title:'确定离开？',content:'离开后，您在当前组织中的数据将失去所有权。'})){
                return;
            }
            await this.$request.post("/client/organization/leave", {
                organization_id         : this.item._id,
            });
            this.$EventBus.emit('organization-leave', { organization:this.item });
            this.linkBack();
        },
        async intoOrganization(){
            await this.$request.post("/client/organization/switch", {
                organization_id         : this.item._id,
            });
            this.$EventBus.emit('organization-switch', { organization:this.item });
        },
        async updateOrganization(data){
            if(data.settings.join_code_enabled){
                let conf = await this.confirm({title:'请输加入密码',content:[
                    {name:'code',value:'',label:'加入密码',placeholder:'不超过20个字符',reg:'/^.{20}$/'}
                ]});
                if(conf==false){
                    return data.settings.join_code_enabled=false;
                }
                data.settings.join_code_value=conf.code;
            }
            await this.$request.post("/client/organization/upset", Object.assign({
                organization_id         : this.item._id,
            },data));
            this.$EventBus.emit('organization-update', { organization:this.item });
        },
        async toEdit(){
            this.link({path:'edit',query:this.$route.query})
        },
        async toSettings(){
            this.link({path:'settings',query:this.$route.query})
        },

        async toRecharge(){
            let data = await this.confirm({title:'确认充值金额',content:[
                {name:'amount',value:'200',label:'请输入金额(元)',type:"input:number",placeholder:'单位(元)',min:"0",max:"100"}
            ]});
            if(!data){
                return;
            }
            let res  = await this.$request.post("/client/organization/recharge", {
                ...data,
                organization_id         : this.item._id,
            });
            this.recharge_url           = res.data.pay_url;
            this.recharge_show          = true;
            this.recharge_amount        = (data.amount*1).toFixed(2);
            this.recharge_count_down    = 10;
            clearInterval(this.recharge_count_down_run);
            this.recharge_count_down_run= setInterval(()=>{
                this.recharge_count_down--;
                if(this.recharge_count_down==0){
                    clearInterval(this.recharge_count_down_run);
                }
            },1000);
        },
        async refishRecharge(){
            clearInterval(this.recharge_count_down_run);
            this.recharge_show          = false;
            this.loadInfo();
        },
    },
};
</script>

<template>
    <div class="c-body c-screen am faster" :class="{show:PAGESHOW}">
        <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title">组织详情</div>
            <div class="c-options">
                <div class="iconfont icon-more icon-menu" @click="showMenu()"></div>
            </div>
        </CHead>
        <div class="c-scoll c-pd c-wd">
            <a-empty v-if="!item && loading" description="数据加载中..." />
            <div class="c-form pr" v-if="item">
                <div class="c-id">
                    <Clipboard class="hand" :text="item._id" @clipboard-success="()=>aMessage().success('已复制到粘贴板')"> 组织ID: {{item._id}} </Clipboard>
                </div>
                <div class="head">
                    <div>
                        <CFile ref="file" @change="selectavatar" :autoSubmit="false" border="none" background="none">
                            <template v-slot:initial>
                                <CoverImage class="logo" :src="item.avatar" :width="100" :height="100" :alt="item.name" />
                            </template>
                            <template v-slot:preview>
                                <CoverImage class="logo" :src="item.avatar" :width="100" :height="100" :alt="item.name" />
                            </template>
                        </CFile>
                    </div>
                    <div class="name">{{item.name}}</div>
                    <div class="slogan">{{item.slogan || '欢迎加入'}}</div>
                    <div>
                        <a-space :size="16">
                            <a-button type="link" @click="intoOrganization()">
                                进入<template #icon><SelectOutlined /></template>
                            </a-button>
                            <template v-if="item.user_id==user._id">
                                <a-button type="link" @click="toEdit()">
                                    编辑<template #icon><EditOutlined /></template>
                                </a-button>
                                <a-button type="link" @click="toSettings()">
                                    设置<template #icon><EditOutlined /></template>
                                </a-button>
                                <a-button type="link" @click="link({path:'secret',query:$route.query})">
                                    密钥<template #icon><KeyOutlined /></template>
                                </a-button>
                            </template>
                        </a-space>
                    </div>
                </div>
                <a-divider class="line" />
                <a-row class="info">
                    <a-col :span="12" class="tal"><p>组内成员</p></a-col>
                    <a-col :span="12"><p>存储额度</p></a-col>
                </a-row>
                <a-row class="info">
                    <a-col :span="12" class="tal">
                        <p>{{user_count}}/{{item.settings.user_limit}}</p>
                    </a-col>
                    <a-col :span="12">
                        <p>{{byteFormat(storage_count)}}/{{item.settings.storage_limit}}GB</p>
                    </a-col>
                </a-row>
                <a-divider class="line" />

                <div class="join-settings">
                    <div class="setting">
                        <div class="name">邀请方式加入</div>
                        <div class="exte"></div>
                        <div class="enable"><a-switch v-model:checked="item.settings.join_invite_enabled" @change="updateOrganization({settings:item.settings})" /></div>
                    </div>

                    <div class="setting">
                        <div class="name">口令方式加入</div>
                        <div class="exte" style="margin-left: auto;padding-right:0.5rem;color: #999;">
                            {{item.settings.join_code_value.replace(/./g,'*')}}
                        </div>
                        <div class="enable"><a-switch v-model:checked="item.settings.join_code_enabled" @change="updateOrganization({settings:item.settings})" /></div>
                    </div>
                </div>

                <a-divider class="line">组织简介</a-divider>

                <div v-if="item.introduction!=''" class="introduction" v-html="introduction_html" v-highlight></div>
                <div v-if="item.introduction==''" class="introduction">
                    <a-empty description="未编辑组织简介" @click="toEdit()" />
                </div>

                <ActionSheet ref="as" />

                <a-modal v-model:open="recharge_show" title="充值二维码">
                    <div class="recharge-modal">
                        <a-qrcode error-level="M" :value="recharge_url" :icon="item.avatar" />
                        <div class="ddd">
                            <div>支付金额：{{recharge_amount}}</div>
                            <div>请使用 “支付宝” 扫码付款</div>
                            <a-button type="primary" @click="refishRecharge()" :disabled="recharge_count_down?true:false"> 我已，完成支付{{recharge_count_down?`(${recharge_count_down}s)`:''}} </a-button>
                        </div>
                    </div>
                    <template #footer> </template>
                </a-modal>
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.recharge-modal{
    display: flex;

    .ddd{
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        justify-content: space-around;
    }
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
    }

    .line{

    }
    .info{
        width:100%;
        text-align: center;
        .iconfont{
            vertical-align: middle;
        }
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
