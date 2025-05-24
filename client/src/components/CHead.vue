<script>
import task from '../pages/console/task/task.vue';
import CoverImage from './CoverImage.vue';
export default {
    components: { task },
    props: {
        right                           : {
            type                        : Array,
            default                     : [{'icon':'icon-back',event:'navbar-hide'}],
        },
        left                            : {
            type                        : Array,
            default                     : [],
        },
        class                           : {
            type                        : [Object,String],
            default                     : {},
        }
    },
    data() {
        return {};
    },
    async mounted() {
    },
    methods: {
        clickItem(item){
            if (typeof item.event == 'function'){
                item.event(item)
            } else if(typeof item.event == 'string') {
                this.$EventBus.emit(item.event, item);
            }
        }
    },
};
</script>

<template>
    <div class="c-head" :class="class">
        <slot name="right">
            <template v-for="(o,i) in right" :key="i">
                <CoverImage v-if="/^(http|\/).*/.test(o.icon)" :class="'round'" :src="o.icon" :maxwidth="35" :maxheight="35" :alt="o.alt" class="c-menu" @click="clickItem(o)" />
                <div v-else class="c-menu iconfont" :class="o.icon" @click="clickItem(o)"></div>
            </template>
        </slot>
        <slot> </slot>
        <slot name="left">
            <div v-for="(o,i) in left" :key="i" class="c-menu iconfont" :class="o.icon" @click="clickItem(o)"></div>
        </slot>
    </div>
</template>

<style lang="scss" scoped>
.c-head{
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
}
</style>
