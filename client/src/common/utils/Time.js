export default class Time {
    static async delay(sec = 1) {
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                resolve();
            }, sec * 1000);
        });
    }

    static async waiting(assert, callback) {
        let d = false;
        while (d === false) {
            d = await assert()
        }
        await callback(d)
        return d;
    }

    static async interval(each, sec = 1, times = 10) {
        return new Promise((resolve, reject) => {
            let r, n = 0, stop = (data) => {
                clearInterval(r);
                resolve(data);
            };
            each(n, stop);
            r = setInterval(() => {
                n++;
                try {
                    if (n == times) {
                        stop(null);
                    } else {
                        each(n, stop);
                    }
                } catch (e) {
                    clearInterval(r);
                    reject(e);
                }
            }, sec * 1000);
        });
    }
}
