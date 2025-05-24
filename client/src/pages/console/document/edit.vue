<script>
import Time from '../../../common/utils/Time';

export default {
    components: {},
    data() {
        return {
            IS_PAGE                     : true,
            PAGESHOW                    : false,
            form                        : {
                _id                     : '',
                title                   : '',
                abstract                : '',
                text                    : '',
            },
            submit_ing                  : false,
        };
    },
    async mounted() {
        this.PAGESHOW                   = true;
        let document_id                 = this.$route.query.document_id;
        let {data}                      = await this.$request.post("/client/document/info", {
            document_id,
        }).finally(()=>this.loading = false);
        Object.assign(this.form,data.document);
    },
    methods: {
        async submit(data){
            this.submit_ing             = true;
            try{
                this.form.text          = this.$refs.markdown.getValue();
                data                    = await this.$request.post("/client/document/upset", {
                    document_id         : this.$route.query.document_id,
                    ...this.form
                });
                let document            = data.data.document;
                this.$EventBus.emit('document-update', { document });
                await Time.delay(1)
                this.submit_ing         = false;
                this.linkBack()
            } catch (e){
                this.submit_ing         = false;
                console.error(e)
            }
        },
    },
};
</script>

<template>
    <div class="c-body c-screen" :class="{show:PAGESHOW}">
        <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title">编辑文档</div>
            <div class="c-options">
                <div class="iconfont icon-more icon-menu"></div>
            </div>
        </CHead>
        <div class="c-scoll c-pd c-wd">
            <a-form v-if="form._id" class="c-form" :layout="FORM_LAYOUT" :model="form" name="basic" :label-col="{ span: col[0] }" :wrapper-col="{ span: col[1] }" autocomplete="off" @finish="submit">
                <a-form-item label="标题" name="title" :rules="[{ required: true, pattern: /^.{4,20}$/, message: '名称需要4~20个字!' }]">
                    <a-input v-model:value="form.title" :maxlength="20" placeholder="名称需要4~20个字!" />
                </a-form-item>
                <a-form-item label="摘要" name="abstract" :rules="[{ required: true, pattern: /^[\s\S]{0,200}$/,message: '描述需要200个字以内!' }]">
                    <a-textarea v-model:value="form.abstract" :rows="4" :maxlength="200" placeholder="描述需要200个字以内" />
                </a-form-item>
                <a-form-item label="内容">
                    <Markdown ref="markdown" :content="form.text" height="auto" placeholder="编辑文档内容，Markdown编辑器。"/>
                </a-form-item>
            </a-form>
            <a-affix :offset-bottom="40">
                <a-form class="c-form" style="padding-top: 0;">
                    <a-form-item :wrapper-col="{ offset: col[0], span: col[1] }">
                        <a-button type="primary" @click="submit()" :loading="submit_ing">提交</a-button>
                    </a-form-item>
                </a-form>
            </a-affix>
        </div>
    </div>
</template>

<style lang="scss" scoped>

.ant-btn-link {
    padding: 0;
}
.c-form{
    padding-top:10%;
}
</style>
