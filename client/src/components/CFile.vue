<script>
import {message as Message } from 'ant-design-vue';
export default {
    props                               : {
        //@change
        private                         : {
            type                        : [Boolean,String],
            default                     : false,
        },
        organization_id                 : {
            default                     : '',
        },
        width                           : {                         // 宽度
            default                     : '100px',
        },
        height                          : {                         // 高度
            default                     : '100px',
        },
        border                          : {
            default                     : 'solid 1px #d9d9d9',
        },
        background                      : {
            default                     : '#ffffff',
        },
        radius                          : {
            default                     : '6px',
        },
        accept                          : {                         // 类型限制
            type                        : String,
            default                     : '.jpg,.png,gif',
        },
        maxSize                         : {                         // 文件限制大小/M
            type                        : Number,
            default                     : 10, //5m
        },
        autoSubmit                      : {                         // 自动提交
            type                        : Boolean,
            default                     : true,
        },
        submitUpload: {                        // 宽度
            type                        : Function,
            default                     : new Function(),
        },
    },
    data() {
        return {
            file                        : null,
        };
    },
    async mounted() {},
    methods: {
        async change({target}){
            let file                    = target.files[0];
            if(file==null){
                return this.$emit('cancel');
            }
            if (file.size > this.maxSize * 1024 * 1024) {
                target.value            = '';
                return setTimeout(()=>{
                    this.$emit('submit', {status:'failed',reason:`上传大小不得超过: ${this.maxSize}m`});
                },200);
            }
            this.file                   = file
            // this.$emit('', target.files[0]);
            if (this.autoSubmit){
                await this.submit();
            }
        },
        async submit(){
            if(this.file==null){
                return Message.error(`未选择文件`);
            }
            let {data}                  = await this.$request.post("/client/file/upload", {
                file                    : this.file,
                private                 : (this.private==1 || this.private==true)?'1':'0',
                organization_id         : this.organization_id,
            },{headers:{'Content-Type': 'multipart/form-data'}});
            this.$emit('submit', data.file);
        }
    },
};
</script>

<template>
    <div class="file" :style="{width:width,height:height,border:border,background:background,borderRadius: radius}">
        <slot v-if="file==null" name="initial">
            <div class="initial">
                <CloudUploadOutlined style="large" />
            </div>
        </slot>
        <slot v-if="file!=null" name="preview">
            <div class="preview">
                {{file.name}}
            </div>
        </slot>
        <input class="input" type="file" @change="change" :accept="accept" />
    </div>
</template>

<style lang="scss" scoped>
.file{
    overflow: hidden;
    position: relative;


    .initial{
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .preview{
        @extend .initial
    }
    .input{
        position: absolute;
        display: inline-block;
        background: #ff0;
        width: 100%;
        height: 100%;
        top: 0;
        left: 0;
        z-index: 1;
        opacity: 0;
    }
}
</style>
