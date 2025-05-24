<script>
import locale from 'ant-design-vue/es/date-picker/locale/zh_CN';
export default {
    data() {
        return {
            locale,
            IS_PAGE                     : true,
            query                       : {

            },
            list                        : [],
            search_ing                  : false,
        };
    },
    async unmounted(){

    },
    async mounted() {
        if (this.organization){
            this.search(0);
        }
    },
    methods: {

        async search(skip=0) {

        },
        async onPanelChange(e){

        },
    },
};
</script>

<template>
    <div class="c-list c-screen">
        <CHead :right="[{icon:(organization && organization.avatar)?organization.avatar:'icon-menu',event:'navbar-show'}]">
            <a-input v-model:value="query.keyword" placeholder="日程搜索" @pressEnter="search(0)">
                <template #addonAfter>+日程</template>
            </a-input>
        </CHead>
        <div class="c-scoll">
            <a-calendar :locale="locale"> </a-calendar>
        </div>
    </div>
    <!-- <router-view></router-view> -->
</template>

<style lang="scss" scoped></style>
