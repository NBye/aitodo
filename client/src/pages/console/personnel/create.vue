<script>
import Time from '../../../common/utils/Time';

export default {
    components: {},
    data() {
        return {
            IS_PAGE                     : true,
            PAGESHOW                    : false,
            form                        : {
                avatar                  : '',
                nickname                : '',
                slogan                  : '',
                gender                  : '--',
                birthday                : '',
                introduction            : '',
                settings                : {
                    "model"             : [],
                    "visionmodel"       : [],
                    "textmodel"         : [],

                    "definition"        : "",
                    "template_related_me"        : "",
                    "template_embeddings"        : "",

                    "opening_speech"    : "",
                    
                    "temperature"       : 0.7,
                    "num_ctx"           : 4096,
                    "max_iterations"    : 1,
                    "message_size"      : 20,
                    "thoughtful"        : 5,


                },
            },
            preview_avatar              : '',
            steps                       : [
                {
                    title               : '基础信息',
                },
                {
                    title               : 'AI设置',
                },
            ],
            step                        : 0,
            submit_ing                  : false,
        };
    },
    async mounted() {
        this.PAGESHOW                   = true;
    },
    methods: {
        async submit(data){
            if (this.step != this.steps.length-1){
                return this.step++;
            }
            this.form.introduction = this.$refs.markdown.getValue();
            this.submit_ing             = true;
            try{
                data                    = await this.$request.post("/client/organization/createAssistant", this.form);
                let user                = data.data.user;
                await Time.delay(1)
                if (this.avatar_file){
                    data                = await this.$request.post("/client/user/upset", {
                        organization_id : this.organization._id,
                        user_id         : user._id,
                        group           : 'base',
                        avatar          : this.avatar_file,
                    },{
                        SUCCESS_TIPS_ENABLE : false,
                    });
                    Object.assign(user,data.data.user)
                    await Time.delay(1)
                }
                this.$EventBus.emit('organization-user-invite', { user });
                this.submit_ing         = false;
                this.link({path:'/console/personnel/details',query:{user_id:user._id}},'replace');
            } catch (e){
                this.submit_ing         = false;
            }
        },
        async selectavatar({target}){
            let file = target.files[0]
            let reader                  = new FileReader();
            reader.onload=(e)=> {
                this.preview_avatar     = e.target.result;
            };
            reader.readAsDataURL(file);
            this.avatar_file            = file
        },
        async switchStep(e){
            console.log(e)
        },
    },
};
</script>

<template>
    <div class="c-body c-screen" :class="{show:PAGESHOW}">
        <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title">创建AI员工</div>
            <div class="c-options">
                <div class="iconfont icon-more icon-menu"></div>
            </div>
        </CHead>
        <div class="c-scoll c-pd c-wd">
            <div class="c-form" style="padding: 0;">
                <a-steps v-model:current="step" :items="steps" direction="horizontal" :responsive="false" @change="switchStep"></a-steps>
            </div>
            <a-form v-show="step==0" class="c-form" :layout="FORM_LAYOUT" :model="form" name="basic" :label-col="{ span: col[0] }" :wrapper-col="{ span: col[1] }" autocomplete="off" @finish="submit">
                <a-form-item label="Logo">
                    <CFile ref="file" @change="selectavatar" :autoSubmit="false">
                        <template #preview>
                            <CoverImage :src="preview_avatar" :width="100" :height="100" />
                        </template>
                    </CFile>
                </a-form-item>
                <a-form-item label="AI昵称" name="nickname" :rules="[{ required: true, pattern: /^.{2,20}$/, message: '名称需要2~20个字!' }]">
                    <a-input v-model:value="form.nickname" :maxlength="12" placeholder="名称需要1~12个字!" />
                </a-form-item>
                <a-form-item label="个性签名" name="slogan" :rules="[{ pattern: /^.{0,50}$/,message: '标语口号需要50个字以内!' }]">
                    <a-input v-model:value="form.slogan" :maxlength="50" placeholder="好的标语口号是AI的原动力！" />
                </a-form-item>
                <a-form-item label="性别" name="gender">
                    <a-select v-model:value="form.gender" style="width: 100%">
                        <a-select-option value="--">未知</a-select-option>
                        <a-select-option value="xy">男</a-select-option>
                        <a-select-option value="xx">女</a-select-option>
                    </a-select>
                </a-form-item>
                <a-form-item label="自我介绍">
                    <Markdown ref="markdown" :content="form.introduction" placeholder="编辑个人信息，展现自我风采。支持Markdown语法。" />
                </a-form-item>
                <a-form-item :wrapper-col="{ offset: col[0], span: col[1] }">
                    <a-button type="primary" html-type="submit">下一步</a-button>
                </a-form-item>
            </a-form>
            <a-form v-show="step==1" class="c-form" :layout="FORM_LAYOUT" :model="form.settings" name="basic" :label-col="{ span: col[0] }" :wrapper-col="{ span: col[1] }" autocomplete="off" @finish="submit">
                <a-form-item label="消息轮次" name="message_size" :rules="[{ required: true}]">
                    <a-input-number v-model:value="form.settings.message_size" :min="0" :max="2000" placeholder="AI分析聊天记录的长度" style="width:100%" />
                </a-form-item>
                <!-- <a-form-item label="思考深广" name="thoughtful" :rules="[{ required: true}]">
                    <a-input-number v-model:value="form.settings.thoughtful" :min="0" :max="20" placeholder="根据对话思考应用自身能力的广度" style="width:100%" />
                </a-form-item> -->
                <a-form-item label="上下文长度" name="num_ctx" :rules="[{ required: true}]">
                    <a-input-number v-model:value="form.settings.num_ctx" :min="0" :max="102400" placeholder="AI上下文长度" style="width:100%" />
                </a-form-item>
                <a-form-item label="迭代深度" name="max_iterations" :rules="[{ required: true}]">
                    <a-input-number v-model:value="form.settings.max_iterations" :min="0" :max="100" placeholder="对自身回答检查补充思考最大次数" style="width:100%" />
                </a-form-item>
                <a-form-item label="情感创意" name="temperature" :rules="[{ required: true}]">
                    <a-input-number v-model:value="form.settings.temperature" :min="0" :max="1" placeholder="0~1越大越有创意" style="width:100%" />
                </a-form-item>
                <a-form-item label="意图模型" name="model" :rules="[{ required: true,message: '请选择意图模型'}]">
                    <a-cascader v-model:value="form.settings.model" :options="modelsFilter('tools')" placeholder="思考理解分类模型" />
                </a-form-item>
                <a-form-item label="视觉模型" name="visionmodel" :rules="[{ required: true,message: '请选择视觉模型'}]">
                    <a-cascader v-model:value="form.settings.visionmodel" :options="modelsFilter('vision')" placeholder="理解图片视频模型" />
                </a-form-item>
                <a-form-item label="语言模型" name="textmodel" :rules="[{ required: true,message: '请选择语言模型'}]">
                    <a-cascader v-model:value="form.settings.textmodel" :options="modelsFilter('text')" placeholder="生成对话文案模型" />
                </a-form-item>
                <a-form-item :wrapper-col="{ offset: col[0], span: col[1] }">
                    <a-button type="primary" html-type="submit" :loading="submit_ing">提交</a-button>
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

    .number{
        width: calc(100% - 55px);
        margin-right: 0.5rem;
    }
}
</style>
