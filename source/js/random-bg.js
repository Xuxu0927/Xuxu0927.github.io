// 三张图片的路径列表（根据你的实际文件名）
const bgImages = [
    '/images/beijing1.jpg',
    '/images/beijing2.jpg',
    '/images/beijing3.jpg'
];

// 随机选择一张
const randomBg = bgImages[Math.floor(Math.random() * bgImages.length)];

// 应用到背景元素
const webBg = document.getElementById('web_bg');
if (webBg) {
    webBg.style.backgroundImage = `url(${randomBg})`;
}