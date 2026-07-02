import os, csv, re, random, string, json
from datetime import timedelta
from .models import QuizQuestion
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth import logout, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils import timezone
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from .models import (
    Quiz, Question, Choice, Subject, StudentAnswer,
    Classroom, ClassEnrollment, StudentExamSession, Profile
)

User = get_user_model()


# ==========================================
# --- TIỆN ÍCH & CƠ BẢN ---
# ==========================================

def is_teacher(user): return user.is_authenticated and user.is_teacher()


def is_student(user): return user.is_authenticated and user.is_student()


def home(request):
    public_quizzes = Quiz.objects.filter(is_public=True, is_active=True)
    return render(request, 'app1/home.html', {'public_quizzes': public_quizzes})


def logout_view(request):
    logout(request)
    return redirect('login')


# ==========================================
# --- TÀI KHOẢN & HỒ SƠ ---
# ==========================================

def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        role = request.POST.get('role')

        if password != password_confirm:
            messages.error(request, "Mật khẩu xác nhận không khớp!")
            return redirect('signup')
        if User.objects.filter(username=username).exists():
            messages.error(request, "Tên đăng nhập đã tồn tại!")
            return redirect('signup')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.role = User.Role.TEACHER if role == 'teacher' else User.Role.STUDENT
        user.save()
        messages.success(request, "Đăng ký thành công!")
        return redirect('login')
    return render(request, 'account/signup.html')


@login_required(login_url='/accounts/login/')
def profile_settings_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Logic đổi mật khẩu
        if 'old_password' in request.POST:
            if request.user.check_password(request.POST.get('old_password')):
                request.user.set_password(request.POST.get('new_password'))
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "Đổi mật khẩu thành công!")
            else:
                messages.error(request, "Mật khẩu cũ sai!")
        # Logic cập nhật thông tin
        else:
            profile.full_name = request.POST.get('full_name', '').strip()
            request.user.email = request.POST.get('email', '').strip()

            # Xử lý ngày sinh an toàn
            dob = request.POST.get('dob')
            profile.dob = dob if dob else None

            if 'avatar' in request.FILES: profile.avatar = request.FILES['avatar']

            profile.save()
            request.user.save()
            messages.success(request, "Cập nhật thành công!")
        return redirect('profile_settings')
    return render(request, 'app1/profile_settings.html', {'profile': profile})


@login_required
def login_redirect_view(request):
    if is_teacher(request.user): return redirect('teacher_room')
    if is_student(request.user): return redirect('student_room')
    return redirect('home')


# ==========================================
# --- PHÒNG CHỨC NĂNG & VIEWPOINT ---
# ==========================================

@login_required(login_url='/accounts/login/')
def teacher_room(request):
    if not is_teacher(request.user): raise PermissionDenied()
    my_classes = Classroom.objects.filter(teacher=request.user).order_by('-created_at')
    pending_requests = ClassEnrollment.objects.filter(classroom__in=my_classes, status='PENDING').order_by(
        '-created_at')
    return render(request, 'app1/teacher_room.html',
                  {'my_quizzes': Quiz.objects.filter(creator=request.user), 'my_classes': my_classes,
                   'pending_requests': pending_requests})


@login_required(login_url='/accounts/login/')
def student_room(request):
    # Kiểm tra quyền: Cho phép học sinh thật HOẶC giáo viên đang dùng góc nhìn học sinh
    is_teacher_viewing = is_teacher(request.user) and request.session.get('is_viewing_as_student')
    if not (is_student(request.user) or is_teacher_viewing):
        raise PermissionDenied("Bạn không có quyền vào phòng Học sinh!")

    user = request.user

    # XỬ LÝ KHI NGƯỜI DÙNG BẤM NÚT
    if request.method == 'POST':

        # 1. Bấm nút "Vào thi"
        if 'btn_vao_thi' in request.POST:
            room_id = request.POST.get('room_id', '').strip()
            if Quiz.objects.filter(room_id=room_id, is_active=True).exists():
                # Chuyển hướng sang Phòng xác nhận (Phòng chờ)
                return redirect('enter_quiz_room', room_id=room_id)
            messages.error(request, "Mã phòng thi không tồn tại hoặc đề thi đang đóng!")

        # 2. Bấm nút "Tham gia lớp học"
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

    # DỮ LIỆU HIỂN THỊ LÊN TRANG
    joined_classes = ClassEnrollment.objects.filter(student=user, status='APPROVED')
    pending_classes = ClassEnrollment.objects.filter(student=user, status='PENDING')

    return render(request, 'app1/student_room.html', {
        'joined_classes': joined_classes,
        'pending_classes': pending_classes,
    })


