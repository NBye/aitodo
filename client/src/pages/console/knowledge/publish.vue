<script>
import mammoth from "mammoth";
import * as pdfjsLib from 'pdfjs-dist';
pdfjsLib.GlobalWorkerOptions.workerSrc = "/static/pdfjs/pdf.worker.min.mjs";

import Time from '../../../common/utils/Time';

export default {
    components: {},
    data() {
        return {
            IS_PAGE                     : true,
            PAGESHOW                    : false,
            text                        : '',
            uploading                   : false,
        };
    },
    async mounted() {
        this.PAGESHOW                   = true;

    },
    methods: {
        async submit(){
            if(this.text == false){
                return;
            }
            if(!await this.confirm({title:'确定提价？',content:'提交后文本会自动切割为多个知识碎片。'})){
                return;
            }
            this.uploading              = true;
            await this.$request.post("/client/knowledge/importText", {
                knowledge_bucket_id     : this.$route.query.knowledge_bucket_id,
                text                    : this.text,
            }).finally(()=>this.uploading=false);
            await Time.delay(1);
            this.linkBack();
        },

        async upload({target}){
            let file                    = target.files[0]
            console.log(file.type)
            if (file.type == 'application/pdf') {
                await this.uploadPdf(file);
            } else {
                await this.uploadDocx(file);
            }
        },

        async uploadDocx(file){
            let reader                  = new FileReader();
            reader.onload               = (e) => {
                const arrayBuffer       = e.target.result;
                mammoth.extractRawText({ arrayBuffer }).then((result) => {
                    this.text = result.value.trim();
                }).catch((err) => {
                    this.aMessage().error(err.message)
                });
            };
            reader.readAsArrayBuffer(file);
        },

        async uploadPdf(file){
            if (file.type !== 'application/pdf') {
                return this.aMessage().error('请传入正确的pdf文件')
            }
            let reader                  = new FileReader();
            reader.onload               = async(e)=> {
                let arrayBuffer         = new Uint8Array(e.target.result);
                let pdf                 = await pdfjsLib.getDocument(arrayBuffer).promise;
                let textContent         = '';
                for (let i = 1; i <= pdf.numPages; i++) {
                    let page            = await pdf.getPage(i);
                    let textContentObj  = await page.getTextContent();
                    let pageText        = textContentObj.items.map((item) => item.str).join(' ');
                    textContent         += `${pageText}\n\n`;
                }
                this.text               = textContent.trim();
            };
            reader.readAsArrayBuffer(file);
        },
    },
};
</script>

<template>
    <div class="c-body c-screen" :class="{show:PAGESHOW}">
        <CHead class="c-left c-line" :right="[{icon:'icon-back',event:()=>linkBack(-1)}]">
            <div class="c-title">添加知识文本</div>
            <div class="c-options">
                <div class="iconfont icon-more icon-menu"></div>
            </div>
        </CHead>
        <div class="c-scoll c-pd c-wd">
            <div class="c-form pr">
                <div style="line-height: 60px;">您可以将文档内容直接拷贝进来。</div>
                <a-textarea v-model:value="text" style="height:300px" placeholder="不超过2万子的文本" :maxlength="20000" />
                <div class="tools">
                    <div class="group">
                        <CFile @change="upload" width="32px" height="32px" :autoSubmit="false" border="none" background="none" class="iconfont" accept=".docx,.pdf">
                            <template #initial>
                                <div class="iconfont icon-upload"></div>
                            </template>
                            <template #preview>
                                <div class="iconfont icon-upload"></div>
                            </template>
                        </CFile>
                        <div>导入docx,pdf</div>
                    </div>
                    <div class="group">
                        <a-button type="primary" @click="submit" :loading="uploading">提交</a-button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>

.tools{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 0;

    .group{
        display: flex;
        align-items: center;

        .iconfont{
            font-size:28px;
        }
    }
}
</style>
