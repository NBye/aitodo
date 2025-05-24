<script>


export default {
    components: {},
    props: {
        width: {
            type                        : Number,
            default                     : 0,
        },
        height: {
            type                        : Number,
            default                     : 0,
        },
        maxwidth: {
            type                        : Number,
            default                     : 0,
        },
        maxheight: {
            type                        : Number,
            default                     : 0,
        },
        mode: {
            type                        : Number,
            default                     : 1,
        },
        src: {
            type                        : String,
            default                     : "",
            // required: true, // 必须传递
        },
        alt: {
            type                        : String,
            default                     : "",
        },
        tags                            : {
            type                        : Array,
            default                     : [],
        },
        size: {
            type                        : String,
            default                     : "cover",
        },
        background: {
            type                        : String,
            default                     : "rgba(0, 0, 0, 0)",
        },
        class                           : {
            type                        : [Object,String],
            default                     : {},
        }
    },
    data() {
        return {};
    },
    methods: {
        url() {
            let w                       = this.width || this.maxwidth;
            let h                       = this.height || this.maxwidth;
            let url                     = this.cutImgUrl(this.src,{w,h,mode:this.mode,alt:this.alt})
            if (url){
                return `url(${url})`
            }else{
                return 'none'
            }

        },

        style(){
            return {
                width                   : (this.width || this.maxwidth) + 'px',
                height                  : (this.height || this.maxheight) + 'px',
                maxWidth                : this.maxwidth?(this.maxwidth + 'px'):'auto',
                maxHeight               : this.maxheight?(this.maxheight + 'px'):'auto',
                backgroundImage         : this.url(),
                backgroundColor         : this.background,
                backgroundSize          : this.size
            }
        }
    },
};
</script>

<template>
    <div class="image" :style="style()" :class="class">
        <div v-if="/^icon-/.test(src)" class="iconfont" :class="src" :style="{fontSize:'calc('+style().width+' * 0.9)'}"></div>
        <div class="tags" v-if="tags.length">
            <template v-for="(tag,i) in tags" :key="i">
                <div class="tag iconfont" :class="tag.class || tag" :title="tag.tip || ''"></div>
            </template>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.image {
    display: inline-block;
    background-position: center;
    background-repeat: no-repeat;
    position: relative;
    overflow: hidden;
    .iconfont{
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #fff;
    }
    .tags{
        position: absolute;
        top: 0;
        right: 0;
        display: flex;
        justify-content: flex-end;
        flex-direction: row;

        .tag{
            display: block;
            color:#dd0000;
            opacity: 0.8;
            border-radius: 0 0 0 0.3rem;
        }
    }
}
</style>
