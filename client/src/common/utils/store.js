const data = {};
Object.entries(sessionStorage).forEach(([k, v]) => {
    try {
        data[k] = JSON.parse(v)
    } catch (e) {
        console.warn(`sessionStorage.${k} not json parse!`)
    }
})

export default new Proxy(data, {
    set(target, prop, value) {
        target[prop] = value;
        sessionStorage.setItem(prop, JSON.stringify(value));
        return true;
    },
    get(target, prop) {
        return target[prop];
    },
    deleteProperty(target, prop) {
        delete target[prop];
        sessionStorage.removeItem(prop)
        return true;
    }
});