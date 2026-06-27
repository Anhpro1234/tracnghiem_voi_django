document.addEventListener("DOMContentLoaded", function () {
    const container = document.getElementById('exam-timer-container');
    const timerText = document.getElementById('exam-timer-text');
    const progressBar = document.getElementById('exam-timer-bar');
    const examEndStr = window.EXAM_END_TIME || '';
    const totalMinutes = window.TOTAL_MINUTES || 0;

    if (!container || !timerText || !progressBar || !examEndStr || totalMinutes <= 0) {
        if (container) container.style.display = 'none';
        return;
    }

    const endTime = new Date(examEndStr).getTime();
    // Tổng thời gian ban đầu (ms) - luôn cố định dù refresh
    const totalDuration = totalMinutes * 60 * 1000;

    if (endTime <= Date.now()) {
        container.style.display = 'none';
        document.getElementById('exam-form')?.submit();
        return;
    }

    container.style.display = 'flex';

    function updateTimer() {
        const now = Date.now();
        const distance = endTime - now;

        if (distance <= 0) {
            timerText.textContent = "⏳ 00:00";
            progressBar.style.width = "0%";
            clearInterval(interval);
            document.getElementById('exam-form')?.submit();
            return;
        }

        const m = Math.floor((distance % 3600000) / 60000);
        const s = Math.floor((distance % 60000) / 1000);
        timerText.textContent = `⏳ ${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;

        const percentLeft = (distance / totalDuration) * 100;
        progressBar.style.width = percentLeft + '%';

        if (percentLeft < 20) {
            progressBar.className = 'progress-bar bg-danger';
        } else if (percentLeft < 50) {
            progressBar.className = 'progress-bar bg-warning';
        } else {
            progressBar.className = 'progress-bar bg-success';
        }
    }

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
});
// === ĐỒNG HỒ ĐẾM NGƯỢC TỪ SERVER ===
(function() {
    const container = document.getElementById('exam-timer-container');
    const timerText = document.getElementById('exam-timer-text');
    const progressBar = document.getElementById('exam-timer-bar');
    const examEndStr = window.EXAM_END_TIME || '';
    const totalMinutes = window.TOTAL_MINUTES || 0;

    if (!container || !timerText || !progressBar || !examEndStr || totalMinutes <= 0) {
        if (container) container.style.display = 'none';
        return;
    }

    const endTime = new Date(examEndStr).getTime();
    const totalDuration = totalMinutes * 60 * 1000;

    function update() {
        const now = Date.now();
        const distance = endTime - now;

        if (distance <= 0) {
            timerText.textContent = '00:00';
            progressBar.style.width = '0%';
            document.getElementById('quizForm')?.submit();
            return;
        }

        const m = Math.floor((distance % 3600000) / 60000);
        const s = Math.floor((distance % 60000) / 1000);
        timerText.textContent = `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;

        const percent = (distance / totalDuration) * 100;
        progressBar.style.width = percent + '%';
    }

    update();
    setInterval(update, 1000);
    container.style.display = 'block';
})();