<script>
import locale from 'ant-design-vue/es/date-picker/locale/zh_CN'
import CoverImage from '../../../components/CoverImage.vue';
import Empty from '../../../components/Empty.vue';

import IDate from '../../../common/utils/IDate';


export default {
    components: { CoverImage, Empty },
    data() {
        return {
            IS_PAGE: true,
            PAGESHOW: false,
            locale,
            query: {
                keyword: '',
                skip: 0,
                size: 50,
                sort: 'created asc',
            },
            list: [],
            search_ing: false,
            generate_ing: false,
        };
    },
    async mounted() {
        // this.$vueClipboard.config({ autoSetContainer: true });
    },
    watch: {
        '$route.query': {
            handler() {
                this.PAGESHOW = true;
                this.search(0)
            },
            immediate: true,
        },
    },
    methods: {
        async search(skip = 0) {
            if (this.search_ing) {
                return;
            }
            this.query.skip = skip;
            this.search_ing = true;
            let { data } = await this.$request.post("/client/secret/search", {
                ...this.query,
                organization_id: this.$route.query.organization_id,
            }, {}).finally(() => this.search_ing = false);
            data.list.forEach((item) => {

            });
            if (this.query.skip == 0) {
                this.list = data.list;
            } else {
                data.list.forEach((item) => {
                    this.list.push(item);
                });
            }
        },
        async generate() {
            let date = new Date()
            date.setFullYear(date.getFullYear() + 10)
            let post = await this.confirm({
                title: '生成密钥', content: [
                    {
                        name: 'description', value: '', label: '描述', type: 'input', maxlength: 20, placeholder: '密钥作用4~20个字', reg: '/^.{4,20}$/'
                    },
                    {
                        name: 'expired', value: IDate.format('yyyy-mm-dd hh:ii:ss', date), label: '过期时间', type: 'input:datetime-local'
                    },
                ]
            });
            if (!post || !post.description) {
                return;
            }
            this.generate_ing = true;
            let { data } = await this.$request.post("/client/secret/create", {
                ...post,
                organization_id: this.$route.query.organization_id,
            }, {}).finally(() => this.generate_ing = false);
            this.list.push(data.secret);
        },
        async del(item) {
            if (!await this.confirm({ title: '确定删除?', content: '删除后无法恢复,确定删除？' })) {
                return false;
            }
            await this.$request.post("/client/secret/destroy", {
                secret_id: item._id,
                organization_id: item.organization_id,
            });
            this.listRemoveItem(this.list, item);
        },
        async edit(item) {
            let post = await this.confirm({
                title: '修改密钥信息', content: [
                    {
                        name: 'description', value: item.description, label: '作用描述', type: 'input', maxlength: 20, placeholder: '密钥作用4~20个字', reg: '/^.{4,20}$/'
                    },
                    {
                        name: 'expired', value: item.expired, label: '过期时间', type: 'input:datetime-local'
                    },
                ]
            });
            if (!post || !post.description) {
                return;
            }
            this.generate_ing = true;
            await this.$request.post("/client/secret/upset", {
                ...post,
                secret_id: item._id,
                organization_id: this.$route.query.organization_id,
            }, {}).finally(() => this.generate_ing = false);
            Object.assign(item, post);
        },
        async upset(item, options) {
            await this.$request.post("/client/secret/upset", {
                ...options,
                secret_id: item._id,
                organization_id: this.$route.query.organization_id,
            });
        },
    },
};
</script>

<template>
<div class="c-body c-screen am faster" :class="{ show: PAGESHOW }">
    <CHead class="c-left c-line" :right="[{ icon: 'icon-back', event: () => linkBack(-1) }]">
        <div class="c-title">API 密钥管理</div>
        <div class="c-options">
            <div class="iconfont icon-more icon-menu"></div>
        </div>
    </CHead>
    <div class="c-scoll c-pd c-wd">
        <a-empty v-if="search_ing" :description="'数据加载中...'" />
        <div class="c-form pr">
            <a-button :loading="generate_ing" @click="generate">生成密钥</a-button>
            <a-list item-layout="horizontal" :data-source="list" size="small" :locale="{ emptyText: '暂无数据' }">
                <template #renderItem="{ item }">
                    <a-list-item>
                        <template #actions>
                            <a-switch v-model:checked="item.enabled" @change="upset(item, { enabled: item.enabled })"
                                size="small" />

                            <a-button size="samll" type="link" @click="edit(item)">
                                <template #icon>
                                    <EditOutlined />
                                </template>
                            </a-button>
                            <a-button size="samll" type="link" @click="del(item)">
                                <template #icon>
                                    <DeleteOutlined />
                                </template>
                            </a-button>
                        </template>
                        <a-skeleton :title="false" :loading="false" active>
                            <a-list-item-meta :description="`${item.description}，expired: ${item.expired}`">
                                <template #title>
                                    <Clipboard class="hand" :text="item.key"
                                        @clipboard-success="() => aMessage().success('已复制到粘贴板')">
                                        {{ item.key.substr(0, 8) }}
                                        {{ item.key.substr(8, 16).replace(/./g, '*') }}
                                        {{ item.key.substr(-12) }}
                                    </Clipboard>
                                </template>
                            </a-list-item-meta>
                        </a-skeleton>
                    </a-list-item>
                </template>
            </a-list>
        </div>
    </div>
</div>
</template>

<style lang="scss" scoped>
.ant-btn-link {
    padding: 0;
}

.ant-list-item {
    padding-left: 0;
    padding-right: 0;
}
</style>
