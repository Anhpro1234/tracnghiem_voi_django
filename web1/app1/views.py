import re, random, string
from docx import Document
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth import logout
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Quiz, Question, Choice, Subject, StudentAnswer, Classroom, ClassEnrollment
import csv
from django.http import HttpResponse
from django.db.models import Count, Q
import random, json
from django.utils import timezone
from .models import StudentExamSession
from datetime import datetime, timedelta
# Định nghĩa User ngay sau import
User = get_user_model()
# --- TIỆN ÍCH ---
def is_teacher(user): return user.is_authenticated and user.is_teacher()


def is_student(user): return user.is_authenticated and user.is_student()


def home(request):
    public_quizzes = Quiz.objects.filter(is_public=True, is_active=True)
    return render(request, 'app1/home.html', {'public_quizzes': public_quizzes})


def logout_view(request):
    logout(request)
    return redirect('login')


# --- PHÒNG CHỨC NĂNG ---
@login_required(login_url='/accounts/login/')
def teacher_room(request):
    if not is_teacher(request.user): raise PermissionDenied("Bạn không có quyền vào phòng Giáo viên!")

    # Lấy các lớp của GV
    my_classes = Classroom.objects.filter(teacher=request.user).order_by('-created_at')

    # Lấy danh sách Học sinh đang "Chờ duyệt"
    pending_requests = ClassEnrollment.objects.filter(
        classroom__in=my_classes,
        status='PENDING'
    ).order_by('-created_at')

    return render(request, 'app1/teacher_room.html', {
        'my_quizzes': Quiz.objects.filter(creator=request.user).order_by('-created_at'),
        'my_classes': my_classes,
        'pending_requests': pending_requests,
    })


@login_required(login_url='/accounts/login/')
def student_room(request):
    if not is_student(request.user): raise PermissionDenied("Bạn không có quyền vào phòng Học sinh!")
    user = request.user

    joined_classes = ClassEnrollment.objects.filter(student=user, status='APPROVED')
    pending_classes = ClassEnrollment.objects.filter(student=user, status='PENDING')

    if request.method == 'POST':
        if 'btn_vao_thi' in request.POST:
            room_id = request.POST.get('room_id', '').strip()
            if Quiz.objects.filter(room_id=room_id, is_active=True).exists():
                return redirect('take_quiz', room_id=room_id)
            messages.error(request, "Mã phòng thi không tồn tại hoặc đề thi đang đóng!")

        elif 'btn_tham_gia_lop' in request.POST:
            class_code = request.POST.get('class_code', '').strip()
            try:
                classroom = Classroom.objects.get(class_code=class_code)
                if ClassEnrollment.objects.filter(classroom=classroom, student=user).exists():
                    messages.warning(request, "Bạn đã gửi yêu cầu tham gia lớp này rồi!")
                else:
                    ClassEnrollment.objects.create(classroom=classroom, student=user, status='PENDING')
                    messages.success(request, f"Đã gửi yêu cầu vào lớp {classroom.name}. Chờ giáo viên duyệt nhé!")
            except Classroom.DoesNotExist:
                messages.error(request, "Mã lớp không tồn tại! Kiểm tra lại xem.")
        return redirect('student_room')

    return render(request, 'app1/student_room.html', {
        'joined_classes': joined_classes,
        'pending_classes': pending_classes,
    })


# --- QUẢN LÝ LỚP HỌC ---
@login_required(login_url='/accounts/login/')
def create_class(request):
    if request.method == 'POST':
        name = request.POST.get('class_name')
        if name:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            Classroom.objects.create(name=name, teacher=request.user, class_code=code)
    return redirect('teacher_room')


@login_required(login_url='/accounts/login/')
def delete_class(request, class_id):
    classroom = get_object_or_404(Classroom, id=class_id, teacher=request.user)
    classroom.delete()
    return redirect('teacher_room')


@login_required(login_url='/accounts/login/')
def handle_enrollment(request, enrollment_id, action):
    if not is_teacher(request.user): raise PermissionDenied()
    enrollment = get_object_or_404(ClassEnrollment, id=enrollment_id, classroom__teacher=request.user)
    if action == 'approve':
        enrollment.status = 'APPROVED'
        enrollment.save()
        enrollment.classroom.students.add(enrollment.student)
        messages.success(request, f"Đã duyệt cho {enrollment.student.username} vào lớp {enrollment.classroom.name}.")
    elif action == 'reject':
        enrollment.delete()
        messages.warning(request, "Đã từ chối yêu cầu tham gia.")
    return redirect('teacher_room')


