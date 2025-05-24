<script>
export default {
    props: {
        title                           : {
            type                        : String,
            default                     : '请选择',
        },
        closable                        : {
            type                        : Boolean,
            default                     : true,
        },
        onClose                         : {
            type                        : Function,
            default                     : new Function(),
        },
        list                            : {
            type                        : Array,
            default                     : [
                {icon:'icon-shanchu',name:'删除',description:'删除有风险',style:{},click:new Function()},
            ],
        },
    },
    data() {
        return {
            open                        : false,
            title2                      : '',
        };
    },
    async mounted() {},
    methods: {
        show(list=null,title=null){
            if(list){
                while(this.list.length){
                    this.list.pop()
                }
                list.forEach(item=>this.list.push(item))
            }
            if(title){
                this.title2             = title;
            }
            this.open                   = true;
        },
        hide(){
            this.open                   = false;
        },
        trigger(){
            this.open                   = !this.open;
        },
        height(){
            let h                       = 24 * 2 + 70;
            this.list.forEach(item=>{
                if(item.type=='line'){
                    h                   += 8;
                }else{
                    h                   += 8 + 40;
                }
            })
            return h+'px'
        }
    },
};
</script>

<template>
    <a-drawer :title="title2 || title" :height="height()" placement="bottom" :closable="closable" :maskClosab="closable" v-model:open="open" @close="onClose" :get-container="false" :maskStyle="{background: 'rgba(255, 255, 255, 0.0)'}">
        <div class="sheet list">
            <template v-for="(item,i) in list" :key="i">
                <a-divider v-if="item.type=='line'" class="line">{{item.name}}</a-divider>
                <div v-else-if="item.type=='description'" class="description">{{item.description}}</div>
                <div v-else class="item no-select" @click="item.click(item) && hide()">
                    <div class="iconfont" v-if="/^icon-/.test(item.icon)" :class="item.icon"></div>
                    <CoverImage class="iconfont" v-if="/^\/(upload|static)/.test(item.icon)" :src="item.icon" :width="32" :height="32" />
                    <div class="row" :style="item.style">
                        <div class="title">{{item.name}}</div>
                        <div class="description">{{item.description}}</div>
                    </div>
                    <div class="iconfont" :class="item.after"></div>
                </div>
            </template>
        </div>
    </a-drawer>
</template>

<style lang="scss" scoped>
.sheet.list{
    display: flex;
    flex-direction: column;
    gap: 8px;
    .line{
        margin: 0;
    }
    .description{
        opacity: 0.5;
        font-size: 0.8rem;
    }
    .item{
        display: flex;
        flex-direction: row;
        width: 100%;
        align-items: center;
        height: 40px;
        justify-content: center;
        border-radius: 5px;

        &:hover{
            background-color: #eee;
        }
        .iconfont{
            width: 32px;
            font-size: 1.6rem;
        }
        .row{
            display: flex;
            width: 100%;
            flex-direction: column;
            position: relative;
            .description{
                opacity: 0.5;
                font-size: 0.8rem;
            }
            .title{}
        }
    }
}
</style>
