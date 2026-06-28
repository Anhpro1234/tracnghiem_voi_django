from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # Trang chủ
    path('', views.home, name='home'),

    # Lớp học
    path('create-class/', views.create_class, name='create_class'),
    path('delete-class/<int:class_id>/', views.delete_class, name='delete_class'),
    path('class/<int:class_id>/students/', views.view_class_students, name='view_class_students'),
    path('class/<int:class_id>/remove/<int:student_id>/', views.remove_student, name='remove_student'),
    path('enrollment/<int:enrollment_id>/<str:action>/', views.handle_enrollment, name='handle_enrollment'),

    # Giáo viên & Đề thi
    path('teacher-room/', views.teacher_room, name='teacher_room'),
    path('tao-de/', views.upload_create_quiz, name='upload_create_quiz'),
    path('edit-quiz/<int:quiz_id>/', views.edit_quiz, name='edit_quiz'),
    path('delete-quiz/<int:quiz_id>/', views.delete_quiz, name='delete_quiz'),

    # Học sinh
    path('student-room/', views.student_room, name='student_room'),
    path('lam-bai/<str:room_id>/', views.take_quiz, name='take_quiz'),
    path('view-result/<str:room_id>/', views.view_result, name='view_result'),

    # Tiện ích bổ sung
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('route-after-login/', views.login_redirect_view, name='login_redirect'),
    path('class/<int:class_id>/export-students/', views.export_class_students, name='export_class_students'),
    path('quiz/<int:quiz_id>/export-results/', views.export_quiz_results, name='export_quiz_results'),
    path('profile-settings/', views.profile_settings_view, name='profile_settings'),
    path('revoke-teacher/', views.revoke_teacher_view, name='revoke_teacher_role'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)