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
    <div class="c-body c-screen">
        <div class="c-head c-left c-line">
            <div class="c-menu iconfont icon-menu"></div>
            <div class="c-title">ssssss</div>
            <div class="c-options">
                <div class="iconfont icon-more icon-menu"></div>
            </div>
        </div>
        <div class="c-scoll c-pd c-wd">
            <div v-for="(n,i) in Array(222)">create</div>
        </div>
    </div>
</template>

<style lang="scss" scoped></style>