# --- QUẢN LÝ ĐỀ THI ---
@login_required(login_url='/accounts/login/')
def upload_create_quiz(request):
    if not is_teacher(request.user): raise PermissionDenied()
    if request.method == 'POST' and request.FILES.get('word_file'):
        file = request.FILES['word_file']
        subject = Subject.objects.get(id=request.POST.get('subject_id'))
        doc = Document(file)
        quiz = Quiz.objects.create(title=f"Đề: {file.name}", creator=request.user, subject=subject,
                                   room_id=''.join(random.choices(string.digits, k=6)), is_active=False)

        current_q, current_choices = None, []

        def flush_question(q_content, choices_list):
            if q_content and choices_list:
                q = Question.objects.create(quiz=quiz, content=q_content.strip())
                for c in choices_list: Choice.objects.create(question=q, content=c['text'], is_correct=c['is_correct'])

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text: continue
            if re.match(r'^(Câu|Cau)\s*\d+[:\.\s]+', text, re.IGNORECASE):
                flush_question(current_q, current_choices)
                current_q = re.sub(r'^(Câu|Cau)\s*\d+[:\.\s]+', '', text, flags=re.IGNORECASE)
                current_choices = []
            elif re.search(r'[A-D][\.\)\s]+', text, re.IGNORECASE):
                parts = re.split(r'(?=[A-D][\.\)\s]+)', text)
                for part in parts:
                    part = part.strip()
                    if not part: continue
                    is_correct = '*' in part
                    clean_text = re.sub(r'^\*?[A-D][\.\)\s]+', '', part).strip()
                    current_choices.append({'text': clean_text, 'is_correct': is_correct})
            elif current_q:
                current_q += " " + text
        flush_question(current_q, current_choices)
        return redirect('edit_quiz', quiz_id=quiz.id)
    return render(request, 'app1/upload_quiz.html', {'subjects': Subject.objects.all()})


@login_required(login_url='/accounts/login/')
def edit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.creator != request.user:
        raise PermissionDenied()

    if request.method == 'POST':
        # 1. Cập nhật đáp án đúng
        for question in quiz.questions.all():
            correct_id = request.POST.get(f'q_{question.id}')
            if correct_id:
                question.choices.update(is_correct=False)
                question.choices.filter(id=correct_id).update(is_correct=True)

        # 2. Xử lý thời gian làm bài
        duration_str = request.POST.get('duration_minutes', '').strip()

        if duration_str and duration_str.isdigit():
            new_duration = int(duration_str)
            if new_duration >= 0:
                quiz.duration_minutes = new_duration
                quiz.save()

                if new_duration > 0:
                    # Cập nhật end_time cho các session chưa hoàn thành
                    active_sessions = StudentExamSession.objects.filter(quiz=quiz, is_completed=False)
                    for session in active_sessions:
                        session.end_time = session.start_time + timedelta(minutes=new_duration)
                        session.save()
                    messages.success(request, f"Đã cập nhật thời gian làm bài: {new_duration} phút (áp dụng cho học sinh đang thi).")
                else:
                    # new_duration == 0: không giới hạn
                    StudentExamSession.objects.filter(quiz=quiz, is_completed=False).delete()
                    messages.success(request, "Đã tắt giới hạn thời gian. Học sinh có thể làm bài thoải mái.")
            else:
                # Số âm → đặt mặc định 30
                quiz.duration_minutes = 30
                quiz.save()
                messages.info(request, "Thời gian làm bài được đặt mặc định 30 phút (không nhận giá trị âm).")
        else:
            # Không nhập gì → mặc định 30
            quiz.duration_minutes = 30
            quiz.save()
            messages.info(request, "Thời gian làm bài được đặt mặc định 30 phút.")

        # 3. Xử lý nút "Xuất đề" (kích hoạt)
        if 'publish' in request.POST:
            quiz.is_active = True
            quiz.save()
            messages.success(request, "Đề thi đã được kích hoạt!")
            return redirect('teacher_room')

        # 4. Nếu chỉ lưu (nút "Lưu đáp án & thời gian")
        return redirect('edit_quiz', quiz_id=quiz.id)

    # GET request
    return render(request, 'app1/edit_quiz.html', {
        'quiz': quiz,
        'questions': quiz.questions.prefetch_related('choices').all(),
    })


@login_required(login_url='/accounts/login/')
def delete_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, creator=request.user)
    quiz.delete()
    return redirect('teacher_room')


