<script>
export default {
    components: {},
    data() {
        return {
            IS_PAGE                     : true,
        };
    },
    async mounted() {


    },
    methods: {},
};
</script>

<template>
    <div class="c-list c-screen">
        <div class="c-head">
            <div class="c-menu iconfont icon-menu"></div>
        </div>
        <div class="c-scoll">
            <div v-for="(n,i) in Array(222)">scollscollscoll</div>
        </div>
    </div>
    <router-view></router-view>
</template>

<style lang="scss" scoped></style>
