from django import forms
from allauth.account.forms import LoginForm  # Import form đăng nhập gốc của Allauth


# ==========================================
# 1. FORM ĐĂNG NHẬP (Xử lý sửa thông báo lỗi trên hình)
# ==========================================
class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Sửa nội dung lỗi sai tài khoản/mật khẩu (Thay cho câu tiếng Anh trên hình)
        self.error_messages['LOGIN_FAILED'] = 'Tài khoản hoặc mật khẩu không chính xác. Vui lòng thử lại!'

        # (Tùy chọn) Sửa thêm thông báo nếu người dùng để trống ô nhập liệu
        if 'login' in self.fields:
            self.fields['login'].error_messages['required'] = 'Vui lòng nhập tên tài khoản hoặc email.'
        if 'password' in self.fields:
            self.fields['password'].error_messages['required'] = 'Vui lòng nhập mật khẩu.'


# ==========================================
# 2. FORM ĐĂNG KÝ (Giữ nguyên code cũ của bạn)
# ==========================================
# KHÔNG import allauth.account.forms.SignupForm ở đây nữa để tránh lỗi vòng tròn!
class CustomSignupForm(forms.Form):
    # Khai báo trường chọn quyền
    role = forms.ChoiceField(
        choices=[('student', '👨‍🎓 Học sinh'), ('teacher', '👨‍🏫 Giáo viên')],
        label="Bạn là ai?",
        widget=forms.Select(attrs={'class': 'clickable form-control mb-3'})
    )

    def signup(self, request, user):
        # Đây là hàm mặc định mà Allauth sẽ gọi khi lưu user mới

        # Lấy giá trị role từ form
        role = self.cleaned_data.get('role')

        # Gán quyền tương ứng
        if role == 'teacher':
            user.is_teacher = True
        else:
            user.is_student = True

        user.save()
        return user