@login_required
def revoke_teacher_view(request):
    if is_teacher(request.user):
        request.user.role = User.Role.STUDENT
        request.user.save()
        messages.success(request, "Đã trở thành Học sinh.")
    return redirect('student_room')

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

        quiz = Quiz.objects.create(
            title=f"Đề: {file.name}", creator=request.user, subject=subject,
            room_id=''.join(random.choices(string.digits, k=6)), is_active=False
        )

        current_q, current_choices = None, []
        current_table_html = ""
        order_counter = 1

        # --- CÔNG TẮC NGẮT (Flag) ---
        in_answer_section = False
        junk_keywords = ["Nguồn", "Đơn vị", "Niên giám", "Thống kê"]

        def flush_question(q_content, choices_list, table_html):
            nonlocal order_counter
            if q_content and choices_list:
                q = Question.objects.create(
                    subject=subject,
                    content=q_content.strip() + (f"<br>{table_html}" if table_html else ""),
                    creator=request.user
                )
                for c in choices_list:
                    Choice.objects.create(question=q, content=c['text'], is_correct=c['is_correct'])

                QuizQuestion.objects.create(quiz=quiz, question=q, order=order_counter)
                order_counter += 1

        # Duyệt XML Body
        for child in doc.element.body:
            # 1. Xử lý đoạn văn
            if child.tag.endswith('p'):
                p = Paragraph(child, doc)
                text = p.text.strip()
                if not text: continue

                # --- KIỂM TRA ĐIỂM NGẮT (ĐÁP ÁN) ---
                # Nếu thấy chữ "ĐÁP ÁN" -> bật công tắc ngắt
                if "ĐÁP ÁN" in text.upper() or "HƯỚNG DẪN GIẢI" in text.upper():
                    in_answer_section = True

                # Nếu công tắc đang bật -> BỎ QUA dòng này
                if in_answer_section:
                    continue

                    # Bỏ qua các đoạn văn bản rác khác
                if any(keyword.lower() in text.lower() for keyword in junk_keywords):
                    continue

                if re.match(r'^(Câu|Cau)\s*\d+[:\.\s]+', text, re.IGNORECASE):
                    flush_question(current_q, current_choices, current_table_html)
                    current_q = re.sub(r'^(Câu|Cau)\s*\d+[:\.\s]+', '', text, flags=re.IGNORECASE)
                    current_choices = []
                    current_table_html = ""

                elif re.search(r'^[A-D][\.\)\s]+', text, re.IGNORECASE):
                    parts = re.split(r'(?=[A-D][\.\)\s]+)', text)
                    for part in parts:
                        part = part.strip()
                        if not part: continue
                        clean_text = re.sub(r'^\*?[A-D][\.\)\s]+', '', part).strip()
                        # Lọc rác nhỏ
                        if any(keyword.lower() in clean_text.lower() for keyword in junk_keywords):
                            continue
                        is_correct = '*' in part
                        current_choices.append({'text': clean_text, 'is_correct': is_correct})

                elif current_q and not current_choices:
                    current_q += " " + text

            # 2. Xử lý Bảng
            elif child.tag.endswith('tbl'):
                # Nếu đang ở khu vực đáp án thì bỏ qua bảng luôn
                if in_answer_section: continue

                table = Table(child, doc)
                html_table = "<table class='table table-bordered'>"
                for row in table.rows:
                    html_table += "<tr>"
                    for cell in row.cells:
                        html_table += f"<td>{cell.text}</td>"
                    html_table += "</tr>"
                html_table += "</table>"
                current_table_html = html_table

        flush_question(current_q, current_choices, current_table_html)
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
    if 'btn_vao_thi' in request.POST:
        room_id = request.POST.get('room_id', '').strip()
        if Quiz.objects.filter(room_id=room_id, is_active=True).exists():
            return redirect('enter_quiz_room', room_id=room_id)  # Sửa ở đây
        messages.error(request, "Mã phòng thi không tồn tại!")
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


