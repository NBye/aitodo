const prefix_key = 'storage_auto_type:';

const get = function (key) {
    return localStorage.getItem(key)
}
const set = function (key, data) {
    localStorage.setItem(key, JSON.stringify(data));
}
const del = function (key) {
    localStorage.removeItem(key);
}

export default function (key, val, timeout = 3600 * 24 * 30) {
    key = prefix_key + key;
    if (val === undefined) {
        let data = get(key);
        if (!data) {
            return null;
        }
        let { value, expire } = JSON.parse(data);
        if (expire && expire < Date.now()) {
            del(key);
            return null;
        }
        return value
    } else if (val === null) {
        del(key);;
    } else {
        set(key, { value: val, expire: Date.now() + timeout * 1000 });
    }
}