# --- HỌC SINH LÀM BÀI ---
@login_required(login_url='/accounts/login/')
def take_quiz(request, room_id):
    quiz = get_object_or_404(Quiz, room_id=room_id, is_active=True)
    questions = quiz.questions.prefetch_related('choices').all()

    # 1. Xác định chế độ thời gian
    if quiz.duration_minutes and quiz.duration_minutes > 0:
        # Có giới hạn -> dùng StudentExamSession
        session, created = StudentExamSession.objects.get_or_create(
            user=request.user,
            quiz=quiz,
            defaults={'end_time': timezone.now() + timezone.timedelta(minutes=quiz.duration_minutes)}
        )

        if session.is_completed or timezone.now() >= session.end_time:
            messages.warning(request, "Thời gian làm bài đã kết thúc hoặc bạn đã nộp bài.")
            return redirect('view_result', room_id=room_id)

        # Xử lý mã đề
        if created or not session.shuffled_question_ids:
            question_ids = list(questions.values_list('id', flat=True))
            random.shuffle(question_ids)
            session.shuffled_question_ids = question_ids

            shuffled_choice_map = {}
            for q in questions:
                choice_ids = list(q.choices.values_list('id', flat=True))
                random.shuffle(choice_ids)
                shuffled_choice_map[str(q.id)] = choice_ids
            session.shuffled_choice_ids = shuffled_choice_map
            session.save()
        else:
            question_ids = session.shuffled_question_ids
            shuffled_choice_map = session.shuffled_choice_ids

        exam_end_time = session.end_time.isoformat()
        total_minutes = quiz.duration_minutes

    else:
        # Không giới hạn thời gian -> không dùng session, xáo trộn mỗi lần
        question_ids = list(questions.values_list('id', flat=True))
        random.shuffle(question_ids)

        shuffled_choice_map = {}
        for q in questions:
            choice_ids = list(q.choices.values_list('id', flat=True))
            random.shuffle(choice_ids)
            shuffled_choice_map[str(q.id)] = choice_ids

        exam_end_time = ''
        total_minutes = 0

    # Sắp xếp lại danh sách câu hỏi
    question_dict = {q.id: q for q in questions}
    ordered_questions = [question_dict[qid] for qid in question_ids if qid in question_dict]

    for q in ordered_questions:
        choice_dict = {c.id: c for c in q.choices.all()}
        choice_order = shuffled_choice_map.get(str(q.id), [])
        q.shuffled_choices = [choice_dict[cid] for cid in choice_order if cid in choice_dict]

    # 2. Xử lý POST nộp bài (chỉ có ý nghĩa với bài có giới hạn, nhưng vẫn cho nộp nếu không giới hạn)
    if request.method == 'POST':
        score = 0
        with transaction.atomic():
            StudentAnswer.objects.filter(user=request.user, quiz=quiz).delete()
            for q in ordered_questions:
                choice_id = request.POST.get(f'question_{q.id}')
                selected = Choice.objects.filter(id=choice_id, question=q).first() if choice_id else None
                is_correct = selected.is_correct if selected else False
                if is_correct:
                    score += 1
                StudentAnswer.objects.create(
                    user=request.user, quiz=quiz, question=q,
                    selected_choice=selected, is_correct=is_correct
                )
        request.session[f'score_{quiz.id}'] = score

        # Nếu có session, đánh dấu hoàn thành
        if 'session' in locals():
            session.is_completed = True
            session.save()

        return redirect('view_result', room_id=room_id)

    return render(request, 'app1/take_quiz.html', {
        'quiz': quiz,
        'questions': ordered_questions,
        'exam_end_time': exam_end_time,
        'total_minutes': total_minutes,
    })

@login_required(login_url='/accounts/login/')
def view_result(request, room_id):
    quiz = get_object_or_404(Quiz, room_id=room_id)
    total_questions = quiz.questions.count()
    return render(request, 'app1/view_result.html', {
        'quiz': quiz,
        'score': request.session.get(f'score_{quiz.id}', 0),
        'total_questions': total_questions,
        'student_answers': StudentAnswer.objects.filter(user=request.user, quiz=quiz).select_related('question',
                                                                                                     'selected_choice')
    })


# --- XEM DANH SÁCH & XÓA HỌC SINH KHỎI LỚP ---
@login_required(login_url='/accounts/login/')
def view_class_students(request, class_id):
    if not is_teacher(request.user): raise PermissionDenied()

    # Lấy thông tin lớp học (chỉ cho phép GV chủ nhiệm của lớp đó xem)
    classroom = get_object_or_404(Classroom, id=class_id, teacher=request.user)
    students = classroom.students.all()

    return render(request, 'app1/view_class_students.html', {
        'classroom': classroom,
        'students': students
    })


