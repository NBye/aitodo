<script>

import {HOST} from "../../common/utils/request"
import storage from '../../common/utils/storage';
import Time from '../../common/utils/Time';
import EventBus from '../../common/utils/EventBus';

export default {
    components: {},
    data() {
        return {
            IS_PAGE                     : true,
            PAGESHOW                    : false,
            navs                        : [
                {title:"聊天",  stitle:'聊天消息',      path:"/console/chat",           icon:"icon-chat",           active:false},
                {title:"成员",  stitle:'组织内成员',    path:"/console/personnel",      icon:"icon-personnel",      active:false},
                {title:"文件",  stitle:'文件管理',      path:"/console/file",           icon:"icon-file",           active:false},
                {title:"知识",  stitle:'知识管理',      path:"/console/knowledge",      icon:"icon-zhishi",         active:false},

                {title:"数据",  stitle:'数据库',        path:"/console/database",       icon:"icon-database",       active:false},


                {title:"任务",  stitle:'任务管理',      path:"/console/task",           icon:"icon-task",           active:false},
                // {title:"日程",  stitle:'日程',          path:"/console/calendar",       icon:"icon-calendar",       active:false},
                // {title:"更多",  stitle:'查看更多',      icon:"icon-more", children:[]},

                {title:"帮助",  stitle:'帮助文档',      path:"/console/document",       icon:"icon-dengpao",         active:false,   align:"end"},
                {title:"组织",  stitle:'我的组织',      path:"/console/organization",   icon:"icon-enterprise",     active:false},
            ],
            organizations               : [],

            SwitchOrganizationState     : false,

            controller                  : null,
        };
    },
    watch: {
        '$route.query': {
            handler() {
                this.navbar_active();
            },
        },
    },
    async unmounted(){
        this.$EventBus.off('organization-event',this.organization_event);

        this.$EventBus.off('organization-switch',this.organization_switch);
        this.$EventBus.off('organization-update',this.organization_update);
        this.$EventBus.off('organization-leave',this.organization_leave);
        this.$EventBus.off('navbar-show',this.navbar_show);
        this.$EventBus.off('organization-forbid',this.switchOrganization);

        this.event_close();
    },
    async mounted() {

        this.$EventBus.on('organization-switch',this.organization_switch);
        this.$EventBus.on('organization-update',this.organization_update);
        this.$EventBus.on('organization-leave',this.organization_leave);
        this.$EventBus.on('navbar-show',this.navbar_show);
        this.$EventBus.on('organization-forbid',this.switchOrganization);

        this.navbar_active();
        this.loadInfo();
    },
    methods: {
        async event_close(){
            if(this.controller){
                this.controller.abort();
                this.controller = null;
            }
        },
        async event_listener(times=0,maxtimes=1000){
            if(times>maxtimes){
                return;
            }
            this.event_close();
            this.controller = new AbortController();
            let headers = {
                'content-type': 'application/json',
                'token': storage('token') || '',
            };
            fetch(`${HOST}/client/organization/event`, {
                method                  : 'GET',
                credentials             : 'same-origin',
                signal                  : this.controller.signal,
                headers
            }).then(async response => {
                if (!response.ok) {
                    this.controller     = null;
                    throw new Error('连接断开自动重连');
                }
                window.listening          = true;
                times                   = 0;
                const reader            = response.body.getReader();  // 获取响应体的读取器
                const decoder           = new TextDecoder();  // 用于将流中的字节解码成文本
                while(this.controller){
                    let { done, value } = await reader.read()
                    let text            = decoder.decode(value, { stream: true })
                    text.split('\n\n').forEach(message=>{
                        if(!message){
                            return;
                        }
                        try {
                            let data    = JSON.parse(message)
                            if(data.code!=1){
                                this.aMessage().error(data.message);
                            }
                        } catch(e) {
                            let data    = {}
                            message.split('\n').forEach(line=>{
                                if(/^event:/.test(line)){
                                    data.event      = line.substring(6).trim();
                                }else if(/^id:/.test(line)){
                                    data.id         = line.substring(3).trim();
                                }else if(/^data:/.test(line)){
                                    data.data       = JSON.parse(line.substring(5).trim());
                                }
                            });
                            this.$EventBus.emit(data.event,data.data);
                        }
                    });
                    if(done){
                        break
                    }
                }
            }).catch(async error => {
                if (error.name === 'AbortError') {
                    console.log('Fetch request aborted');
                } else {
                    times && await Time.delay(times/1000*100)
                    this.event_listener(times+1)
                }
            });
        },
        async organization_switch({organization}){
            await this.refishCache()
            this.link({path:'/console/personnel'})
            this.event_listener()
        },
        async organization_update({organization}){
            if(this.organization._id==organization._id){
                Object.assign(this.organization,organization);
            }
        },
        async organization_leave({organization}){
            if(this.organization._id==organization._id){
                this.switchOrganization();
            }
        },
        async navbar_show(){
            this.PAGESHOW               = true;
        },
        async navbar_active(){
            for(let item of this.navs){
                if(this.$route.path.indexOf(item.path)==0){
                    this.switchNav(item);
                    break;
                }
            }
        },
        async loadInfo(){
            // 加载个人信息
			await this.refishMyInfo()
            // 加载我的组织
            if (!this.organization){
                return await this.switchOrganization();
            }
			this.refishModels()
			this.refishTemplates()
            this.event_listener();
        },
        async switchOrganization(){
            let {data}                  = await this.$request.post("/client/organization/search", {});
            this.organizations          = data.list
            if(data.list.length==0){
                this.aModal().info({title:'您还没有加入任何组织',content:"点击确认创建一个属于自己的组织，同时您可以邀请其他用户与您共同使用。",okText:'确认',afterClose:()=>{
                    this.link({path:'/console/organization/create'});
                }});
            } else {
                this.SwitchOrganizationState    = true;
            }
        },
        async inotoOrganization(organization){
            await this.$request.post("/client/organization/switch", {
                organization_id                 : organization._id,
            });
            this.SwitchOrganizationState        = false;
            this.$EventBus.emit('organization-switch', { organization });
        },
        async moreOrganization(){
            this.link({path:'/console/organization'});
            this.SwitchOrganizationState        = false;
        },
        switchNav(item){
            item.path && this.navs.forEach(e=>{
                e.active=e==item;
            });
        },
        checkedNav(item){
            this.link({path:item.path})
            this.PAGESHOW                       = false;
            console.log('checkedNav',item.path)
        },
        showMenu(){
            this.link({path:'/console/center'})
            this.PAGESHOW                       = false;
        },
    },
};
</script>

