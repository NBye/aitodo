<script>
import Time from '../../../common/utils/Time';

export default {
    components: {},
    data() {
        return {
            IS_PAGE                     : true,
            PAGESHOW                    : false,
            form_base                   : {},
            form_join                   : {},
            form_salary                 : {},
            form_settings               : {},
            form_template               : {},
            form_account                : {},

            item                        : null,
            preview_avatar              : '',
            submit_ing                  : false,

            segmented_list              : [],
            segmented                   : '',
        };
    },
    async mounted() {
        this.PAGESHOW                   = true;
        this.loadInfo()
    },
    methods: {
        async loadInfo(){
            let user_id                 = this.$route.query.user_id;
            let {data}                  = await this.$request.post("/client/user/info", {
                organization_id         : this.organization._id,
                user_id
            }).finally(()=>this.loading = false);
            this.item                   = data.user;
            let segmented_list          = []

            // 只能修改自己的，或者 修改组织内部创建的AI
            if(data.user._id==this.user._id || (data.user.role=='assistant' && data.user.creator_organization_id==this.organization._id) ){
                segmented_list.push({value:'base'     ,payload:'基础信息'});
            }
            // 组织内的所有人都可以修改备注信息
            if(true){
                segmented_list.push({value:'join'     ,payload:'组内信息'});
            }
            // 只能修改组织内部创建的AI机器人
            if(data.user.role=='assistant' && data.user.creator_organization_id==this.organization._id){
                segmented_list.push({value:'salary'   ,payload:'薪资设定'});
                segmented_list.push({value:'settings' ,payload:'参数设置'});
                segmented_list.push({value:'template' ,payload:'模板设置'});
            }
            // 只有自己才能修改自己的登录信息
            if(data.user._id==this.user._id){
                segmented_list.push({value:'account'  ,payload:'登录设置'});
            }
            this.segmented_list         = segmented_list;
            if(this.$route.query.tab){
                this.segmented          = this.$route.query.tab;
            } else {
                this.segmented          = segmented_list[0].value;
            }


            this.form_base.avatar       = data.user.avatar;
            this.form_base.nickname     = data.user.nickname;
            this.form_base.slogan       = data.user.slogan;
            this.form_base.gender       = data.user.gender;
            this.form_base.birthday     = data.user.birthday;
            this.form_base.introduction = data.user.introduction;


            this.form_join.aliasname    = data.user.join_info.aliasname;
            this.form_join.remark       = data.user.join_info.remark;

            this.form_salary            = data.user.salary;
            this.form_settings          = data.user.settings;
            this.form_template          = data.user.settings;

            this.form_account.username  = data.user.username || '';
            this.form_account.password  = data.user.password || '';
        },
        async submit(data){
            if(this.segmented=='base'){
                this.form_base.introduction = this.$refs.markdown.getValue();
            }
            this.submit_ing             = true;
            try{
                let post                = Object.assign({
                    group               : this.segmented,
                    user_id             : this.item._id,
                    organization_id     : this.organization._id,
                },this['form_'+this.segmented]);
                data                    = await this.$request.post("/client/user/upset", post);
                let user                = data.data.user;
                await Time.delay(1)
                this.$EventBus.emit('user-update', { user });
                this.submit_ing         = false;
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
            this.form_base['avatar']    = file;
        },
    },
};
</script>

<template>
    <div class="c-body c-screen" :class="{show:PAGESHOW}">
        <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title">编辑用户信息</div>
            <div class="c-options">
                <div class="iconfont icon-more icon-menu"></div>
            </div>
        </CHead>
        <div class="c-scoll c-pd c-wd">
            <div v-if="item" class="c-form" style="padding: 0;">
                <a-segmented v-model:value="segmented" :options="segmented_list" block>
                    <template #label="{ payload }">
                        <div>{{ payload }}</div>
                    </template>
                </a-segmented>
            </div>
            <a-form v-if="item && segmented=='base'" class="c-form" :layout="FORM_LAYOUT" :model="form_base" name="basic" :label-col="{ span: col[0] }" :wrapper-col="{ span: col[1] }" autocomplete="off" @finish="submit">
                <a-form-item label="Logo">
                    <CFile ref="file" @change="selectavatar" :autoSubmit="false">
                        <template #initial>
                            <CoverImage :src="form_base.avatar" :width="100" :height="100" :alt="item.nickname" />
                        </template>
                        <template #preview>
                            <CoverImage :src="preview_avatar" :width="100" :height="100" />
                        </template>
                    </CFile>
                </a-form-item>
                <a-form-item label="成员昵称" name="nickname" :rules="[{ required: true, pattern: /^.{2,12}$/, message: '名称需要2~12个字!' }]">
                    <a-input v-model:value="form_base.nickname" :maxlength="12" placeholder="名称需要1~12个字!" />
                </a-form-item>
                <a-form-item label="成员口号" name="slogan" :rules="[{ pattern: /^.{0,50}$/,message: '标语口号需要50个字以内!' }]">
                    <a-input v-model:value="form_base.slogan" :maxlength="50" placeholder="好的标语口号是组织的原动力！" />
                </a-form-item>
                <a-form-item label="出生日期" name="birthday">
                    <a-input type="date" v-model:value="form_base.birthday" />
                </a-form-item>
                <a-form-item label="性别" name="gender">
                    <a-select v-model:value="form_base.gender" style="width: 100%">
                        <a-select-option value="--">未知</a-select-option>
                        <a-select-option value="xy">男</a-select-option>
                        <a-select-option value="xx">女</a-select-option>
                    </a-select>
                </a-form-item>
                <a-form-item label="自我介绍">
                    <Markdown ref="markdown" :content="form_base.introduction" placeholder="编辑个人信息，展现自我风采。支持Markdown语法。" />
                </a-form-item>
                <a-form-item :wrapper-col="{ offset: col[0], span: col[1] }">
                    <a-button type="primary" html-type="submit" :loading="submit_ing">保存</a-button>
                </a-form-item>
            </a-form>

            <a-form v-if="item && segmented=='join'" class="c-form" :layout="FORM_LAYOUT" :model="form_join" name="basic" :label-col="{ span: col[0] }" :wrapper-col="{ span: col[1] }" autocomplete="off" @finish="submit">
                <a-form-item label="组内别名" name="aliasname">
                    <a-input v-model:value="form_join.aliasname" :maxlength="12" placeholder="成员名称需要12个字以内!" />
                </a-form-item>
                <a-form-item label="人员备注" name="remark">
                    <a-textarea v-model:value="form_join.remark" :maxlength="50" placeholder="50各字以内" />
                </a-form-item>
                <a-form-item :wrapper-col="{ offset: col[0], span: col[1] }">
                    <a-button type="primary" html-type="submit" :loading="submit_ing">保存</a-button>
                </a-form-item>
            </a-form>

            <a-form v-if="item && segmented=='salary'" class="c-form" :layout="FORM_LAYOUT" :model="form_salary" name="basic" :label-col="{ span: col[0] }" :wrapper-col="{ span: col[1] }" autocomplete="off" @finish="submit">
                <a-form-item label="按年">
                    <a-input-number class="number" v-model:value="form_salary.y.price" :min="0" :max="10000" :precision="2" placeholder="按年收费" />
                    <a-switch v-model:checked="form_salary.y.enable" />
                </a-form-item>
                <a-form-item label="按月">
                    <a-input-number class="number" v-model:value="form_salary.m.price" :min="0" :max="10000" :precision="2" placeholder="按月收费" />
                    <a-switch v-model:checked="form_salary.m.enable" />
                </a-form-item>
                <a-form-item label="按日">
                    <a-input-number class="number" v-model:value="form_salary.d.price" :min="0" :max="10000" :precision="2" placeholder="按日收费" />
                    <a-switch v-model:checked="form_salary.d.enable" />
                </a-form-item>
                <a-form-item label="按小时">
                    <a-input-number class="number" v-model:value="form_salary.h.price" :min="0" :max="10000" :precision="2" placeholder="按小时收费" />
                    <a-switch v-model:checked="form_salary.h.enable" />
                </a-form-item>
                <a-form-item :wrapper-col="{ offset: col[0], span: col[1] }">
                    <a-button type="primary" html-type="submit" :loading="submit_ing">保存</a-button>
                </a-form-item>
                <a-form-item :wrapper-col="{ offset: col[0], span: col[1] }"> 平台收取薪资的20%，作为平台服务费。 </a-form-item>
            </a-form>

            <a-form v-if="item && segmented=='settings'" class="c-form" :layout="FORM_LAYOUT" :model="form_settings" name="basic" :label-col="{ span: col[0] }" :wrapper-col="{ span: col[1] }" autocomplete="off" @finish="submit">
                <a-form-item label="消息轮次" name="message_size" :rules="[{ required: true}]">
                    <a-input-number v-model:value="form_settings.message_size" :min="0" :max="2000" placeholder="AI分析聊天记录的长度" style="width:100%" />
                </a-form-item>
                <!-- <a-form-item label="思考深广" name="thoughtful" :rules="[{ required: true}]">
                    <a-input-number v-model:value="form_settings.thoughtful" :min="0" :max="20" placeholder="根据对话思考应用自身能力的广度" style="width:100%" />
                </a-form-item> -->
                <a-form-item label="上下文长度" name="num_ctx" :rules="[{ required: true}]">
                    <a-input-number v-model:value="form_settings.num_ctx" :min="0" :max="102400" placeholder="AI上下文长度" style="width:100%" />
                </a-form-item>
                <a-form-item label="迭代深度" name="max_iterations" :rules="[{ required: true}]">
                    <a-input-number v-model:value="form_settings.max_iterations" :min="0" :max="100" placeholder="对自身回答检查补充思考最大次数" style="width:100%" />
                </a-form-item>
                <a-form-item label="情感创意" name="temperature" :rules="[{ required: true}]">
                    <a-input-number v-model:value="form_settings.temperature" :min="0" :max="1" placeholder="0~1越大越有创意" style="width:100%" />
                </a-form-item>
                <a-form-item label="意图模型" name="model" :rules="[{ required: true,message: '请选择意图模型'}]">
                    <a-cascader v-model:value="form_settings.model" :options="modelsFilter('tools')" placeholder="思考理解分类模型" />
                </a-form-item>
                <a-form-item label="视觉模型" name="visionmodel" :rules="[{ required: true,message: '请选择视觉模型'}]">
                    <a-cascader v-model:value="form_settings.visionmodel" :options="modelsFilter('vision')" placeholder="理解图片视频模型" />
                </a-form-item>
                <a-form-item label="语言模型" name="textmodel" :rules="[{ required: true,message: '请选择语言模型'}]">
                    <a-cascader v-model:value="form_settings.textmodel" :options="modelsFilter('text')" placeholder="生成对话文案模型" />
                </a-form-item>
                <a-form-item label="开场对话" name="opening_speech" help="AI加入会话后的第一句发言。">
                    <a-textarea v-model:value="form_settings.opening_speech" :autoSize="{minRows:2,maxRows:10}" :maxlength="1000" placeholder="对话开场白" style="width:100%" />
                </a-form-item>
                
                <a-form-item label="提示引导" name="prompts" help="会显示在对话输入框上边。">
                    <a-textarea v-model:value="form_settings.prompts" :autoSize="{minRows:2,maxRows:10}" :maxlength="1000" placeholder="提示引导一行一个问题" style="width:100%" />
                </a-form-item>

                <a-form-item :wrapper-col="{ offset: col[0], span: col[1] }">
                    <a-button type="primary" html-type="submit" :loading="submit_ing">保存</a-button>
                </a-form-item>
            </a-form>
            <a-form v-if="item && segmented=='template'" class="c-form" :layout="FORM_LAYOUT" :model="form_template" name="basic" :label-col="{ span: col[0] }" :wrapper-col="{ span: col[1] }" autocomplete="off" @finish="submit">
                <a-form-item label="注">
                    <div>
                        模板对于AI至关重要，设置模板内容可以让AI有着不同的智力水平。不同区域的模板有着不同的参数可用，缺省可是使用全局设置。
                        <a-button type="link" size="small" @click="this.windowOpen({url:'/document/particulars?document_id=GuuHAJcBu45vkOx9_Gkh'});">查看文档</a-button>
                    </div>
                </a-form-item>
                <a-form-item label="人设定义" name="definition">
                    <template #help>对AI的人设定义，以及对整个聊天室内会话内的全局定义。</template>
                    <a-textarea v-model:value="form_template.definition" :autoSize="{minRows:2,maxRows:10}" :maxlength="2000" :placeholder="constant.templates.definition" style="width:100%" />
                </a-form-item>
                <a-form-item label="涉及感知" name="template_related_me">
                    <template #help>在多人聊天中，未指定自己时，感知与自我相关时，主动发言。 </template>
                    <a-textarea v-model:value="form_template.template_related_me" :autoSize="{minRows:2,maxRows:10}" :maxlength="2000" :placeholder="constant.templates.related_me" style="width:100%" />
                </a-form-item>

                <a-form-item label="工具嵌入" name="template_embeddings">
                    <template #help>大模型调用工具的数据会以system消息的方式嵌入． </template>
                    <a-textarea v-model:value="form_template.template_embeddings"  :autoSize="{minRows:2,maxRows:10}" :maxlength="2000" :placeholder="constant.templates.embeddings"  style="width:100%" />
                </a-form-item>
                <a-form-item label="深度迭代" name="template_checkreply">
                    <template #help>大模型输出后，对自己的输出进行思考，是否有补充和追问回答等。 </template>
                    <a-textarea v-model:value="form_template.template_checkreply"  :autoSize="{minRows:2,maxRows:10}" :maxlength="2000" :placeholder="constant.templates.checkreply"  style="width:100%" />
                </a-form-item>

                <a-form-item label="推荐问题" name="template_recprompts">
                    <template #help>大模型输出后，对自己的输出，推荐适合的问题。 </template>
                    <a-textarea v-model:value="form_template.template_recprompts"  :autoSize="{minRows:2,maxRows:10}" :maxlength="2000" :placeholder="constant.templates.recprompts"  style="width:100%" />
                </a-form-item>

                <a-form-item label="深度思考" name="template_understand">
                    <template #help>大模型对用户所说的话进行补全，将问题完善,提高回答的精准。 </template>
                    <a-textarea v-model:value="form_template.template_understand" :autoSize="{minRows:2,maxRows:10}" :maxlength="2000" :placeholder="constant.templates.understand" style="width:100%" />
                </a-form-item>
                <a-form-item :wrapper-col="{ offset: col[0], span: col[1] }">
                    <a-button type="primary" html-type="submit" :loading="submit_ing">保存</a-button>
                </a-form-item>
            </a-form>

            <a-form v-if="item && segmented=='account'" class="c-form" :layout="FORM_LAYOUT" :model="form_account" name="basic" :label-col="{ span: col[0] }" :wrapper-col="{ span: col[1] }" autocomplete="off" @finish="submit">
                <!-- <a-form-item label="登录账号" name="username" :rules="[{ required: true, pattern: /^.{4,20}$/, message: '账号长度为4~20个字符' }]">
                    <a-input v-model:value="form_account.username" :maxlength="20" placeholder="可以使用账号登录" />
                </a-form-item> -->
                <a-form-item label="新密码" name="password" :rules="[{ required: true, pattern: /^.{6,50}$/, message: '密码长度为6~50个字符' }]">
                    <a-input-password v-model:value="form_account.password" :maxlength="50" placeholder="登录密码" />
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

    .number{
        width: calc(100% - 55px);
        margin-right: 0.5rem;
    }
}
</style>
