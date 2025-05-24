<script>
import CoverImage from '../../../components/CoverImage.vue';
import Time from '../../../common/utils/Time';

export default {
    components: {CoverImage},
    data() {
        return {
            IS_PAGE                     : true,
            PAGESHOW                    : false,
            form                        : {
                name                    : '',
                slogan                  : '',
            },
            accept                      : false,
            preview_avatar              : '',

            submit_ing                  : false,
        };
    },
    async mounted() {
        this.PAGESHOW                   = true;
    },
    methods: {
        async submit(data){
            this.submit_ing             = true;
            // 创建组织
            try{
                let post                    = Object.assign({
                },this.form);
                data                        = await this.$request.post("/client/organization/create", post);
                let organization            = data.data.organization;
                await Time.delay(1);
                // 更新组织头像
                if(this.preview_avatar){
                    data                    = await this.$request.post("/client/organization/upavatar", {
                        organization_id     : organization._id,
                        avatar              : this.$refs['file'].file,
                    },{headers:{'Content-Type': 'multipart/form-data'}});
                    organization.avatar     = data.data.avatar
                }
                // 切换至该组织
                await this.$request.post("/client/organization/switch", {
                    organization_id         : organization._id
                });
                // 刷新重载
                await Time.delay(1);
                this.$EventBus.emit('organization-created', { organization });
                this.$EventBus.emit('organization-switch', { organization });
            }catch(e){
                this.submit_ing         = false;
                console.error(e)
            }
        },
        async selectavatar({target}){
            let file = target.files[0]
            let reader                  = new FileReader();
            reader.onload=(e)=> {
                this.preview_avatar     = e.target.result;
            };
            reader.readAsDataURL(file);
        }
    },
};
</script>

<template>
    <div class="c-body c-screen" :class="{show:PAGESHOW}">
        <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title">创建组织</div>
            <div class="c-options">
                <div class="iconfont icon-more icon-menu"></div>
            </div>
        </CHead>
        <div class="c-scoll c-pd c-wd">
            <a-form class="c-form" :model="form" name="basic" :label-col="{ span: col[0] }" :wrapper-col="{ span: col[1] }" autocomplete="off" @finish="submit">
                <a-form-item label="Logo" name="preview_avatar">
                    <CFile ref="file" @change="selectavatar" :autoSubmit="false">
                        <template v-slot:preview>
                            <CoverImage :src="preview_avatar" :width="100" :height="100" />
                        </template>
                    </CFile>
                </a-form-item>

                <a-form-item label="组织名称" name="name" :rules="[{ required: true, pattern: /^.{3,20}$/, message: '组织名称需要3~20个字!' }]">
                    <a-input v-model:value="form.name" :maxlength="12" placeholder="组织名称需要3~20个字!" />
                </a-form-item>

                <a-form-item label="标语口号" name="slogan" :rules="[{ pattern: /^.{0,50}$/,message: '标语口号需要50个字以内!' }]">
                    <a-input v-model:value="form.slogan" :maxlength="50" placeholder="好的标语口号是组织的原动力！" />
                </a-form-item>

                <a-form-item name="accept" :wrapper-col="{ offset: col[0], span: col[1] }">
                    <a-checkbox v-model:checked="accept">我接受 <a-button type="link">服务协议</a-button> 和 <a-button type="link">隐私协议</a-button></a-checkbox>
                </a-form-item>

                <a-form-item :wrapper-col="{ offset: col[0], span: col[1] }">
                    <a-button type="primary" html-type="submit" :disabled="!accept" :loading="submit_ing">确定创建</a-button>
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
}
</style>
