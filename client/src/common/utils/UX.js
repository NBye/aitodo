async function prompt(title, content, options = {}) {
    return new Promise((resolve, reject) => {
        uni.showModal(Object.assign({
            title,
            placeholderText: content,
            editable: true,
            success: ({ cancel, content }) => {
                if (cancel) {
                    resolve(null)
                } else if (!content.trim()) {
                    reject(new Error('未输入有效内容'));
                } else {
                    resolve(content);
                }
            },
            fail: reject,
        }, options));
    });
}

async function confirm(title, content, options = {}) {
    return new Promise((resolve, reject) => {
        uni.showModal(Object.assign({
            title,
            content,
            success: ({ confirm }) => {
                resolve(confirm);
            },
            fail: reject,
        }, options));
    });
}

async function toast(title, duration = 1.5, options = {}) {
    return new Promise((resolve, reject) => {
        uni.showToast(Object.assign({
            title,
            icon: options.icon || 'none',
            duration: duration * 1000,
            success: ({ confirm }) => {
                resolve(confirm);
            },
            fail: reject,
        }, options));
    });
}


export default {
    prompt, confirm, toast
}