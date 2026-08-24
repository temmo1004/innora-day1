// 產生滷味機待機頁的 QR（靜態，URL 固定就不必把 28KB 的 library 塞進頁面）
// 用 papnkukn/qrcode-svg（MIT）：node luwei/mkqr.js > luwei/qr.svg
global.window = {};
require('./qrcode.browser.js');
const url = process.argv[2] || 'https://temmo1004.github.io/innora-day1/luwei/';
const q = new window.QRCode({ content: url, padding: 0, width: 512, height: 512,
                              color: '#000', background: '#fff', ecl: 'M', join: true });
// 一定要補 viewBox：qrcode-svg 只輸出 width/height，縮放時會變成裁切不是縮小
process.stdout.write(q.svg().replace('<svg ', '<svg viewBox="0 0 512 512" '));
