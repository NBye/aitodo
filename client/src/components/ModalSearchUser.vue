<script>
export default {
    props                               : {
        title                           : {
            type                        : String,
            default                     : '搜索成员',
        },
        query                           : {
            type                        : Object,
            default                     : {},
        },
        disabledUserIdList              : {
            type                        : Array,
            default                     : [],
        },
    },
    data() {
        return {
            state                       : false,
            searching                   : false,
            submiting                   : false,
            list                        : [],
            keyword                     : '',
            size                        : 5,
            skip                        : 0,
        };
    },
    methods: {
        async show(){
            this.state                  = true;
            this.submiting              = false;
            this.search();
        },
        async hide(){
            this.state                  = false;
            this.submiting              = false;
        },
        async search(){
            this.searching              = true;
            let {data}                  = await this.$request.post("/client/user/search", {
                keyword                 : this.keyword,
                size                    : this.size,
                skip                    : this.skip,
                ...this.query
            }).finally(()=>this.searching = false );
            data.list.forEach(item=>item.checked=this.disabledUserIdList.indexOf(item._id)>-1);
            this.list                   = data.list;
        },
        async entity(){
            let users                   = [];
            this.list.forEach(item=>{
                if(item.checked && this.disabledUserIdList.indexOf(item._id)==-1){
                    users.push(item);
                }
            });
            if(users.length<1){
                return this.aMessage().warn('请选择用户')
            }
            this.submiting              = true;
            this.$emit('submit', users);
        },
        async choose(item){
            if(this.disabledUserIdList.indexOf(item._id)==-1 ){
                item.checked=!item.checked
            }
        },
    },
};
</script>

<template>
    <a-modal v-model:open="state" :title="title">
        <div style="padding:1rem 1.5rem;">
            <a-input-search v-model:value="keyword" placeholder="搜索名称" :loading="searching" enter-button @search="search" />
        </div>
        <template #footer>
            <a-button @click="hide()">取消</a-button>
            <a-button type="primary" @click="entity()" :loading="submiting" style="margin-right:2rem">确定</a-button>
        </template>
        <a-list item-layout="horizontal" :data-source="list" size="small">
            <template #renderItem="{ item }">
                <a-list-item class="hand no-select" @click="choose(item)">
                    <template #actions>
                        <a-checkbox @click.stop v-model:checked="item.checked" :disabled="disabledUserIdList.indexOf(item._id)>-1"></a-checkbox>
                    </template>
                    <a-skeleton avatar :title="false" :loading="false" active>
                        <a-list-item-meta :description="item.join_info?item.join_info.remark:item.slogan">
                            <template #title>
                                <a>{{ item.nickname }}</a>
                            </template>
                            <template #avatar>
                                <a-avatar :src="cutImgUrl(item.avatar,{w:100,h:100,alt:item.nickname})" />
                            </template>
                        </a-list-item-meta>
                    </a-skeleton>
                </a-list-item>
            </template>
        </a-list>
    </a-modal>
</template>

<style lang="scss" scoped></style>
