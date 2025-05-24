<script>
import List from 'ant-design-vue/es/vc-virtual-list/List';
import global from '../common/utils/global';
export default {
    props: {
        parent                           : {
            type                        : Object,
            default                     : null,
        },
        agent                           : {
            type                        : Object,
            required                    : true,
        },
        index                           : {
            type                        : Number,
            default                     : null,
        },
    },
    data() {
        return {
            hover                       : false,
            columns                     : [
                {
                    title: 'Full Name',
                    dataIndex: 'name',
                    fixed: 'left',
                    width: 150,
                    resizable: true,
                    rowDrag: true,
                    key: 'name',
                },
                {
                    title: 'Action',
                    key: 'operation',
                    fixed: 'right',
                    width: 100,
                    resizable: true,
                },
            ],
        };
    },
    async mounted() {
    },
    methods: {
        disabled(){
            this.agent.disabled=!this.agent.disabled;
            this.$EventBus.emit('agent-resave');
        },
        toEdit(){
            this.$refs.afm.show('编辑Agent',this.agent.type,this.agent,this.parent.root);
        },
        addAgent(title='添加子集Agent'){
            this.$refs.afm.show(title,this.agent.type,null,this.agent.root);
        },
        async toRemove(){
            if(!await this.confirm({title:'确认删除？',content:this.agent.description})){
                return ;
            }
            this.listRemoveItem(this.parent.children,this.agent);
            this.$EventBus.emit('agent-resave');
        },
        async onSubmit(data){
            if(data.name){
                delete data.children;
                Object.assign(this.agent,data);
            } else {
                this.agent.children.push(data)
            }
            this.$refs.afm.hide()
            this.$EventBus.emit('agent-resave');
        },


        onDragStart(event,agent) {
            document.documentElement.addEventListener('mouseup',this.onDrop)
            document.documentElement.addEventListener('touchend',this.onDrop)
            global.target = {
                pageY:event.pageY,
                agent,
                parent:this.parent,
            }
        },
        onDragMove(event,agent) {
            if(!global.target || global.target.agent==agent){
                return;
            } else if(global.target.parent.children!=this.parent.children){
                return;
            }
            let i = global.target.parent.children.indexOf(global.target.agent)
            global.target.parent.children.splice(i,1)
            if (event.pageY < global.target.pageY){
                i = this.parent.children.indexOf(agent)
            } else {
                i = this.parent.children.indexOf(agent)+1
            }
            this.parent.children.splice(i,0,global.target.agent)
            this.moved                  = true;
            global.target.pageY         = event.pageY
        },
        onDrop(event,agent) {
            if (global.target && this.moved){
                this.$EventBus.emit('agent-resave');
            }
            this.moved                  = false;
            delete global.target;
            document.documentElement.removeEventListener('mouseup',this.onDrop)
            document.documentElement.removeEventListener('touchend',this.onDrop)
        },
    },
};
</script>

<template>
    <div class="agent" :class="{hover:hover}" @mouseover.stop="hover=true" @mouseout.stop="hover=false">
        <div class="head" v-if="!agent.root" @touchstart.stop="(e)=>onDragStart(e,agent)" @touchmove.stop="(e)=>onDragMove(e,agent)" @touchend.stop="(e)=>onDrop(e,agent)" @mousedown.stop="(e)=>onDragStart(e,agent)" @mousemove.stop="(e)=>onDragMove(e,agent)" @mouseup.stop="(e)=>onDrop(e,agent)">
            <div class="no" v-if="!parent.root">
                <span class="iconfont icon-xiayou"></span>
                <span>{{index}}</span>
            </div>
            <div class="title">
                <!-- <span>{{agent.name}}</span> -->
                <span class="no-select">{{agent.description}}</span>
            </div>
            <a-space :size="1" @touchstart.stop @touchmove.stop @touchend.stop="(e)=>onDrop(e,agent)" @mousedown.stop="(e)=>onDragStart(e,agent)" @mousemove.stop="(e)=>onDragMove(e,agent)" @mouseup.stop>
                <a-button type="link" @click.stop="disabled()" title="启用禁用">
                    <template #icon><span class="iconfont icon-jinyong jinyong" :class="{disabled:agent.disabled}"></span></template>
                </a-button>
                <a-button type="link" @click.stop="addAgent()" title="添加后续">
                    <template #icon><span class="iconfont icon-xiayou"></span></template>
                </a-button>
                <a-button type="link" @click.stop="toEdit()">
                    <template #icon><EditOutlined /></template>
                </a-button>
                <a-button type="link" @click.stop="toRemove()">
                    <template #icon><DeleteOutlined /></template>
                </a-button>
            </a-space>
        </div>
        <div class="children" :class="{pdl:!agent.root}">
            <template v-for="(c,i) in agent.children">
                <Agent :agent="c" :index="i+1" :parent="agent"></Agent>
            </template>
        </div>
    </div>
    <AgentForm ref="afm" @submit="onSubmit" />
</template>

<style lang="scss" scoped>
.ant-btn-link {
    padding: 0;
}
.agent{
    width: 100%;
    .head{
        display: flex;
        align-items: center;
        width: 100%;
        .title{
            flex-grow: 1;
            font-family: monospace;
            overflow: hidden;
            text-overflow: ellipsis;
            height: 1rem;

            display: -webkit-box;
            -webkit-box-orient: vertical;  /* 设置纵向排列 */
            -webkit-line-clamp: 2;         /* 限制最多显示 2 行 */

            .no-select{
                cursor: grab;
                margin-left:0.6rem;
            }
        }
        .options{
            flex: 0 0 auto;
        }
        .no{
            width:2rem;
            width: 4rem;
            text-align: left;
            color:#999;
            &::after{
                content: '.';
            }
        }
    }
    .children{
        &.pdl{
            padding-left:1.5rem;
        }
        .iconfont {
            font-size: 16px;
        }

        .iconfont.jinyong{
            color: #999;
            &.disabled{color: #f00;}
        }
    }
    .hover{
        background: #f5f5f5;
    }
}
</style>
