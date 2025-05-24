<script>
import Time from '../common/utils/Time';
export default {
    props: {
        //@submit,@close
        closable                        : {
            type                        : Boolean,
            default                     : true,
        },
        height                          : {
            type                        : String,
            default                     : '80%',
        },
    },
    data() {
        return {
			col: [4, 0],
            title                       : 'Agent 配置',
            open                        : false,
            item                        : null,
            item_type                   : '',
            btnText                     : '提交',
            submiting                   : false,

            type_help                   : {
                knowledge               : '配置知识库，AI可以通过此知识库解答用户问题。',
                request                 : '对接外部接口，打通外部系统对接。',
                generate                : '通过jinja2模板语法进行逻辑控制。',
                modelcall               : '使用大模型进行引导、决策、生成内容。',
            },
            template_help               : '支持Jinja2语法，支持变量: message,messages,parameters,output,'
                                        + 'parent.output(上一级Agent的output)'
                                        + '若为空则将接返回口文本直接返回。',
            model_supports              : [],
            model_return_description    : '',
            knowledge_bucket_list       : [],
            cache                       : {},
            mcps                        : [],
            mcp_agent_list              : [],
        };
    },
    async mounted() {
    },
    methods: {
        switchType(type,data=null){
            let itemDefault             = {
                knowledge               : {
                    type                : 'knowledge',
                    decision            : 'ai',
                    description         : '',
                    knowledge_bucket_id        : '',
                    knowledge_bucket_name      : '',
                },
                request                 : {
                    type                : 'request',
                    decision            : 'ai',
                    description         : '',
                    url                 : '',
                    method              : 'post',
                    headers             : [
                        {key:'content-type',val:'application/json'}
                    ],
                    metadata            : false,
                    parameters          : {
                        type            : 'object',
                        properties      : [],
                        required        : true,
                        enum            : [],
                    },
                    template            : '',
                },
                generate                : {
                    type                : 'generate',
                    decision            : 'ai',
                    description         : '',
                    input               : '',
                    model               : '',
                    model_action        : '',
                    parameters          : {
                        type            : 'object',
                        properties      : [],
                        required        : true,
                        enum            : [],
                    },
                },
                modelcall               : {
                    type                : 'modelcall',
                    decision            : 'ai',
                    description         : '',
                    model               : '',
                    model_action        : '',
                    model_params        : {
                        type            : 'object',
                        properties      : [],
                        required        : true,
                        enum            : [],
                    },
                    format_template     : '',
                },
                mcp                     : {
                    action_id           : '',
                    rname               : '',
                    type                : 'mcp',
                    decision            : 'ai',
                    description         : '',
                    parameters        : {
                        type            : 'object',
                        properties      : [],
                        required        : true,
                        enum            : [],
                    },
                }
            };
            let item                    = {}
            if(this.item && this.item.name){
                item['name']            = this.item.name;
            }
            if(this.item && this.item.description){
                item['description']     = this.item.description;
            }
            if(this.item){
                this.cache[this.item.type] = JSON.stringify(this.item)
            }
            this.item                   = Object.assign(itemDefault[type] ||
                                        itemDefault['knowledge'], data ||
                                        item,this.cache[type]?JSON.parse(this.cache[type]):{})
            this.item_type              = this.item.type;
            if(this.item_type=='modelcall' && this.item.model){
                for(let p of this.MODEL_LIST){
                    if(p.value==this.item.model[0]){
                        for(let m of p.children){
                            if(m.value==this.item.model[1]){
                                this.model_supports = m.support;
                                break;
                            }
                        }
                        break;
                    }
                }
            }
        },
        show(title='',type,data=null){
            this.cache                  = {}
            this.item                   = null;
            this.title                  = title || 'Agent 配置'
            this.switchType(type,data)
            this.btnText                = data?'保存':'添加'
            this.open                   = true;
            this.submiting              = false;
            // console.log(JSON.parse(JSON.stringify(this.item)))
            this.knowledgeSearch();
            this.loadMcps();
        },
        hide(){
            this.cache                  = {}
            this.item                   = null;
            this.open                   = false;
            this.submiting              = false;
            this.model_supports         = [];
        },
        async onSubmit(){
            if(!this.item.description){
                return this.aMessage().warn('请把表单填写完善');
            } else if(this.item.type=='knowledge' && !this.item.knowledge_bucket_id){
                return this.aMessage().warn('请把表单填写完善');
            } else if(this.item.type=='request' && !this.item.url){
                return this.aMessage().warn('请把表单填写完善');
            } else if(this.item.type=='generate' && !this.item.input){
                return this.aMessage().warn('请把表单填写完善');
            } else if(this.item.type=='modelcall' && !this.item.model_action){
                return this.aMessage().warn('请把表单填写完善');
            }
            this.submiting              = true;
            await this.$emit('submit',this.item);
            this.submiting              = false;
            this.cache                  = {};
        },
        async useMcp(mcp){
            this.item.description       = mcp.description || '';
            this.item.rname             = mcp.rname || '';
            this.item.parameters        = mcp.parameters || {};
        },
        async loadMcps(){
            if (this.mcps.length ){
                return;
            }
            let {data}                  = await this.$request.post("/client/action/search",{
                type                    : 'mcp',
                enabled                 : true,
                user_id                 : this.$route.query.user_id,
                skip                    : 0,
                size                    : 100,
                sort                    : 'updated DESC',
                _source                 : ['name','agent_list'],
            });
            this.mcps                   = data.list;
            console.log(this.mcps)
        },
        async knowledgeSearch(keyword=''){
            if(this.knowledge_bucket_list.length){
                return;
            }
            let {data}                  = await this.$request.post("/client/knowledge/bucketSearch", {
                keyword,
            }).finally(()=>this.search_ing = false );
            this.knowledge_bucket_list  = [];
            data.list.forEach(item=>{
                this.knowledge_bucket_list.push({
                    value: item._id,
                    label: item.name,
                })
            });
        },
        async knowledgeChage(item,bucket_id){
            this.knowledge_bucket_list.forEach(bucket=>{
                if(bucket.value == bucket_id){
                    item.description    = bucket.label;
                }
            })
        },

        setModelSupport(supports){
            this.model_supports         = supports;
            this.item.model_action      = '';
            this.item.model_params      = {
                type            : 'object',
                properties      : [],
                required        : true,
                enum            : [],
            };
        },
        setModelAction(e){
            this.item.model_params.properties = [];
            if (e=='voice.clone'){
                this.model_return_description = '此处 output 是一个 DataBase 对象。'
                this.item.model_params.properties.push({
                    type                : 'string',
                    key                 : 'file_id',
                    description         : '音频文件id',
                    default             : '',
                    properties          : [],
                    required            : true,
                    enum                : [],
                });
            } else if (e=='voice.create'){
                this.model_return_description = '此处 output 是一个 File 对象。'
                this.item.model_params.properties.push({
                    type                : 'string',
                    key                 : 'clone_id',
                    description         : '声音复刻ID',
                    default             : '',
                    properties          : [],
                    required            : true,
                    enum                : [],
                });
                this.item.model_params.properties.push({
                    type                : 'string',
                    key                 : 'text',
                    description         : '合成语音文案',
                    default             : '',
                    properties          : [],
                    required            : true,
                    enum                : [],
                });
                this.item.model_params.properties.push({
                    type                : 'string',
                    key                 : 'name',
                    description         : '合成语音后保存的文件名',
                    default             : '',
                    properties          : [],
                    required            : false,
                    enum                : [],
                });
            } else if (e=='image.from_text'){
                this.model_return_description = '此处 output 是一个 list[File] 元素是一个File对象的列表list。'
                this.item.model_params.properties.push({
                    type                : 'string',
                    key                 : 'prompt',
                    description         : '生成图片要求提示',
                    default             : '',
                    properties          : [],
                    required            : true,
                    enum                : [],
                });
                this.item.model_params.properties.push({
                    type                : 'string',
                    key                 : 'name',
                    description         : '生成图片后保存的文件名',
                    default             : '',
                    properties          : [],
                    required            : false,
                    enum                : [],
                });
                this.item.model_params.properties.push({
                    type                : 'number',
                    key                 : 'width',
                    description         : '图片宽度，最大1200',
                    default             : 800,
                    properties          : [],
                    required            : false,
                    enum                : [],
                });
                this.item.model_params.properties.push({
                    type                : 'number',
                    key                 : 'height',
                    description         : '图片高度，最大800',
                    default             : 600,
                    properties          : [],
                    required            : false,
                    enum                : [],
                });
            } else if (e=='video.from_text'){
                this.model_return_description = '此处 output 是一个 File 对象。'
                this.item.model_params.properties.push({
                    type                : 'string',
                    key                 : 'prompt',
                    description         : '生成视频要求',
                    default             : '',
                    properties          : [],
                    required            : true,
                    enum                : [],
                });
                this.item.model_params.properties.push({
                    type                : 'string',
                    key                 : 'name',
                    description         : '生成视频后保存的文件名',
                    default             : '',
                    properties          : [],
                    required            : false,
                    enum                : [],
                });
                this.item.model_params.properties.push({
                    type                : 'number',
                    key                 : 'duration',
                    description         : '生成视频的时间s',
                    default             : 5,
                    properties          : [],
                    required            : false,
                    enum                : [],
                });
            } else if (e=='video.from_image'){
                this.model_return_description = '此处 output 是一个 File 对象。'
                this.item.model_params.properties.push({
                    type                : 'string',
                    key                 : 'prompt',
                    description         : '图片生成视频要求',
                    default             : '',
                    properties          : [],
                    required            : true,
                    enum                : [],
                });
                this.item.model_params.properties.push({
                    type                : 'string',
                    key                 : 'file_id',
                    description         : '图片文件id',
                    default             : '',
                    properties          : [],
                    required            : true,
                    enum                : [],
                });
                this.item.model_params.properties.push({
                    type                : 'string',
                    key                 : 'name',
                    description         : '生成视频后保存的文件名',
                    default             : '',
                    properties          : [],
                    required            : false,
                    enum                : [],
                });
                this.item.model_params.properties.push({
                    type                : 'number',
                    key                 : 'duration',
                    description         : '生成视频的时间s',
                    default             : 5,
                    properties          : [],
                    required            : false,
                    enum                : [],
                });
            }

        },
    },
}
</script>

