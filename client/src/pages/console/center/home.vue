<script>
export default {
    data() {
        return {
            IS_PAGE                     : true,
            PAGESHOW                    : false,
            item                        : null,
            loading                     : false,
            storage_count               : 0,

            introduction_html           : '',

            menu                        : [
                {icon:'icon-bianji'    ,name:'编辑信息',description:'',style:{},click:()=>this.toEdit()},
                {type:'line'},
                {icon:'icon-tichu',name:'退出登录',description:'',style:{color:'#f00'},click:this.logout},
            ],
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
            immediate: true,
        },
    },
    methods: {
        async loadInfo(){
            this.item                   = null;
            let {data}                  = await this.$request.post("/client/user/info", {
            }).finally(()=>this.loading = false);
            this.item                   = data.user;
            this.storage_count          = data.storage_count;
            this.item.tags              = this.item.role=='assistant' ? ['icon-ai'] : []
            this.introduction_html      = await this.md2html(this.item.introduction)
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
        async toEdit(){
            this.link({path:'/console/center/update',query:{user_id:this.item._id}})
        },
    },
};
</script>

<template>
    <div class="c-body c-screen am faster" :class="{show:PAGESHOW}">
        <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title">我的详情</div>
            <div class="c-options">
                <div class="iconfont icon-more icon-menu" @click="$refs.as.trigger()"></div>
            </div>
        </CHead>
        <div class="c-scoll c-pd c-wd">
            <a-empty v-if="!item && loading" description="数据加载中..." />
            <div class="c-form pr" v-if="item">
                <div class="head">
                    <div>
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
                    <div>
                        <a-space :size="16">
                            <a-button type="link" @click="toEdit()">
                                编辑<template #icon><EditOutlined /></template>
                            </a-button>
                            <a-button type="link" @click="chatCreate(item._id)">
                                对话<template #icon><MessageOutlined /></template>
                            </a-button>
                        </a-space>
                    </div>
                </div>
                <a-divider class="line" />
                <a-row class="info">
                    <a-col :span="8" class="tal"><p>生日</p></a-col>
                    <a-col :span="8"><p>性别</p></a-col>
                    <a-col :span="8" class="tar"><p>存储</p></a-col>
                </a-row>
                <a-row class="info">
                    <a-col :span="8" class="tal">
                        <p>{{item.birthday || '未知'}}</p>
                    </a-col>
                    <a-col :span="8">
                        <p>{{genderFormat(item.gender)}}</p>
                    </a-col>
                    <a-col :span="8" class="tar">
                        <p>{{byteFormat(storage_count)}}/{{item.settings.storage_limit}}GB</p>
                    </a-col>
                </a-row>
                <a-divider class="line">个人简介</a-divider>

                <div v-if="item.introduction!=''" class="introduction" v-html="introduction_html" v-highlight></div>
                <div v-if="item.introduction==''" class="introduction">
                    <a-empty description="未编辑成员简介" @click="toEdit()" />
                </div>

                <ActionSheet ref="as" :list="menu" />
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
