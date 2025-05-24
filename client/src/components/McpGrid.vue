<script>
export default {
    components: {},
    props: {},
    data() {
        return {
            mcp_list                    : [],
        };
    },
    async mounted() {
        let {data}                      = await this.$request.post("/client/mcp/search");
        data.list.forEach(tag=>{
            tag.activate                = false;
        })
        this.mcp_list                   = data.list;
    },
    watch: {},
    methods: {
        async selectMcp(mcp){
            this.mcp_list.forEach(tag=>{
                tag.activate            = tag==mcp;
            });
            this.$emit('select', mcp);
        },
    },
};
</script>

<template>
    <div class="mcps">
        <div class="mcp no-select hand" v-for="(mcp,i) in mcp_list" :key="i" @click="selectMcp(mcp)" :class="{activate:mcp.activate}">
            <div class="head">
                <div class="icon" :style="`background-image:url(${mcp.icon})`"></div>
                <div class="info">
                    <div class="name">{{mcp.name}}</div>
                    <div class="by">{{mcp.author}}</div>
                </div>
            </div>
            <div class="iner">
                <div class="description">{{mcp.description}}</div>
            </div>
            <div class="foot">
                <div class="tags">
                    <div class="tag" v-for="tag in mcp.tags" :key="tag">{{tag}}</div>
                </div>
                <a class="install btn iconfont icon-fenxiang" target="__blank" :href="mcp.link"></a>
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>


.mcps{
    display: grid;
    // grid-auto-flow: column;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    overflow-x: auto;
    white-space: nowrap;
    grid-gap: 7px;
    justify-content: start;
    .mcp{
        display: flex;
        // width: 260px;
        flex-direction: column;
        background: rgba(244, 242, 241);
        border: solid 1px rgba(244, 242, 241);
        padding: 7px;
        border-radius: 7px;
        &.activate{
            border: solid 1px #ccc;
        }
        .head{
            display: flex;
            flex-direction: row;
            .icon{
                width: 40px;
                background-size: contain;
                background-position: center;
                background-repeat: no-repeat;
            }
            .info{
                padding: 0.1rem;
                padding: 0 5px;
                .name{
                    font-weight: 500;
                    font-size: 1.2rem;
                }
                .by{
                    color:hsl(16 69% 51%);
                    line-height: 1rem;
                    &::before{content:'by ';color: #999;}
                }
            }

        }
        .iner{
            height: 2rem;
            margin: 7px 2px;
            display: flex;
            align-items: center;
            overflow: hidden;
            -webkit-box-orient: vertical;
            -webkit-line-clamp: 2;
            white-space: normal;
            word-break: break-word;
            font-size: 0.8rem;
            line-height: 1rem;
        }
        .foot{
            display: flex;
            flex-direction: row;
            justify-content: space-between;
            .tags{
                display: flex;
                flex-direction: row;
                align-items: center;
                .tag{
                    border: solid 1px #333;
                    border-radius: 20px;
                    line-height: 1rem;
                    font-size: 0.9rem;
                    padding: 0.2rem 0.5rem;
                    margin-right: 4px;
                    &::before{content:'#';}
                }
            }
            .install{
                width: 1.5rem;
                height: 1.5rem;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                &:hover{
                    background: #ddd;
                }
            }

        }
    }
}
</style>
