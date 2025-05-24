<script>
export default {
    props                               : {
        data                            : {
            type                        : Object,
            required                    : true,
        },
        root                            : {
            type                        : Boolean,
            required                    : false,
        },
    },
    data() {
        return {
            hover                       : false,
        };
    },
    async mounted() {},
    methods: {
        chageType(type){
            this.data.enum              = [];
            this.data.description       = '';
            this.data.properties        = [];
            if(this.data.type=='boolean'){
                this.data['default']    = true
            } else {
                this.data['default']    = ''
            }

        },
        addPropertie(){
            this.data.properties.push({
                type                    : 'string',
                key                     : '',
                description             : '',
                default                 : '',
                properties              : [],
                required                : true,
                enum                    : [],
            })
        },
        remPropertie(propertie){
            let i = this.data.properties.indexOf(propertie);
            this.data.properties.splice(i,1);
        },
        emitRemove(item){
            this.$emit('remove', item);
        },
    },
};
</script>

<template>
    <div class="propertie" :class="{hover:hover}" @mouseover.stop="hover=true" @mouseout.stop="hover=false">
        <div class="title" v-if="!root">
            <a-checkbox v-model:checked="data.required" style="padding-right: 5px;"></a-checkbox>
            <a-select class="type" v-model:value="data.type" @change="chageType(data.type)">
                <a-select-option value="object">object</a-select-option>
                <a-select-option value="string">string</a-select-option>
                <a-select-option value="integer">integer</a-select-option>
                <a-select-option value="number">number</a-select-option>
                <a-select-option value="boolean">boolean</a-select-option>
            </a-select>
            <a-input class="key" v-model:value="data.key" placeholder="Key值" />

            <a-input class="def" v-model:value="data['default']" placeholder="默认值，支持模板参数" v-if="data.type=='string'" />
            <a-input class="def" v-model:value="data['default']" placeholder="默认值，支持模板参数" v-if="data.type=='integer'"/>
            <a-input class="def" v-model:value="data['default']" placeholder="默认值，支持模板参数" v-if="data.type=='number'"/>
            <a-switch class="def" style="width:60px" v-model:checked="data['default']" checked-children="True" un-checked-children="False" v-if="data.type=='boolean'" />

            <a-input class="dec" v-model:value="data.description" placeholder="描述，AI根据此进行赋值" />
            <div class="iconfont icon-meiju hover" @click="['object','boolean'].indexOf(data.type)==-1 && data.enum.push('')"></div>
            <div class="iconfont icon-close hover" @click="emitRemove(data)"></div>
        </div>
        <div class="enum" v-for="(e,i) in data.enum" :key="i">
            <a-input-number v-if="data.type=='number'" v-model:value="data.enum[i]" placeholder="可选值：请输入数字" class="w100" />
            <a-input-number v-if="data.type=='integer'" v-model:value="data.enum[i]" placeholder="可选值：请输入整数" class="w100" />
            <a-input v-if="data.type=='string'" v-model:value="data.enum[i]" placeholder="可选值：请输入字符串" />
            <a-input v-if="data.type=='object'" v-model:value="data.enum[i]" placeholder="可选值：请输入json字符串" />
            <a-checkbox v-if="data.type=='boolean'" v-model:checked="data.enum[i]" class="w100">{{data.enum[i]?'True':'False'}}</a-checkbox>
            <div class="iconfont icon-close hover" @click="listRemoveItem(data.enum,data.enum[i],i)"></div>
        </div>
        <div class="tal" v-if="data.type=='object'">
            <a-button type="link" @click="addPropertie()"><PlusOutlined />添加</a-button>
            <span v-if="root" style="font-size:0.8rem;color:#999">(勾选则为必填项)</span>
        </div>
        <div class="child" :class="{pd:!root}" v-if="data.type=='object'">
            <template v-for="(item,i) in data.properties">
                <AgentFormPropertie :data="item" @remove="remPropertie" />
            </template>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.propertie{
    padding: 5px;
    &.hover{
        background: #f5f5f5;
    }
    .title{
        display: flex;
        align-items: center;
        .type{
            width: 92px;
            flex-shrink: 0;
            flex: 0 0 auto;
        }
        .iconfont{
            flex: 0 0 auto;
        }
        .key{
            width:80px;
            flex-shrink: 0;
        }
        .def{
            width:100px;
            flex-shrink: 0;
        }
        .dec{

        }
    }
    .child{
        &.pd{
            padding-left:2rem;
        }
    }
    .enum{
        padding: 0 32px 0 112px;
        display: flex;
        align-items: center;
    }
}
</style>