def profile_settings_view(request):
    # Lấy hoặc tạo profile nếu chưa có
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Cập nhật thông tin User (nếu cần)
        request.user.email = request.POST.get('email')
        request.user.save()

        # Cập nhật Avatar nếu có file mới
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
            profile.save()

        messages.success(request, "Cập nhật hồ sơ thành công!")
        return redirect('profile_settings')

    return render(request, 'app1/profile_settings.html', {'profile': profile})



@login_required
def profile_settings_view(request):
    # Lấy chính xác bản ghi Profile của User, nếu chưa có thì tự động tạo mới
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()

        # Cập nhật họ tên vào Profile
        profile.full_name = full_name

        # Xử lý hình ảnh Avatar
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']

        # Lưu lại bảng Profile trước
        profile.save()

        # Cập nhật Email vào bảng User nếu có thay đổi
        if email:
            request.user.email = email
            request.user.save()

        messages.success(request, "Cập nhật tài khoản thành công!")
        return redirect('profile_settings')

    # BẮT BUỘC: Truyền túi data 'profile' này ra ngoài để HTML hứng trực tiếp
    return render(request, 'app1/profile_settings.html', {'profile': profile})


@login_required
def profile_settings_view(request):
    from .models import Profile
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # --- LOGIC ĐỔI MẬT KHẨU ---
        if 'change_password' in request.POST:
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')

            # Kiểm tra mật khẩu cũ
            if request.user.check_password(old_password):
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)  # Giữ user không bị văng ra ngoài
                messages.success(request, "Đổi mật khẩu thành công!")
            else:
                messages.error(request, "Mật khẩu hiện tại không đúng!")
            return redirect('profile_settings')

        # --- LOGIC CẬP NHẬT THÔNG TIN CHUNG (Avatar, Tên, Email) ---
        else:
            full_name = request.POST.get('full_name', '').strip()
            # Lấy email, nếu user xóa trắng thì nó sẽ là chuỗi rỗng ""
            email = request.POST.get('email', '').strip()

            profile.full_name = full_name

            if 'avatar' in request.FILES:
                profile.avatar = request.FILES['avatar']

            profile.save()

            # Gắn/Gỡ email thoải mái (kể cả để trống)
            request.user.email = email
            request.user.save()

            messages.success(request, "Cập nhật thông tin thành công!")
            return redirect('profile_settings')

    return render(request, 'app1/profile_settings.html', {'profile': profile})


@login_required
def revoke_teacher_view(request):
    user = request.user

    if user.role == User.Role.TEACHER:
        user.role = User.Role.STUDENT
        user.save()
        # Đồng bộ lại object từ database ngay lập tức
        user.refresh_from_db()
        messages.success(request, "Đã gỡ quyền Giáo viên. Bạn giờ là Học sinh!")
    else:
        messages.info(request, "Bạn hiện không phải là Giáo viên.")

    return redirect('student_room')


@login_required(login_url='/accounts/login/')
def enter_quiz_room(request, room_id):
    # Lấy thông tin đề thi
    quiz = get_object_or_404(Quiz, room_id=room_id, is_active=True)

    # Kiểm tra xem học sinh đã từng vào chưa
    # session, created = StudentExamSession.objects.get_or_create(user=request.user, quiz=quiz)

    return render(request, 'app1/enter_quiz.html', {'quiz': quiz})