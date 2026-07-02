from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


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


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=100, blank=True, default='')
    avatar = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    dob = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f'{self.user.username} Profile'


# 2. Subject
class Subject(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tên môn học")
    code = models.CharField(max_length=20, unique=True, verbose_name="Mã môn học")

    def __str__(self):
        return self.name


# 3. Classroom
class Classroom(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tên lớp học")
    class_code = models.CharField(max_length=10, unique=True, null=True, blank=True, verbose_name="Mã lớp")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='classrooms')
    created_at = models.DateTimeField(auto_now_add=True)
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, limit_choices_to={'role': 'STUDENT'},
                                      related_name='enrolled_classes', blank=True)

    def __str__(self):
        return self.name


# QUẢN LÝ DUYỆT HỌC SINH
class ClassEnrollment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Chờ xác nhận'),
        ('APPROVED', 'Đã tham gia'),
    ]
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='enrollments')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='class_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('classroom', 'student')


# ==========================================
# KHU VỰC NGÂN HÀNG CÂU HỎI
# ==========================================

# 4. Question (Bây giờ nó thuộc về Môn học, không thuộc về Quiz nữa)
class Question(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='questions',
                                verbose_name="Thuộc môn học")
    content = models.TextField(verbose_name="Nội dung câu hỏi")
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content[:50]


# 5. Choice
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    content = models.CharField(max_length=255, verbose_name="Nội dung đáp án")
    is_correct = models.BooleanField(default=False, verbose_name="Đáp án đúng?")

    def __str__(self):
        return self.content


# ==========================================
# KHU VỰC QUẢN LÝ ĐỀ THI
# ==========================================

# 6. Quiz (Đề thi)
class Quiz(models.Model):
    title = models.CharField(max_length=200, verbose_name="Tiêu đề đề thi")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='quizzes')
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        limit_choices_to={'role': 'TEACHER'},
        verbose_name="Người tạo"
    )
    duration_minutes = models.PositiveIntegerField(
        null=True, blank=True, default=45,
        help_text="Để trống nếu không giới hạn thời gian"
    )
    room_id = models.CharField(max_length=20, unique=True, verbose_name="Mã phòng thi")
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    show_answers_after = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Kéo câu hỏi từ Ngân hàng vào Đề thi thông qua bảng trung gian QuizQuestion
    questions = models.ManyToManyField(Question, through='QuizQuestion', related_name='quizzes')

    def __str__(self):
        return self.title


# 7. Bảng trung gian (Xác định câu hỏi nào nằm trong đề nào, số thứ tự bao nhiêu)
class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=1, verbose_name="Thứ tự câu hỏi")

    class Meta:
        unique_together = ('quiz', 'question')
        ordering = ['order']


# ==========================================
# KHU VỰC HỌC SINH LÀM BÀI
# ==========================================

class StudentExamSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)  # Sửa lại cho phép null để lúc tạo session không bị lỗi
    is_completed = models.BooleanField(default=False)
    shuffled_question_ids = models.JSONField(null=True, blank=True)
    shuffled_choice_ids = models.JSONField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'quiz')


class StudentAnswer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, null=True, blank=True, on_delete=models.SET_NULL)
    is_correct = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'quiz', 'question')