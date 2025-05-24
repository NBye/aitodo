<script>
import Time from "../../../common/utils/Time"
function options_data(options){
    let data                            = {}
    options.forEach(o=>{
        data[o.key]                     = o. value;
    });
    return data;
}

export default {
    data() {
        return {
            IS_PAGE                     : true,
            PAGESHOW                    : false,
            item                        : null,
            loading                     : false,
            sending                     : false,
            settings                    : {},
            forms                       : [
                {
                    title               : '大模型源设置',
                    items               : [
                        {
                            key         : 'bailian',
                            enable      : false,
                            name        : '阿里云百炼',
                            description : '阿里旗下汇总各种开源大模型以及，千问系列模型 的云算例平台。',
                            options     : [
                                {type : 'password', value:'',label:'API-KEY',key:'api_key'}
                            ]
                        },
                        {
                            key         : 'ollama',
                            enable      : false,
                            name        : 'Ollama',
                            description : 'Ollama是由Meta公司开源的大模型框架，部署简单便于本地部署。',
                            options     : [
                                {type : 'text', value:'',label:'API地址,如: http://localhost:11434',key:'host'},
                                {type : 'text', value:'',label:'Basic认证 用户名',key:'username'},
                                {type : 'password', value:'',label:'Basic认证 密码',key:'password'},
                                {type : 'password', value:'',label:'Bearer认证 ApiKey',key:'apikey'},
                            ],
                            models      : [],
                            showModels  : async (item)=>await this.load_models(item,'ollama'),
                        },
                        {
                            key         : 'nvidia',
                            enable      : false,
                            name        : 'Nvidia',
                            description : '英伟达GPU加速平台，托管大模型部署。',
                            options     : [
                                {type : 'password', value:'',label:'API-KEY',key:'api_key'}
                            ],
                            models      : [],
                            showModels  : async (item)=>await this.load_models(item,'nvidia'),
                        },
                        {
                            key         : 'ragflow',
                            enable      : false,
                            name        : 'RAGFlow',
                            description : '接入RAGFlow，使用他的能力',
                            options     : [
                                {type : 'text', value:'',label:'API host 地址,如: http://ragflow:80',key:'host'},
                                {type : 'password', value:'',label:'Bearer认证 ApiKey',key:'api_key'},
                            ],
                            models      : [],
                            showModels  : async (item)=>await this.load_models(item,'ragflow'),
                        },
                        {
                            key         : 'other',
                            enable      : false,
                            name        : '其他',
                            description : '兼容OpenAI SDK的相大模型平台。',
                            options     : [
                                {type : 'text', value:'',label:'API地址,如: https://api.openai.com/v1',key:'base_url'},
                                {type : 'password', value:'',label:'Bearer认证 ApiKey',key:'api_key'},
                            ],
                            models      : [],
                            showModels  : async (item)=>await this.load_models(item,'openai'),
                        },
                    ],
                },
            ],
            menu                        : [
            ],
        };
    },
    async mounted() {
    },
    watch: {
        '$route.query': {
            handler() {
                this.PAGESHOW           = true;
                this.organization_id    = this.$route.query.organization_id || this.organization._id;
                this.loadInfo()
            },
            immediate: true,
        },
    },
    methods: {
        async loadInfo(){
            let {data}                  = await this.$request.post("/client/organization/settingInfo", {
                organization_id         : this.organization_id,
            }).finally(()=>this.loading = false);
            this.settings               = data.settings;
            this.forms.forEach(setting=>{
                setting.items.forEach(item=>{
                    if(item.key){
                        let conf        = data.settings[item.key] || {}
                        item.enable     = conf.enable || false;
                        item.models     = conf.models || [];
                        item.options.forEach(o=>{
                            o.value     = conf[o.key] || o.value;
                        });
                    }
                });
            });
        },
        async load_models(item,type){
            let {data}  = await this.$request.post(`/client/organization/${type}_models`, {
                organization_id         : this.organization_id,
                ...options_data(item.options),
            });
            let models                  = []
            data.models.forEach((m)=>{
                for(let o of item.models){
                    if (m.value==o.value){
                        m.support       = o.support;
                        break;
                    }
                }
                models.push(m)
            });
            item.models                 = models;
        },
        async saveSettings(){
            if(!this.settings.embedmodel){
                return this.aMessage().error('请选择向量模型')
            }
            let data                    = {
                embedmodel              : this.settings.embedmodel,
            }
            this.forms.forEach(setting=>{
                setting.items.forEach(item=>{
                    if(item.key){
                        data[item.key]  = {
                            enable      : item.enable,
                        }
                        item.options.forEach(o=>{
                            data[item.key][o.key]   = o.value;
                        });
                        let models      = [];
                        item.models.forEach(m=>{
                            if(m.support.length>0){
                                models.push(m)
                            }
                        });
                        data[item.key].models   = models;
                    }
                });
            });
            if(this.sending){
                return;
            }
            this.sending                = true;
            await this.$request.post("/client/organization/settingSave", {
                organization_id         : this.organization_id,
                settings                : data,
            }).finally(()=>this.sending = false);
            await this.loadInfo()
            await Time.delay(1)
            await this.refishModels()
        },
    },
};
</script>

