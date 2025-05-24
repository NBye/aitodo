<script>
import Time from '../../../common/utils/Time';
const mcp_placeholder=`{
    "command": "",
    "args": [],
    "env": {}
}`
export default {
    components: {},
    data() {
        return {
            IS_PAGE                     : true,
            PAGESHOW                    : false,
            form                        : {
                name                    : '',
                description             : '',
                type                    : 'custom', //custom | mcp
                settings                : mcp_placeholder,
                support                 : {
                    'PC'                : true,
                    'Mac'               : true,
                    'Web'               : true,
                    'Android'           : true,
                    'IOS'               : true,
                }
            },
            submit_ing                  : false,
            mcp_placeholder,
            mcpstore                    : false,
        };
    },
    async mounted() {
        this.PAGESHOW                   = true;
        let action_id                   = this.$route.query.action_id;
        let {data}                      = await this.$request.post("/client/action/info", {
            action_id,
        }).finally(()=>this.loading = false);
        Object.assign(this.form,data.action);
    },
    methods: {
        async submit(data){
            this.submit_ing             = true;
            try{
                data                    = await this.$request.post("/client/action/upset", {
                    action_id             : this.$route.query.action_id,
                    ...this.form
                });
                let action              = data.data.action;
                this.$EventBus.emit('organization-action-update', { action });
                await Time.delay(1)
                this.submit_ing         = false;
                this.linkBack()
            } catch (e){
                this.submit_ing         = false;
                console.error(e)
            }
        },
        async selectMcp(mcp){
            this.mcpstore               = false;
            this.form.name              = mcp.name;
            this.form.description       = mcp.description;
            this.form.settings          = {
                "command"               : mcp.command,
                "args"                  : mcp.args,
                "env"                   : mcp.env,
                "cwd"                   : mcp.cwd,
            }
        },
    },
};
</script>

<template>
    <div class="c-body c-screen" :class="{show:PAGESHOW}">
        <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title">修改能力</div>
            <div class="c-options">
                <div class="iconfont icon-more icon-menu"></div>
            </div>
        </CHead>
        <div class="c-scoll c-pd c-wd">
            <div class="c-form c-form-body">
                <a-form class="c-form" :layout="FORM_LAYOUT" :model="form" name="basic" :label-col="{ span: col[0] }" :wrapper-col="{ span: col[1] }" autocomplete="off" @finish="submit">
                    <a-form-item label="支持平台">
                        <a-checkbox v-model:checked="form.support.PC">PC</a-checkbox>
                        <a-checkbox v-model:checked="form.support.Mac">Mac</a-checkbox>
                        <a-checkbox v-model:checked="form.support.Web">Web</a-checkbox>
                        <a-checkbox v-model:checked="form.support.Android">Android</a-checkbox>
                        <a-checkbox v-model:checked="form.support.IOS">IOS</a-checkbox>
                    </a-form-item>
                    <a-form-item label="类型" name="type" :rules="[{ required: true}]">
                        <a-radio-group v-model:value="form.type" name="type">
                            <a-radio value="custom">自定义</a-radio>
                            <a-radio value="mcp" @click="mcpstore=true">MCP <a-button v-if="form.type=='mcp'" type="link" @click="mcpstore=true" size="small">Open Store</a-button></a-radio>
                        </a-radio-group>
                        <template #help>
                                <div v-if="form.type=='mcp'">
                                    检测到系统中已安装的MCP服务，点击可配置。若使使用自研mcp服务可以独立部署本平台。可参考文档：
                                    <a-button type="link" size="small" @click="this.windowOpen({url:'/document/particulars?document_id=HOuIAJcBu45vkOx9Z2nB'});">独立部署</a-button> 
                                    &nbsp;
                                    <a-button type="link" size="small" @click="this.windowOpen({url:'/document/particulars?document_id=G-uIAJcBu45vkOx9Jmkz'});">本地MCP安装配置</a-button>
                                </div>
                            </template>
                    </a-form-item>
                    <template v-if="form.type=='mcp' && form.settings.command">
                        <a-form-item v-for="k in ['command','args']" :label="k">
                            {{ form.settings[k] }}
                        </a-form-item>
                        <a-form-item v-for="(v,k) in form.settings.env" :label="k" name="settings" :rules="[{ required: true }]">
                            <a-input v-model:value="form.settings.env[k]" :maxlength="220"/>
                        </a-form-item>
                    </template>
                    <a-form-item label="能力名称" name="name" :rules="[{ required: true, pattern: /^.{2,20}$/, message: '名称需要2~20个字!' }]">
                        <a-input v-model:value="form.name" :maxlength="20" placeholder="名称需要2~20个字!" />
                    </a-form-item>
                    <a-form-item label="能力描述" name="description" :rules="[{ pattern: /^[\s\S]{0,500}$/,message: '描述需要500个字以内!' }]">
                        <a-textarea v-model:value="form.description" :autoSize="{minRows:2,maxRows:50}" :maxlength="500" placeholder="可以是针对该能力的流程、介绍等描述，需要500个字以内!" />
                    </a-form-item>
                    <a-form-item :wrapper-col="{ offset: col[0], span: col[1] }">
                        <a-button type="primary" html-type="submit" :loading="submit_ing">提交</a-button>
                    </a-form-item>
                </a-form>
                <a-drawer title="MCP Store" placement="bottom" v-model:open="mcpstore" :closable="true" :maskClosable="true":get-container="false" :maskStyle="{background: 'rgba(255, 255, 255, 0.0)'}">
                    <McpGrid @select="selectMcp" />
                </a-drawer>
            </div>
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
.c-form-body{
    padding-top:0;
    min-height:100%;
    position: relative;
}
</style>
