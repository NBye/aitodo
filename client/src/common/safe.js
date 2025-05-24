import devtools from 'devtools-detect';
const isPC = (() => {
    const userAgent                     = navigator.userAgent.toLowerCase();
    const isScreenWidthLarge            = window.innerWidth > 1024;
    const isMobile                      = /iphone|ipod|android|iPad|IEMobile|Windows Phone/i.test(userAgent);
    return isScreenWidthLarge && !isMobile;
})();
const checkDevtools = function () {
    let width                           = window.outerWidth - window.innerWidth > 100;
    let height                          = window.outerHeight - window.innerHeight > (isPC?100:800);
    // console.log(window.outerWidth , window.innerWidth,window.screen.width,window.screen.availWidth,window.visualViewport.width)
    let start                           = Date.now();
    debugger;
    let devtoolsOpen                    = false;
    if (width || height) {
        devtoolsOpen                    = true;
    }
    if (Date.now() - start > 100) {
        devtoolsOpen                    = true;
    }
    if (devtoolsOpen) {
        document.body.innerHTML         = `<p style="text-align: center;padding-top: 20%;">
            <img src="/risk.png" style="width: 150px;"/>
            <br/>
            系统检测到风险访问，点击 <a href="javascript:void(0);window.location.reload();">刷新</a> 重试。
            </p>`;
    }
}
if (process.env.NODE_ENV !== 'development') {
    checkDevtools();
    setInterval(checkDevtools, 100);
}