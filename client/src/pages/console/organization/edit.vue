<script>
import Time from '../../../common/utils/Time';

export default {
    components: {},
    data() {
        return {
            IS_PAGE                     : true,
            PAGESHOW                    : false,

            segmented_list              : [],
            segmented                   : '',
            form_base                   : {},
            form_model                  : {},

            item                        : null,
            preview_avatar              : '',
            submit_ing                  : false,
        };
    },
    async mounted() {
        this.PAGESHOW                   = true;
        this.loadInfo()
    },
    methods: {
        async loadInfo(){
            let organization_id         = this.$route.query.organization_id;
            let {data}                  = await this.$request.post("/client/organization/info", {
                organization_id
            }).finally(()=>this.loading = false);
            Object.assign(this,data);
            this.item                   = data.organization;

            let segmented_list          = []
            segmented_list.push({value:'base'     ,payload:'基础信息'});
            segmented_list.push({value:'model'    ,payload:'大模型源'});


            this.form_base.name         = data.organization.name;
            this.form_base.slogan       = data.organization.slogan;


        },
        async submit(data){
            this.submit_ing             = true;
            try{
                let post                = Object.assign({
                    organization_id     : this.item._id,
                    introduction        : this.$refs.markdown.getValue(),
                },this.form_base);
                data                    = await this.$request.post("/client/organization/upset", post);
                let organization        = data.data.organization;
                await Time.delay(1)
                this.$EventBus.emit('organization-update', { organization });
                this.submit_ing         = false;
                this.linkBack()
            } catch (e){
                this.submit_ing         = false;
                console.error(e);
            }
        },
        async selectavatar({target}){
            let file = target.files[0]
            let reader                  = new FileReader();
            reader.onload=(e)=> {
                this.preview_avatar     = e.target.result;
            };
            reader.readAsDataURL(file);
            this.form_base['avatar']         = file;
        }
    },
};
</script>

<template>
    <div class="c-body c-screen" :class="{show:PAGESHOW}">
        <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title">编辑设置</div>
            <div class="c-options">
                <div class="iconfont icon-more icon-menu"></div>
            </div>
        </CHead>
        <div class="c-scoll c-pd c-wd">
            <a-form class="c-form" :layout="FORM_LAYOUT" :model="form_base" name="basic" :label-col="{ span: col[0] }" :wrapper-col="{ span: col[1] }" autocomplete="off" @finish="submit">
                <a-form-item label="Logo">
                    <CFile ref="file" @change="selectavatar" :autoSubmit="false">
                        <template #initial v-if="item">
                            <CoverImage :src="item.avatar" :width="100" :height="100" :alt="item.name" />
                        </template>
                        <template #preview>
                            <CoverImage :src="preview_avatar" :width="100" :height="100" />
                        </template>
                    </CFile>
                </a-form-item>

                <a-form-item label="组织名称" name="name" :rules="[{ required: true, pattern: /^.{3,20}$/, message: '组织名称需要3~20个字!' }]">
                    <a-input v-model:value="form_base.name" :maxlength="12" placeholder="组织名称需要3~20个字!" />
                </a-form-item>

                <a-form-item label="标语口号" name="slogan" :rules="[{ pattern: /^.{0,50}$/,message: '标语口号需要50个字以内!' }]">
                    <a-input v-model:value="form_base.slogan" :maxlength="50" placeholder="好的标语口号是组织的原动力！" />
                </a-form-item>

                <a-form-item label="组织介绍" v-if="item">
                    <Markdown ref="markdown" :content="item.introduction" placeholder="编辑组织信息，体现组织风采。支持Markdown语法。"/>
                </a-form-item>

                <a-form-item :wrapper-col="{ offset: col[0], span: col[1] }">
                    <a-button type="primary" html-type="submit" :loading="submit_ing">保存</a-button>
                </a-form-item>
            </a-form>
        </div>
    </div>
</template>

<style lang="scss" scoped>

.ant-btn-link {
    padding: 0;
}
.c-form{
    padding-top:10%;

    .vditor{

    }
}
</style>
