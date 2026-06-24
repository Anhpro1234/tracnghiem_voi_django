from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Subject, Classroom, Quiz, Question, Choice, StudentAnswer

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Thêm trường role vào giao diện chỉnh sửa User
    fieldsets = UserAdmin.fieldsets + (
        ('Phân quyền', {'fields': ('role',)}),
    )
    # Hiển thị cột role ngoài danh sách
    list_display = ('username', 'email', 'role', 'is_staff')

# Đăng ký các bảng còn lại
admin.site.register(Subject)
admin.site.register(Classroom)
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(StudentAnswer)