<template>
    <a-drawer :title="title" :height="height" placement="bottom" :closable="closable" :maskClosab="closable" v-model:open="open" :get-container="false" :maskStyle="{background: 'rgba(255, 255, 255, 0.0)'}">
        <template #extra>
            <a-button type="primary" @click="onSubmit" :loading="submiting">{{btnText}}</a-button>
        </template>
        <a-form class="form" v-if="item" :model="item" name="basic" :layout="FORM_LAYOUT" :label-col="{ span: col[0] }" :wrapper-col="{ span: col[1] }">
            <a-form-item label="类型" :help="type_help[item.type]">
                <a-radio-group v-model:value="item_type" @change="switchType(item_type)">
                    <template v-for="(v,k) in AGENT_TYPE_MAP">
                        <a-radio-button :value="k">{{v}}</a-radio-button>
                    </template>
                </a-radio-group>
            </a-form-item>
            <a-form-item label="执行决策" help="">
                <a-radio-group v-model:value="item.decision">
                    <a-radio value="ai">AI决定是否执行</a-radio>
                    <a-radio value="auto">强制自动执行</a-radio>
                </a-radio-group>
            </a-form-item>
            <a-form-item label="描述" name="description" :rules="[{ required: true, message: '不能为空,200字以内。' }]">
                <a-input v-model:value="item.description" :maxlength="200" :placeholder="`AI根据此描述，判断是否使用以下${AGENT_TYPE_MAP[item.type]}。`" />
            </a-form-item>
            
            <!-- knowledge -->     
            <template v-if="item.type=='knowledge'">
                <a-form-item label="知识库" :rules="[{ required: true}]">
                    <a-select v-model:value="item.knowledge_bucket_id" @change="(bucket_id)=>knowledgeChage(item,bucket_id)" :placeholder="'搜索知识库'" :default-active-first-option="false" :show-arrow="false" :filter-option="false" :not-found-content="null" :options="knowledge_bucket_list" show-search @search="knowledgeSearch"></a-select>
                </a-form-item>
            </template>
            <template v-if="item.type=='generate'">
                <a-form-item label="参数" :rules="[{ required: true}]" v-if="item.decision=='ai'">
                    <AgentFormPropertie :edit="true" :root="true" :data="item.parameters" />
                </a-form-item>
                <a-form-item label="输入" name="input" :rules="[{ required: true, message: '不能为空,5000字以内。' }]">
                    <a-textarea v-model:value="item.input" :maxlength="5000" :rows="6" :placeholder="`支持模板绑定数据。${template_help}`" showCount />
                    <template #help>
                        <div>
                            此处模板支持缓存元数据，以及一些逻辑处理，作用非常强大，请参考。
                            <a-button type="link" size="small" @click="this.windowOpen({url:'/document/particulars?document_id=GuuHAJcBu45vkOx9_Gkh'});">查看文档</a-button>
                        </div>
                    </template>
                </a-form-item>

                <a-form-item label="模型" help="选择模型可以让模型根据用户问题自动对输入进行整理。">
                    <a-cascader v-model:value="item.model" :options="modelsFilter('text')" placeholder="不使用模型，直接返回" />
                </a-form-item>
            </template>
            
            <!-- mcp -->            
            <template v-if="item.type=='mcp'">
                <a-form-item label="引用">
                    <div style="display: flex;width:100%">
                        <a-select v-model:value="item.action_id" style="width:30%;">
                            <a-select-option value="" @click="mcp_agent_list=[]">请选择</a-select-option>
                            <a-select-option v-for="mcp in mcps" :value="mcp._id" @click="mcp_agent_list=mcp.agent_list">{{mcp.name}}</a-select-option>
                        </a-select>
                        <a-select v-model:value="item.rname" style="width:70%;padding-left:5px;">
                            <a-select-option value="" @click="useMcp({})">请选择</a-select-option>
                            <a-select-option v-for="a in mcp_agent_list" :value="a.rname" @click="useMcp(a)">{{a.description}}</a-select-option>
                        </a-select>
                    </div>
                </a-form-item>

                <a-form-item label="参数" :rules="[{ required: true}]" v-if="item.decision=='ai'">
                    <AgentFormPropertie :edit="true" :root="true" :data="item.parameters" />
                </a-form-item>
            </template>
            
            <!-- modelcall -->    
            <template v-if="item.type=='modelcall'">
                <a-form-item label="模型" :rules="[{ required: true}]" help="选择模型可以让模型根据用户问题自动对输入进行整理。">
                    <a-cascader v-model:value="item.model" @change="(e,s)=>setModelSupport(model_supports=s?s[1].support:[])" :options="modelsFilter(/^(voice|image|video)\./)" placeholder="不使用模型，直接返回" />
                </a-form-item>

                <a-form-item label="模型能力" name="model_action" :rules="[{ required: true, message: '必选一个。' }]" v-if="item.model">
                    <a-radio-group v-model:value="item.model_action" @change="setModelAction(item.model_action)">
                        <a-radio value="voice.clone" v-if="model_supports.indexOf('voice.clone')>-1">声音复刻</a-radio>
                        <a-radio value="voice.create" v-if="model_supports.indexOf('voice.create')>-1">语音合成</a-radio>

                        <a-radio value="image.from_text" v-if="model_supports.indexOf('image.from_text')>-1">图片生成</a-radio>

                        <a-radio value="video.from_text" v-if="model_supports.indexOf('video.from_text')>-1">文生视频</a-radio>
                        <a-radio value="video.from_image" v-if="model_supports.indexOf('video.from_image')>-1">图生视频</a-radio>
                    </a-radio-group>
                </a-form-item>

                <a-form-item label="参数" :rules="[{ required: true}]" v-if="item.model_action">
                    <AgentFormPropertie :edit="true" :root="true" :data="item.model_params" />
                </a-form-item>

                <a-form-item label="格式化返回" :rules="[{ required: false}]" v-if="item.model_action">
                    <template #help>
                        <div>
                            {{model_return_description}}
                            <a-button type="link" size="small" @click="this.windowOpen({url:'/document/particulars?document_id=GuuHAJcBu45vkOx9_Gkh'});">查看文档</a-button>
                        </div>
                    </template>
                    <a-textarea v-model:value="item.format_template" :maxlength="5000" :rows="6" :placeholder="`将接口数据转化为字符文本。${template_help}`" showCount />
                </a-form-item>
            </template>

            <!-- request -->    
            <template v-if="item.type=='request'">
                <a-form-item label="URL" :rules="[{ required: true, message: '不能为空，256字符以内' }]">
                    <a-input v-model:value="item.url" :maxlength="256" placeholder="请求AIP的地址" />
                </a-form-item>
                <a-form-item label="Method" :rules="[{ required: true}]">
                    <a-radio-group v-model:value="item.method" name="method">
                        <a-radio value="post">Post</a-radio>
                        <a-radio value="get">Get</a-radio>
                        <a-radio value="put">Put</a-radio>
                        <a-radio value="delete">Delete</a-radio>
                        <a-radio value="head">Head</a-radio>
                        <a-radio value="patch">Patch</a-radio>
                        <a-radio value="options">Options</a-radio>
                    </a-radio-group>
                </a-form-item>
                <a-form-item label="Headers" :rules="[{ required: true}]">
                    <div class="header" v-for="(h,i) in item.headers" :key="i">
                        <a-input class="input" v-model:value="h.key" :maxlength="50" placeholder="键" />
                        <a-input class="input" v-model:value="h.val" :maxlength="256" placeholder="值" />
                        <div class="iconfont icon-close hover" @click="listRemoveItem(item.headers,h)"></div>
                    </div>
                    <div class="tar">
                        <a-button type="link" @click="item.headers.push({key:'',val:''})"> <PlusOutlined />添加 </a-button>
                    </div>
                </a-form-item>
                <a-form-item label="参数" :rules="[{ required: true}]" v-if="item.decision=='ai'">
                    <div style="padding:5px 10px;">
                        <a-checkbox v-model:checked="item.metadata">同时提交 metadata 数据，key为‘metadata’。</a-checkbox>
                    </div>
                    <AgentFormPropertie :edit="true" :root="true" :data="item.parameters" />
                </a-form-item>
                <a-form-item label="格式化返回" :rules="[{ required: false}]">
                    <template #help>
                        <div>
                            此处模板可以将http接口返回进行格式化，或做一些逻辑处理。
                            <a-button type="link" size="small" @click="this.windowOpen({url:'/document/particulars?document_id=GuuHAJcBu45vkOx9_Gkh'});">查看文档</a-button>
                        </div>
                    </template>
                    <a-textarea v-model:value="item.template" :maxlength="5000" :rows="6" :placeholder="`将接口数据转化为字符文本。${template_help}`" showCount />
                </a-form-item>
            </template>
        </a-form>
    </a-drawer>
</template>

<style lang="scss" scoped>
.form{
    .header{
        display: flex;
        .iconfont{
            flex: none;
        }
        .input{
            width: 50%;
        }
    }
}
</style>