<template>
    <div class="console" :class="{'is-mobile':IS_MOBILE}">
        <div class="c-screen c-navbar am faster" :class="{show:PAGESHOW}" @click.stop="PAGESHOW=false">
            <div class="c-head" v-if="organization" @click.stop="showMenu">
                <CoverImage :src="organization.avatar" :alt="organization.name" :width="38" :height="38" style="border-radius: 0.3rem;" />
                <div class="name" v-if="IS_MOBILE">
                    {{organization.name}}
                </div>
                <div class="c-menu iconfont icon-close mla" @click.stop="PAGESHOW=false"></div>
            </div>
            <div class="c-head" v-if="!organization && user" @click.stop="showMenu">
                <CoverImage :width="38" :height="38" :alt="user.nickname" background="#fff" size="50%" style="border-radius: 0.3rem;" />
                <div class="c-menu iconfont icon-close mla" @click.stop="PAGESHOW=false"></div>
            </div>
            <div class="list navs" @click.stop>
                <div class="nav no-select am faster" v-for="(item,i) in navs" :key="i" :class="item.align">
                    <div class="pd" :class="{active:item.active}" @click="switchNav(item),checkedNav(item)">
                        <div class="iconfont" :class="item.icon"></div>
                        <div class="title">{{IS_MOBILE?item.stitle:item.title}}</div>
                    </div>
                </div>
            </div>
        </div>
        <div class="c-container">
            <router-view></router-view>
        </div>
    </div>
    <a-modal v-model:open="SwitchOrganizationState" title="请选择您的组织" :closable="false" :keyboard="false" :maskClosable="false">
        <template #footer>
            <a-button type="link" @click="moreOrganization()">查看更多</a-button>
        </template>
        <a-list class="demo-loadmore-list" item-layout="horizontal" :data-source="organizations">
            <template #renderItem="{ item }">
                <a-list-item>
                    <template #actions>
                        <a key="list-loadmore-more" @click="inotoOrganization(item)">进入</a>
                    </template>
                    <a-skeleton avatar :title="false" :loading="false" active>
                        <a-list-item-meta :description="item.slogan">
                            <template #title>
                                <a>{{ item.name }}</a>
                            </template>
                            <template #avatar>
                                <a-avatar :src="cutImgUrl(item.avatar,{w:100,h:100,alt:item.name})" />
                            </template>
                        </a-list-item-meta>
                    </a-skeleton>
                </a-list-item>
            </template>
        </a-list>
    </a-modal>
</template>

<style lang="scss" scoped>

.console{
    display: flex;
    height: 100%;
    width: 100%;
    .c-navbar{
        display: flex;
        width: 60px; /* 固定宽度 */
        height: 100%;
        flex-shrink: 0; /* 禁止压缩 */
        flex-grow: 0; /* 禁止拉伸 */
        background-image: linear-gradient(to right, var(--ant-color-primary) 100%,#fff 0%);
        flex-direction: column;
        .c-head{
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ccc;
            .name{
                font-size: 1.2rem;
                padding: 0 1rem;
            }
        }
        .navs{
            overflow: auto;
        }
        .list{
            gap: 0.5rem;
            display: flex;
            flex-direction: column;
            flex: 1;
            overflow: auto;
            .nav{
                height:60px;
                &.end{
                    margin-top: auto;
                }
                .pd{
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    color: #ccc;
                    width: 100%;
                    height:100%;
                    border-radius: 0.2rem;
                    .iconfont{
                        font-size:2.2rem;
                        line-height: 2.1rem;
                    }
                    .title{
                        font-size: 0.9rem;
                    }
                    &:hover{
                        background: rgba(255,255,255,0.1);
                    }
                    &.active{
                        color:#FFF;
                        background: rgba(255,255,255,0.2);
                    }
                }
            }
        }
    }
    .c-container{
        flex: 1; /* 自动占据剩余空间 */
        display: flex;
        flex-direction: row;
    }
}
</style>