<template>
    <div class="c-body c-screen am faster" :class="{show:PAGESHOW}">
        <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title">组织设置</div>
            <div class="c-options">
                <div class="iconfont icon-more icon-menu" @click="$refs.as.trigger()"></div>
            </div>
        </CHead>
        <div class="c-scoll c-pd c-wd">
            <div class="c-form pr">
                <div class="settings">
                    <div class="setting">
                        <div class="title">基础设置</div>
                        <div class="body">
                            <div class="item">
                                <div>
                                    <div class="name">向量模型设置</div>
                                    <div class="desc">修改向量模型后，需要将之前的知识库重新导入，否则将无法准确的使用知识库。</div>
                                    <div class="opt">
                                        <a-cascader size="small" class="input" v-model:value="settings.embedmodel" :options="modelsFilter('embedding')" placeholder="未设置向量模型无法使用知识库。" />
                                    </div>
                                </div>
                                <div class="enable"></div>
                            </div>
                        </div>
                    </div>

                    <div class="setting" v-for="(setting,i) in forms" :key="i">
                        <div class="title">{{setting.title}}</div>
                        <div class="body">
                            <div class="item" v-for="(item,i) in setting.items" :key="i">
                                <div>
                                    <div class="name">{{item.name}}</div>
                                    <div class="desc">{{item.description}}</div>
                                    <template v-if="item.enable">
                                        <template v-for="(opt,i) in item.options">
                                            <div class="opt" v-if="opt.type=='text'">
                                                <a-input :placeholder="opt.label" class="input" v-model:value="opt.value" size="small" />
                                            </div>
                                            <div class="opt" v-if="opt.type=='password'">
                                                <a-input-password :placeholder="opt.label" class="input" v-model:value="opt.value" size="small" />
                                            </div>
                                        </template>
                                        <template v-if="item.showModels">
                                            <div>
                                                <a-button type="link" size="small" @click="item.showModels(item)">
                                                    <template #icon><SearchOutlined /></template>
                                                    更新模型
                                                </a-button>
                                                <span> 您需要，点击更新模型后，进行绑定。</span>
                                            </div>
                                            <div class="models">
                                                <div class="model" v-for="(m,i) in item.models" :key="i">
                                                    <div style="padding-left:23px;font-weight: bold;">{{i+1}}. {{m.value}}</div>
                                                    <!-- <a-input placeholder="模型昵称" class="m" v-model:value="m.label" size="small" /> -->
                                                    <a-checkbox-group v-model:value="m.support" :options="['embedding','tools','text','vision','voice.clone','voice.create','image.from_text','video.from_text','video.from_image']" />
                                                </div>
                                            </div>
                                        </template>
                                    </template>
                                </div>
                                <div class="enable">
                                    <a-switch v-model:checked="item.enable" size="small" :disabled="item.disabled" />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <a-button type="primary" @click="saveSettings()" style="margin-top:20px">保存</a-button>
                <ActionSheet ref="as" :list="menu" />
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>

.ant-btn-link {
    padding: 0;
}
.c-form{
    display: flex;
    flex-direction: column;
    min-height: 100%;
    align-items: flex-start;
}
.settings{
    width:100%;
    .setting{
        .title{
            font-weight: bold;
            font-size: 1.2rem;
            line-height: 2.4rem;
        }
        .body{
            .item{
                display: flex;
                width: 100%;
                justify-content: space-between;
                align-items: flex-start;
                padding: 0.5rem 0;
                .name{
                    line-height: 2rem;
                }
                .desc{
                    font-size: 0.85rem;
                    opacity: 0.5;
                    line-height: 1.4rem;
                }
                .opt{
                    .input{
                        margin: 0.2rem 0;
                        width: 100%;
                        max-width:300px;
                    }

                }
                .enable{
                    width: 50px;
                    flex-shrink: 0;
                    flex-grow: 0;
                    text-align: right;
                }

                .models{
                    max-height: 300px;
                    overflow:auto;
                    margin-top: 0.7rem;
                    .model{
                        border-bottom: solid 1px #ddd;
                        padding: 0.7rem 0;
                        &:first-child{
                            border-top: solid 1px #ddd;
                        }
                        &:hover{
                            background: #f5f5f5;
                        }
                    }
                }
            }
        }
    }
}
</style>
