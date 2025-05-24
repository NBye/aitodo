<script>
import Vditor from "vditor";
export default {
    props: {
        content:{
            type                        : String,
            default                     : '',
        },
        width:{
            type                        : String,
            default                     : '100%',
        },
        height:{
            type                        : String,
            default                     : '300px',
        },
        placeholder                     : {
            type                        : String,
            default                     : '编辑信息，支持Markdown语法。',
        },
    },
    data() {
        return {};
    },
    async mounted() {
        this.vditorInit()
    },
    methods: {
        setValue(value){
            return this.vditor.setValue(value);
        },
        getValue(){
            return this.vditor.getValue();
        },
        async vditorInit(){
            return new Promise((resolve)=>{
                this.vditor = new Vditor(this.$refs.vditor, {
                    cdn: '/static/vditor',
                    cache: {
                        id: "vditor",
                    },
                    height: this.height,
                    width: this.width,
                    padding: "0",
                    border: "none",
                    placeholder: this.placeholder,
                    toolbar: [
                        "emoji",
                        "headings",
                        "bold",
                        "italic",
                        "strike",
                        "link",
                        "|",
                        "list",
                        "ordered-list",
                        "check",
                        "outdent",
                        "indent",
                        "|",
                        "quote",
                        "line",
                        "code",
                        "inline-code",
                        "|",
                        "upload",
                        "table",
                        "|",
                        "undo",
                        "redo",
                        "|",
                        "edit-mode",
                        "both",
                        "preview",
                        "fullscreen",
                    ],
                    upload: {
                        accept: "image/*",
                        handler: async (files) => {
                            console.log('Files to upload:', files);
                            let {data}          = await this.$request.post("/client/file/upload", {
                                organization_id : this.organization._id,
                                refresh         : true,
                                image           : files[0],
                            });
                            this.vditor.insertValue(`![图片描述](${this.cutImgUrl(data.image.url,{})})`);
                        }
                    },
                    mode: "wysiwyg", // sv为同步视图模式
                    after: () => {
                        setTimeout(() => {
                            this.vditor.setValue(this.content)
                            this.$emit('markdonw-initialized', {});
                            resolve(this.vditor)
                        });
                    },
                });
            });
        },
    },
};
</script>

<template>
    <div ref="vditor" class="vditor"></div>
</template>

<style lang="scss" scoped></style>
