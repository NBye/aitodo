import mitt from 'mitt';

export const EventBus = mitt();

/**
navbar-show                     navbar导航显示
navbar-hide                     navbar导航隐藏

organization-created            组织创建
organization-update             组织更新
organization-leave              组织销毁
organization-switch             选择组织

user-update        组织用户更新
user-remove        用户移除组织
user-invite        用户组织邀请

organization-action-create(action)
organization-action-update(action)
organization-action-remove(action)

organization-forbid             # 组织内无权限

chat-create({chat})
chat-update({chat})
chat-destroy({chat})

chat-user-join({chat,user})  chat用户列表刷新
chat-user-leave({chat,user})  chat用户列表刷新

chat-message-stream(message)
chat-message-remove(message)


file-statistics-refresh

knowledge-bucket-create
knowledge-bucket-remove
knowledge-bucket-update

knowledge-create
knowledge-remove
knowledge-update

task-create({task})
task-remove({task})
task-update({task})

*/

EventBus.$emitAsync = async function (event, ...args) {
    const listeners = this._events[event];
    if (listeners) {
        if (Array.isArray(listeners)) {
            for (const listener of listeners) {
                if (typeof listener === "function") {
                    await listener(...args); // 等待每个监听器完成
                }
            }
        } else if (typeof listeners === "function") {
            await listeners(...args);
        }
    }
};
export default {
    install(app) {
        app.config.globalProperties.$EventBus = EventBus
    },
};
