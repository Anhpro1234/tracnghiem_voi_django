# tracnghiem_voi_django

Một nền tảng trắc nghiệm trực tuyến dựa trên Django, lấy cảm hứng từ các nền tảng giáo dục phổ biến của Việt Nam như Azota, Wayground và Tracnghiem.net.

## Tổng Quan

Đây là một ứng dụng web được thiết kế để tạo, quản lý và làm các bài trắc nghiệm trực tuyến. Nó kết hợp một backend Python/Django mạnh mẽ với frontend hiện đại sử dụng JavaScript, HTML và CSS để cung cấp một trải nghiệm học tập tương tác.

## Tính Năng

- **Tạo Trắc Nghiệm**: Dễ dàng tạo và quản lý các câu hỏi trắc nghiệm
- **Làm Bài Trắc Nghiệm**: Giao diện tương tác để làm các bài trắc nghiệm
- **Quản Lý Bài Tập**: Tổ chức và phân loại các bài tập và trắc nghiệm
- **Giao Diện Thân Thiện**: Thiết kế sạch và trực quan
- **Thiết Kế Đáp Ứng**: Hoạt động liền mạch trên các thiết bị khác nhau

## Công Nghệ Sử Dụng

### Backend
- **Python** (11.6%)
- **Django Framework**: Framework web để xây dựng API backend và logic server

### Frontend
- **JavaScript** (34.6%): Chức năng tương tác và các tính năng động
- **HTML** (21%): Cấu trúc trang và bố cục
- **CSS** (32.8%): Tạo kiểu và thiết kế đáp ứng

## Cấu Trúc Dự Án

```
tracnghiem_voi_django/
├── Backend (Django)
│   └── Các tệp ứng dụng Python
├── Frontend
│   ├── Tệp JavaScript
│   ├── Mẫu HTML
│   └── Bảng tính CSS
└── Tệp cấu hình
```

## Bắt Đầu

### Yêu Cầu Cần Thiết
- Python 3.8 trở lên
- pip (Trình quản lý gói Python)
- Node.js (tùy chọn, nếu sử dụng các công cụ xây dựng JavaScript)

### Cài Đặt

1. Clone repository:
```bash
git clone https://github.com/Anhpro1234/tracnghiem_voi_django.git
cd tracnghiem_voi_django
```

2. Tạo môi trường ảo:
```bash
python -m venv venv
source venv/bin/activate  # Trên Windows: venv\Scripts\activate
```

3. Cài đặt các gói Python:
```bash
pip install -r requirements.txt
```

4. Chạy migrations:
```bash
python manage.py migrate
```

5. Khởi động máy chủ phát triển:
```bash
python manage.py runserver
```

6. Mở trình duyệt và điều hướng đến:
```
http://localhost:8000
```

## Sử Dụng

- Tạo trắc nghiệm thông qua bảng điều khiển quản trị hoặc giao diện web
- Chia sẻ liên kết trắc nghiệm với học sinh hoặc người học tập
- Theo dõi hiệu suất và kết quả trắc nghiệm
- Xem chi tiết phân tích và thống kê

## Nguồn Cảm Hứng

Dự án này lấy cảm hứng từ:
- **Azota.com**: Nền tảng công nghệ giáo dục
- **Wayground.com**: Nền tảng học tập trực tuyến
- **Tracnghiem.net**: Nền tảng trắc nghiệm Việt Nam

## Đóng Góp

Chúng tôi chào đón các đóng góp! Bạn có thể:
1. Fork repository
2. Tạo nhánh tính năng (`git checkout -b feature/TinhNangTuyetVoi`)
3. Commit các thay đổi của bạn (`git commit -m 'Thêm TinhNangTuyetVoi'`)
4. Push đến nhánh (`git push origin feature/TinhNangTuyetVoi`)
5. Mở Pull Request

## Giấy Phép

Dự án này hiện chưa có giấy phép. Vui lòng liên hệ với chủ sở hữu repository để biết thêm thông tin về giấy phép.

## Tác Giả

**Anhpro1234**
- GitHub: [@Anhpro1234](https://github.com/Anhpro1234)

## Hỗ Trợ

Để được hỗ trợ, báo cáo lỗi hoặc đặt câu hỏi, vui lòng mở một issue trên [repository GitHub](https://github.com/Anhpro1234/tracnghiem_voi_django/issues).

## Trạng Thái

Dự án này đang trong giai đoạn phát triển tích cực. Được tạo ngày 24 tháng 6 năm 2026.