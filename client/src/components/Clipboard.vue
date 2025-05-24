<script>
import Clipboard from "clipboard";
export default {
    components                          : {},
    props                               : {
        text                            : {
            type                        : String,
            required                    : true,
        },
        class                           : {
            type                        : [String,Object],
            default                     : '',
        },
    },
    data() {
        return {};
    },
    beforeDestroy() {
        if (this.clipboard) {
            this.clipboard.destroy();
        }
    },
    async mounted() {
        this.clipboard = new Clipboard(this.$refs.copy_btn, {
            text: () => this.text
        });
        this.clipboard.on('success', () => {
            this.$emit('clipboard-success')
        });
        this.clipboard.on('error', (e) => {
            this.$emit('clipboard-error')
        });
    },
    methods: {},
};
</script>

<template>
    <div :class="class" ref="copy_btn" @click="">
        <slot><a-button type="text">复制</a-button></slot>
    </div>
</template>

<style lang="scss" scoped></style>
