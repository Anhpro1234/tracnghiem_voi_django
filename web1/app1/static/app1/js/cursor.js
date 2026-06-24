document.addEventListener('DOMContentLoaded', () => {
    // 1. Tắt tính năng trên thiết bị cảm ứng (Mobile/Tablet)
    if (window.matchMedia("(pointer: coarse)").matches) return;

    const cursor = document.getElementById('custom-cursor');
    if (!cursor) return;

    // Hiển thị cursor giả
    cursor.style.display = 'block';

    let mouseX = -100, mouseY = -100;
    let cursorX = -100, cursorY = -100;
    const speed = 0.25; // Tốc độ trượt (0.1: siêu mượt/độ trễ cao, 1: dính sát chuột)

    // Lấy tọa độ chuột thật liên tục
    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });

    // Vòng lặp render bằng Frame của card màn hình (60-120 FPS)
    function renderCursor() {
        cursorX += (mouseX - cursorX) * speed;
        cursorY += (mouseY - cursorY) * speed;

        // Chỉ dịch chuyển tọa độ (X, Y). Phần căn tâm (-50%, -50%) hãy để CSS xử lý sẽ mượt hơn.
        cursor.style.transform = `translate3d(${cursorX}px, ${cursorY}px, 0)`;

        requestAnimationFrame(renderCursor);
    }
    requestAnimationFrame(renderCursor);

    // 2. Xử lý đổi trạng thái cursor bằng Event Delegation
    const interactiveSelector = 'a, button, [role="button"], input, textarea, .clickable, .nav-link, .btn';

    document.addEventListener('mouseover', (e) => {
        const target = e.target.closest(interactiveSelector);
        if (!target) return;

        // Kiểm tra xem có phải các ô nhập liệu văn bản không
        const isTextInput = ['text', 'email', 'password', 'search', 'number'].includes(target.type) || target.tagName === 'TEXTAREA';

        // Thêm class trạng thái tương ứng
        if (isTextInput) {
            cursor.classList.add('is-text');
        } else {
            cursor.classList.add('is-link');
        }
    });

    document.addEventListener('mouseout', (e) => {
        const target = e.target.closest(interactiveSelector);
        if (target) {
            // Xóa toàn bộ class trạng thái khi chuột rời đi, trả về cursor mặc định
            cursor.classList.remove('is-text', 'is-link');
        }
    });

});
