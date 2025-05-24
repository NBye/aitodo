<script>
export default {
    // @checked(item) @scrollTop @scrollBottom
    props: {
        class                           : {
            type                        : [String,Object],
            default                     : '',
        },
        list                            : {
            type                        : Array,
            default                     : [],
        },
        avatar                          : {
            type                        : String,
            default                     : 'avatar',
        },
        tags                            : {
            type                        : String,
            default                     : '',
        },
        name                            : {
            type                        : String,
            default                     : 'name',
        },
        description                            : {
            type                        : String,
            default                     : 'description',
        },
        gap                             : {
            type                        : Number,
            default                     : 8,
        },
        go                             : {
            type                        : Boolean,
            default                     : false,
        },
    },
    data() {
        return {

        };
    },
    async mounted() {
        let scrollElement               = this.$refs.list;
        let fang,stop                   = -1;
        scrollElement.addEventListener('scroll', ()=> {
            fang                        = scrollElement.scrollTop - stop;
            stop                        = scrollElement.scrollTop;
            if (fang < 0 && scrollElement.scrollTop === 0) {
                this.onScrollTop();
            }
            if (fang > 0 && scrollElement.scrollTop + scrollElement.clientHeight >= scrollElement.scrollHeight-20) {
                this.onScrollBottom();
            }
        });
    },
    methods: {
        checkItem(item){
            this.list.forEach(o=>{
                o.active                = item == o;
            });
            this.$emit('checked', item);
        },
        async onScrollTop(){
            if(this.onScrollTopIng){
                clearTimeout(this.onScrollTopIng)
            }
            this.onScrollTopIng         = setTimeout(()=>{
                this.$emit('scrollTop');
            },100)
        },
        async onScrollBottom(){
            if(this.onScrollBottomIng){
                clearTimeout(this.onScrollBottomIng)
            }
            this.onScrollBottomIng      = setTimeout(()=>{
                this.$emit('scrollBottom');
            },100)
        },

        getValue(item,path,def=''){
            for(let p of path.split('|')) {
                let data                = item;
                let find                = false;
                for(let k of p.split('.')){
                    if(data[k]==='' || data[k]===undefined || data[k]===null){
                        find            = false;
                        break;
                    } else {
                        find            = true;
                        data            = data[k];
                    }
                }
                if(find){
                    return data;
                }
            }
            return def;
        }
    },
};
</script>

<template>
    <div ref="list" class="c-list" :class="class">
        <slot name="head"></slot>
        <slot name="list">
            <template v-for="(item,i) in list" :key="i">
                <slot name="item" :item="item">
                    <div class="c-list-item no-select" :class="{active:item.active}" @click="checkItem(item)">
                        <div class="c-list-item-container">
                            <slot name="avatar" :item="item" v-if="avatar">
                                <div class="c-l">
                                    <CoverImage class="c-list-item-container-avatar" :src="getValue(item,avatar)" :alt="getValue(item,name)" :width="46" :height="46" :tags="getValue(item,tags,[])" />
                                </div>
                            </slot>
                            <div class="c-c">
                                <div class="c-list-item-container-name">
                                    <slot name="name" :item="item">{{getValue(item,name)}}</slot>
                                </div>
                                <div class="c-list-item-container-desc">
                                    <slot name="desc" :item="item">
                                        {{getValue(item,description)}}
                                    </slot>
                                </div>
                                <div class="c-list-item-mark">
                                    <slot name="mark" :item="item"></slot>
                                </div>
                            </div>
                            <slot name="go" :item="item" v-if="go">
                                <div class="c-go iconfont icon-go"></div>
                            </slot>
                        </div>
                    </div>
                </slot>
            </template>
        </slot>
        <slot name="foot"></slot>
    </div>
</template>

<style lang="scss" scoped>
.c-list{
    gap: 8px;
    .c-list-item{
        padding: 8px 16px;
        position: relative;
        &:not(:last-child)::after {
            content: "";
            position: absolute;
            right: 0;
            bottom: -5px;
            height: 1px;
            width: 100%;
            background-color: #ddd;
        }
        &:hover{
            background: #e5e5e5;
        }
        &.active{
            background: #dddddd;
        }
        .c-list-item-container{
            display: flex;
            .c-l{
                display: flex;
                .c-list-item-container-avatar{
                    border-radius: .3rem;
                }
            }
            .c-c{
                position: relative;
                display: flex;
                flex-direction: column;
                justify-content: space-around;
                padding-left: 0.3rem;
                width: 100%;
                .c-list-item-container-name{
                    font-size: 1rem;
                }
                .c-list-item-container-desc{
                    font-size: 0.8rem;
                    color:#999;
                    display: -webkit-box;
                    -webkit-line-clamp: 2;
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
                .c-list-item-mark{
                    position: absolute;
                    right: -8px;
                    top: -8px;
                }
            }
            .c-go{
                display: flex;
                align-items: center;
            }
        }
    }
}
</style>
