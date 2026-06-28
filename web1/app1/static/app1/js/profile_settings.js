document.addEventListener("DOMContentLoaded", () => {
    const avatarInput = document.getElementById('avatar-input');
    const avatarPreview = document.getElementById('avatar-preview');

    if (avatarInput) {
        avatarInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();

                reader.onload = function(e) {
                    // Đổi src của thẻ img hiện tại thành ảnh mới chọn
                    avatarPreview.src = e.target.result;
                }

                reader.readAsDataURL(this.files[0]);
            }
        });
    }
});
