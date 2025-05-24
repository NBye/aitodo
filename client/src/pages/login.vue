<script>
import Time from "../common/utils/Time";
import storage from "../common/utils/storage";
import { Modal, message as Message } from 'ant-design-vue';

export default {
    components: {},
    data() {
        return {
            IS_PAGE                     : true,
            form                        : {
                phone                   : "",
                email                   : "",
                username                : "",
                password                : "",

                phone_code_id           : "",
                phone_code              : "",

                email_code_id           : "",
                email_code              : "",

                img_code_id             : "",
                img_code                : "",
                type                    : "1",
                // type=1 手机+密码+图片验证码+验证码ID 登录
                // type=2 邮箱+密码+图片验证码+验证码ID 登录
                // type=3 账号+密码+图片验证码+验证码ID 登录
                // type=4 手机+短信验证码+验证码ID 登录&注册
                // type=5 邮箱+邮箱验证码+验证码ID 登录&注册
            },
            accept                      : false,
            img_code_url                : "",

            tabKey                      : "1",
            fomKey                      : "1",

            send_phone_code             : false,
            send_phone_tips             : "",
            send_email_code             : false,
            send_email_tips             : "",

            submiting                   : false,
        };
    },
    async mounted() {
        this.refImageCode();
    },
    methods: {
        async submit(values) {
            if (!this.accept) {
                if (await this.confirm({ title: "请勾选接受协议" ,content:"确定后表示您已同意遵守隐私协议与服务协议。"})) {
                    this.accept         = true;
                }
            } else {
                this.submiting          = true;
                this.$request.post("/common/user/login", this.form, {
                    ERROR_TIPS_ENABLE   : false,
                }).then(async ({ data }) => {
                    storage('user',data.user)
                    storage('token',data.token)
                    await this.refishCache();
                    await Time.delay(1)
                    this.link({path:'/console'})
                }).catch((e) => {
                    Message.error("登录失败: "+e.message)
                    if (["1", "2", "3"].indexOf(this.form.type) > -1) {
                        this.refImageCode();
                    }
                }).finally(()=>this.submiting = false );
            }
        },
        switchType() {
            if (this.tabKey == "1" && this.fomKey == "1") {
                this.form.type          = "1";
            } else if (this.tabKey == "1" && this.fomKey == "2") {
                this.form.type          = "4";
            } else if (this.tabKey == "2" && this.fomKey == "1") {
                this.form.type          = "2";
            } else if (this.tabKey == "2" && this.fomKey == "2") {
                this.form.type          = "5";
            }
            this.refImageCode();
        },
        async sendPhoneCode() {
            this.send_phone_code        = true;
            this.$request.post("/common/yzm/phone", this.form, {
                ERROR_TIPS_ENABLE       : true,
            }).then(({data})=>{
                Object.assign(this.form,data);
                let sec = 60;
                Time.interval((i) => {
                    this.send_phone_tips=`剩余${sec-1-i}s`
                },1,sec).finally(() => {
                    this.send_phone_code                = false;
                    this.send_phone_tips                =``
                });
            }).catch(e=>{
                this.send_phone_code    = false;
                this.refImageCode();
            });
        },
        sendEmailCode() {
            this.send_email_code = true;
            this.$request.post("/common/yzm/email", this.form, {
                ERROR_TIPS_ENABLE: true,
            }).then(({data}) => {
                let sec                 = 60;
                Object.assign(this.form,data);
                Time.interval((i) => {
                    this.send_email_tips=`剩余${sec-1-i}s`
                },1,sec).finally(() => {
                    this.send_email_code                = false;
                    this.send_email_tips                =``
                });
            }).catch(e=>{
                this.send_email_code    = false;
                this.refImageCode();
            });
        },
        async refImageCode() {
            let { data } = await this.$request.post("/common/yzm/image", {
                width: 240, height: 80, length: 4, size: 62
            },{
                SUCCESS_TIPS_ENABLE     : false,
            });
            this.form.img_code_id = data.img_code_id;
            this.img_code_url = data.img_code_url;
        },
    },
};
</script>

