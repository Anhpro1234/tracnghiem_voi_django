from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.contrib.auth.models import User
# 1. Custom User
class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Ban Giám Đốc / Admin'
        TEACHER = 'TEACHER', 'Giáo viên'
        STUDENT = 'STUDENT', 'Học sinh'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)

    def is_teacher(self):
        return self.role == self.Role.TEACHER

    def is_student(self):
        return self.role == self.Role.STUDENT

# 2. Subject
class Subject(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tên môn học")
    code = models.CharField(max_length=20, unique=True, verbose_name="Mã môn học")

    def __str__(self):
        return self.name

# 3. Classroom
class Classroom(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tên lớp học")
    # Thêm trường mã lớp (class_code) để học sinh nhập
    class_code = models.CharField(max_length=10, unique=True, null=True, blank=True, verbose_name="Mã lớp")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='classrooms')
    created_at = models.DateTimeField(auto_now_add=True)
    students = models.ManyToManyField(User, limit_choices_to={'role': 'STUDENT'}, related_name='enrolled_classes', blank=True)

    def __str__(self):
        return self.name

# QUẢN LÝ DUYỆT HỌC SINH
class ClassEnrollment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Chờ xác nhận'),
        ('APPROVED', 'Đã tham gia'),
    ]
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='enrollments')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='class_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('classroom', 'student') # Một HS chỉ xin vào 1 lớp 1 lần

# 4. Quiz
class Quiz(models.Model):
    title = models.CharField(max_length=200, verbose_name="Tiêu đề đề thi")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='quizzes')
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'TEACHER'},
        verbose_name="Người tạo"
    )
    duration_minutes = models.PositiveIntegerField(
        null=True, blank=True,
        default=45,  # mặc định 45 phút
        help_text="Để trống nếu không giới hạn thời gian"
    )
    room_id = models.CharField(max_length=20, unique=True, verbose_name="Mã phòng thi")
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    show_answers_after = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# 5. Question
class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    content = models.TextField(verbose_name="Nội dung câu hỏi")

    def __str__(self):
        return self.content[:50]

# 6. Choice
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    content = models.CharField(max_length=255, verbose_name="Nội dung đáp án")
    is_correct = models.BooleanField(default=False, verbose_name="Đáp án đúng?")

    def __str__(self):
        return self.content

# 7. StudentAnswer
class StudentAnswer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, null=True, blank=True, on_delete=models.SET_NULL)
    is_correct = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'quiz', 'question')

class StudentExamSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField()
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'quiz')

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=100, blank=True, default='')
    avatar = models.ImageField(upload_to='profile_pics', blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} Profile'