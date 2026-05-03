// 三张图片的路径列表（根据你的实际文件名）
const bgImages = [
    '/images/beijing/beijing1.jpg',
    '/images/beijing/beijing2.jpg',
    '/images/beijing/beijing3.jpg',
    '/images/beijing/beijing4.jpg',
    '/images/beijing/beijing5.jpg'
];

// 随机选择一张
const randomBg = bgImages[Math.floor(Math.random() * bgImages.length)];

// 应用到背景元素
const webBg = document.getElementById('web_bg');
if (webBg) {
    webBg.style.backgroundImage = `url(${randomBg})`;
}