<template>
    <div v-if="isMobile()" class="bg-video"></div>
    <video v-if="!isMobile()" autoplay muted playsinline loop class="bg-video">
        <source src="/bg.mp4" type="video/mp4" />
    </video>
    <div class="login" :class="{mobile:IS_MOBILE}">
        <div class="head">
            <CoverImage src="/logo/logo1.png" :width="50" :height="50" />
            <span style="font-size: 1.5rem; font-weight: 400; margin-left: 0.5rem;color: #fff;">网音·AiToDo</span>
        </div>
        <div class="content">
            <div class="box">
                <div class="title">欢迎使用 AiToDo</div>
                <a-tabs v-model:activeKey="tabKey" @change="switchType()" centered>
                    <a-tab-pane key="1" tab="手机号">
                        <a-form :model="form" autocomplete="off" @finish="submit">
                            <!-- 手机号+密码登录+图片验证 -->
                            <a-form-item v-if="form.type == '1'" name="phone" :rules="[{ required: true, pattern: /^1\d{10}$/, message: '请输入正确的手机号码!' }]">
                                <a-input v-model:value="form.phone" size="large" placeholder="手机号" />
                            </a-form-item>

                            <a-form-item v-if="form.type == '1'" name="password" :rules="[{ required: true, pattern: /^.{6,50}$/, message: '密码为6~50位的字符串' }]">
                                <a-input-password v-model:value="form.password" size="large" placeholder="密码" />
                            </a-form-item>

                            <a-form-item v-if="form.type == '1'" name="img_code" :rules="[{ required: true, pattern: /^[A-Za-z0-9]{4}$/, message: '图片验证码为4个英文/数字组成' }]">
                                <a-input class="input-code" v-model:value="form.img_code" size="large" placeholder="图片验证码" />
                                <CoverImage class="input-img" :src="img_code_url" :width="120" :height="40" background="#eee" @click="refImageCode()" />
                            </a-form-item>
                            <!-- 手机号+短信验证 -->
                            <a-form-item v-if="form.type == '4'" name="phone" :rules="[{ required: true, pattern: /^1\d{10}$/, message: '请输入正确的手机号码!' }]">
                                <a-input v-model:value="form.phone" size="large" placeholder="手机号" />
                            </a-form-item>

                            <a-form-item v-if="form.type == '4'" name="img_code" :rules="[{ required: true, pattern: /^[A-Za-z0-9]{4}$/, message: '图片验证码为4个英文/数字组成' }]">
                                <a-input class="input-code" v-model:value="form.img_code" size="large" placeholder="图片验证码" />
                                <CoverImage class="input-img" :src="img_code_url" :width="120" :height="40" background="#eee" @click="refImageCode()" />
                            </a-form-item>

                            <a-form-item v-if="form.type == '4'" name="phone_code" :rules="[{ required: true, pattern: /^\d{6}$/, message: '短信验证码为6位纯数字组成' }]">
                                <a-input class="input-code" v-model:value="form.phone_code" size="large" placeholder="短信验证码" />
                                <a-button class="input-img" :loading="send_phone_code" @click="sendPhoneCode()" size="large" style="vertical-align: initial">{{ send_phone_tips || "获取验证码" }}</a-button>
                            </a-form-item>

                            <a-form-item>
                                <a-checkbox v-model:checked="accept">
                                    我接受
                                    <a-button type="link" @click.stop="windowOpen({url:'/document/particulars?document_id=GOuHAJcBu45vkOx9VWl-'})">服务协议</a-button>
                                    和
                                    <a-button type="link" @click.stop="windowOpen({url:'/document/particulars?document_id=GeuHAJcBu45vkOx9eGln'})">隐私协议</a-button>
                                </a-checkbox>
                            </a-form-item>

                            <a-form-item>
                                <a-button class="submit" type="primary" html-type="submit" size="large" :loading="submiting">登录/注册</a-button>
                            </a-form-item>

                            <a-form-item v-if="fomKey == '1'">
                                <a-button type="link" @click="(fomKey = '2') && switchType()">验证码登录/注册</a-button>
                            </a-form-item>
                            <a-form-item v-if="fomKey == '2'">
                                <a-button type="link" @click="(fomKey = '1') && switchType()">密码登录</a-button>
                            </a-form-item>
                        </a-form>
                    </a-tab-pane>
                    <a-tab-pane key="2" tab="邮箱">
                        <a-form :model="form" autocomplete="off" @finish="submit">
                            <!-- 邮箱+密码登录+图片验证 -->
                            <a-form-item v-if="form.type == '2'" name="email" :rules="[{ required: true, type: 'email', message: '请输入正确的邮箱!' }]">
                                <a-input v-model:value="form.email" size="large" placeholder="邮箱" />
                            </a-form-item>

                            <a-form-item v-if="form.type == '2'" name="password" :rules="[{ required: true, pattern: /^.{6,50}$/, message: '密码为6~50位的字符串' }]">
                                <a-input-password v-model:value="form.password" size="large" placeholder="密码" />
                            </a-form-item>

                            <a-form-item v-if="form.type == '2'" name="img_code" :rules="[{ required: true, pattern: /^[A-Za-z0-9]{4}$/, message: '图片验证码为4个英文/数字组成' }]">
                                <a-input class="input-code" v-model:value="form.img_code" size="large" placeholder="图片验证码" />
                                <CoverImage class="input-img" :src="img_code_url" :width="120" :height="40" background="#eee" @click="refImageCode()" />
                            </a-form-item>
                            <!-- 邮箱+邮箱验证 -->
                            <a-form-item v-if="form.type == '5'" name="email" :rules="[{ required: true, type: 'email', message: '请输入正确的邮箱!' }]">
                                <a-input v-model:value="form.email" size="large" placeholder="邮箱" />
                            </a-form-item>

                            <a-form-item v-if="form.type == '5'" name="img_code" :rules="[{ required: true, pattern: /^[A-Za-z0-9]{4}$/, message: '图片验证码为4个英文/数字组成' }]">
                                <a-input class="input-code" v-model:value="form.img_code" size="large" placeholder="图片验证码" />
                                <CoverImage class="input-img" :src="img_code_url" :width="120" :height="40" background="#eee" @click="refImageCode()" />
                            </a-form-item>

                            <a-form-item v-if="form.type == '5'" name="email_code" :rules="[{ required: true, pattern: /^\d{6}$/, message: '邮箱验证码为6位纯数字组成' }]">
                                <a-input class="input-code" v-model:value="form.email_code" size="large" placeholder="邮箱验证码" />
                                <a-button class="input-img" :loading="send_email_code" @click="sendEmailCode()" size="large" style="vertical-align: initial">{{ send_email_tips || "获取验证码" }}</a-button>
                            </a-form-item>

                            <a-form-item>
                                <a-checkbox v-model:checked="accept">
                                    我接受
                                    <a-button type="link" @click.stop="windowOpen({url:'/document/particulars?document_id=GOuHAJcBu45vkOx9VWl-'})">服务协议</a-button>
                                    和
                                    <a-button type="link" @click.stop="windowOpen({url:'/document/particulars?document_id=GeuHAJcBu45vkOx9eGln'})">隐私协议</a-button>
                                </a-checkbox>
                            </a-form-item>

                            <a-form-item>
                                <a-button class="submit" type="primary" html-type="submit" size="large" :loading="submiting">登录/注册</a-button>
                            </a-form-item>

                            <a-form-item v-if="fomKey == '1'">
                                <a-button type="link" @click="(fomKey = '2') && switchType()">验证码登录/注册</a-button>
                            </a-form-item>
                            <a-form-item v-if="fomKey == '2'">
                                <a-button type="link" @click="(fomKey = '1') && switchType()">密码登录</a-button>
                            </a-form-item>
                        </a-form>
                    </a-tab-pane>
                </a-tabs>
            </div>
        </div>
        <div class="foot">
            <span style="color:#fff">京ICP备15030926号-3</span>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.bg-video{
    width: 100vw;
    height: 100vh;
    position: fixed;
    top: 0;
    left: 0;
    object-fit: cover;
    z-index: -1;
    background: url(/bg.png) no-repeat;
    background-size: cover;
    background-position: center;
}

.login {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 100%;

    &.mobile{
        .content{
            .box {
                width: 350px;
            }
        }
    }
    .head {
        padding: 20px 40px;
        display: flex;
        align-items: center;
    }
    .foot {
        padding: 20px 40px;
    }
    .content {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        .box {
            background: rgba(255, 255, 255, 0.8);
            width: 400px;
            height: 570px;
            overflow: auto;
            padding: 40px;
            border-radius: 1.5rem;
            box-shadow: 0 0 1rem rgba(0, 0, 0, 0.1);
            z-index: 1;

            .ant-btn-link {
                padding: 0;
            }
            .title {
                font-size: 23px;
                text-align: center;
                padding: 1rem;
            }

            .submit {
                width: 100%;
            }

            .input-code {
                width: calc(100% - 120px);
                border-radius: 8px 0 0 8px;
            }
            .input-img {
                border-radius: 0 8px 8px 0;
                display: inline-flex;
                overflow: hidden;
                width: 120px;
                height: 40px;
                vertical-align: bottom;
            }
        }
    }
}
</style>
