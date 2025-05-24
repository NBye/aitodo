const reat = function (num, len) {
    return ('0'.repeat(len) + num).slice(-len);
}
export default class IDate extends Date {
    format(type) {
        let y = reat(this.getFullYear(), 4);
        let m = reat(this.getMonth() + 1, 2);
        let d = reat(this.getDate(), 2);
        let h = reat(this.getHours(), 2);
        let i = reat(this.getMinutes(), 2);
        let s = reat(this.getSeconds(), 2);
        while (true) {
            if (/yyyy/.test(type)) {
                type = type.replace(/yyyy/g, y);
            } else if (/yy/.test(type)) {
                type = type.replace(/yy/g, y.substring(2));
            } else if (/mm/.test(type)) {
                type = type.replace(/mm/g, m);
            } else if (/m/.test(type)) {
                type = type.replace(/m/g, parseInt(m));
            } else if (/dd/.test(type)) {
                type = type.replace(/dd/g, d);
            } else if (/d/.test(type)) {
                type = type.replace(/d/g, parseInt(d));
            } else if (/hh/.test(type)) {
                type = type.replace(/hh/g, h);
            } else if (/h/.test(type)) {
                type = type.replace(/h/g, parseInt(h));
            } else if (/ii/.test(type)) {
                type = type.replace(/ii/g, i);
            } else if (/i/.test(type)) {
                type = type.replace(/i/g, parseInt(i));
            } else if (/ss/.test(type)) {
                type = type.replace(/ss/g, s);
            } else if (/s/.test(type)) {
                type = type.replace(/s/g, parseInt(s));
            } else {
                break;
            }
        }
        return type;
    }

    static format(type, date) {
        let idate = new IDate(date || new Date());
        return idate.format(type);
    }
}