@login_required(login_url='/accounts/login/')
def remove_student(request, class_id, student_id):
    if not is_teacher(request.user): raise PermissionDenied()

    classroom = get_object_or_404(Classroom, id=class_id, teacher=request.user)
    from .models import User
    student = get_object_or_404(User, id=student_id)

    # Xóa khỏi danh sách học sinh của lớp
    classroom.students.remove(student)
    # Xóa luôn cả bản ghi xin vào lớp
    ClassEnrollment.objects.filter(classroom=classroom, student=student).delete()

    messages.success(request, f"Đã xóa học sinh {student.username} khỏi lớp {classroom.name}.")
    return redirect('view_class_students', class_id=classroom.id)

def forgot_password_view(request):
    return render(request, 'app1/forgot_password.html')

def signup_view(request):
    if request.method == 'POST':
        # ... logic tạo user ...
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


User = get_user_model()


def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        role = request.POST.get('role')  # 'student' hoặc 'teacher'

        # 1. Kiểm tra mật khẩu
        if password != password_confirm:
            messages.error(request, "Mật khẩu xác nhận không khớp!")
            return redirect('signup')

        # 2. Kiểm tra user đã tồn tại chưa
        if User.objects.filter(username=username).exists():
            messages.error(request, "Tên đăng nhập đã tồn tại!")
            return redirect('signup')

        # 3. Tạo User
        user = User.objects.create_user(username=username, email=email, password=password)

        # 4. Gán role
        if role == 'teacher':
            user.is_teacher_flag = True
        else:
            user.is_student_flag = True
        user.save()

        messages.success(request, "Đăng ký thành công! Mời bạn đăng nhập.")
        return redirect('account_login')  # Chuyển về trang đăng nhập của Allauth

    return render(request, 'account/signup.html')

@login_required
def login_redirect_view(request):
    """
    kiểm tra:
    Ai là Giáo viên thì bế vào phòng GV,
    Ai là Học sinh thì bế vào phòng HS.
    """
    if request.user.is_teacher():
        return redirect('teacher_room')
    elif request.user.is_student():
        return redirect('student_room')
    else:
        # Nếu là Admin hoặc role khác chưa phân loại
        return redirect('home')


@login_required
def export_class_students(request, class_id):
    """Xuất danh sách học sinh của một lớp học"""
    # 1. Kiểm tra quyền Giáo viên
    if not getattr(request.user, 'is_teacher', False):
        return HttpResponse("Bạn không có quyền truy cập!", status=403)

    classroom = get_object_or_404(Classroom, id=class_id)
    enrollments = ClassEnrollment.objects.filter(classroom=classroom)

    # 2. Khởi tạo file CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Danh_sach_lop_{classroom.id}.csv"'

    # BOM UTF-8 giúp Excel đọc Tiếng Việt mượt mà
    response.write('\ufeff'.encode('utf8'))

    writer = csv.writer(response)

    # 3. Viết dòng Header (Tiêu đề cột)
    writer.writerow(['STT', 'Tài khoản', 'Email', 'Ngày tham gia'])

    # 4. Đổ dữ liệu từ Database vào
    for idx, en in enumerate(enrollments, start=1):
        date_str = en.enrolled_at.strftime('%d/%m/%Y') if hasattr(en, 'enrolled_at') else "N/A"
        writer.writerow([idx, en.student.username, en.student.email, date_str])

    return response


@login_required
def export_quiz_results(request, quiz_id):
    """Xuất bảng điểm của một đề thi"""
    # 1. Kiểm tra quyền
    if not getattr(request.user, 'is_teacher', False):
        return HttpResponse("Bạn không có quyền truy cập!", status=403)

    quiz = get_object_or_404(Quiz, id=quiz_id)

    # 2. Setup file Excel CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Bang_diem_de_{quiz.id}.csv"'
    response.write('\ufeff'.encode('utf8'))  # Fix font Tiếng Việt

    writer = csv.writer(response)
    writer.writerow(['STT', 'Học sinh', 'Số câu đúng', 'Ngày thi'])

    # 3. Lấy dữ liệu điểm thực tế từ bảng StudentAnswer
    # Đếm số câu is_correct=True của từng user trong đề này
    results = StudentAnswer.objects.filter(quiz=quiz).values(
        'user__username'  # Lấy tên HS
    ).annotate(
        score=Count('id', filter=Q(is_correct=True)),  # Đếm câu đúng
    ).order_by('-score')  # Xếp hạng từ cao xuống thấp

    # 4. Ghi vào file
    for idx, rs in enumerate(results, start=1):
        # Trích xuất dữ liệu từ dict
        student_name = rs['user__username']
        score = rs['score']
        date_str = "Hoàn thành"

        writer.writerow([idx, student_name, score, date_str])

    return response



