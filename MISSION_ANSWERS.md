# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. **Hardcode Secrets**: File chứa thông tin nhạy cảm như `OPENAI_API_KEY` và `DATABASE_URL` ngay trong mã nguồn. Nếu đẩy lên GitHub sẽ bị lộ ngay.
2. **Hardcode Configurations**: Các cấu hình như `DEBUG = True` và `MAX_TOKENS = 500` bị cố định, gây khó khăn khi cần thay đổi cho từng môi trường (dev, staging, prod) mà không sửa code.
3. **Sử dụng Print và Log Secret**: Sử dụng `print()` thay vì thư viện logging chuyên dụng, đồng thời log luôn cả thông tin nhạy cảm (`OPENAI_API_KEY`).
4. **Thiếu Health Check**: Không có các endpoint như `/health` hay `/ready`, khiến cloud platform không thể theo dõi trạng thái sống/chết của ứng dụng để tự động khởi động lại.
5. **Cố định Host và Port**: Bind vào `localhost` và port cố định `8000`, khiến app không thể giao tiếp với bên ngoài nếu chạy trong container (cần bind vào `0.0.0.0`) và không tương thích với việc các platform tự động gán port qua biến môi trường `PORT`.
6. **Reload=True**: Debug reload được bật sẵn, rất nguy hiểm nếu mang nguyên trạng lên môi trường production vì gây hao tốn tài nguyên và rủi ro bảo mật.

### Exercise 1.3: Comparison table
| Feature | Develop (Basic) | Production (Advanced) | Tại sao quan trọng? |
|---------|---------|------------|----------------|
| **Config**  | Hardcode trong code | Đọc từ Environment variables | Bảo mật thông tin nhạy cảm và linh hoạt thay đổi cấu hình mà không cần sửa/build lại code. |
| **Health check** | Không có | Có `/health` và `/ready` | Giúp Cloud Platform theo dõi sức khỏe app, tự động restart khi treo và cân bằng tải hiệu quả. |
| **Logging** | Dùng `print()` text thường | Structured JSON logging | Định dạng JSON dễ dàng được parse và phân tích bởi các hệ thống giám sát log (Datadog, Loki...). Tránh lộ secret. |
| **Shutdown** | Đột ngột (Sudden) | Graceful Shutdown | Nhận tín hiệu (SIGTERM) và xử lý nốt các request đang dang dở trước khi tắt, tránh mất dữ liệu hoặc gián đoạn dịch vụ của user. |
| **Host/Port** | Cố định `localhost:8000` | Bind `0.0.0.0` và đọc PORT từ Env | Đảm bảo chạy được trong môi trường Container (Docker) và đáp ứng yêu cầu cấp phát port động từ Cloud. |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. **Base image**: 
   - Develop sử dụng bản đầy đủ `python:3.11` (~1GB).
   - Production sử dụng multi-stage build với `python:3.11-slim` cho cả builder và runtime.
2. **Working directory**: Cả hai đều dùng thư mục `/app`.
3. **Tại sao COPY requirements.txt trước?**: Để tận dụng Docker Layer Cache. Nếu file `requirements.txt` không thay đổi, Docker sẽ sử dụng lại cache ở các lần build sau, bỏ qua lệnh tải và cài đặt packages bằng `pip install`, giúp giảm đáng kể thời gian build.
4. **CMD vs ENTRYPOINT khác nhau thế nào?**:
   - `ENTRYPOINT` quy định executable mặc định không thể thiếu khi container khởi động (rất khó bị ghi đè trừ khi dùng flag `--entrypoint`).
   - `CMD` có thể đóng vai trò truyền các argument mặc định cho `ENTRYPOINT`, hoặc đóng vai trò như lệnh sẽ thực thi (nếu chưa set ENTRYPOINT). `CMD` rất dễ dàng bị ghi đè khi ta gõ thêm argument ở lệnh `docker run <image> <command>`.

### Exercise 2.3: Image size comparison
- Develop: ~1000 MB (do dùng image gốc `python:3.11`)
- Production: ~150 MB (nhờ cơ chế multi-stage build và dùng `python:3.11-slim` chỉ chứa môi trường runtime)
- Difference: ~85% (giảm thiểu kích thước đáng kể, giúp kéo/đẩy image cực nhanh)

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- URL: https://vinai-day12-production-6dac.up.railway.app
- Screenshot: ![alt text](assets/image.png)

### Discussion Questions (README 03)
1. **Tại sao serverless (Lambda) không phải lúc nào cũng tốt cho AI agent?**
   - AI agent thường chạy các model ngôn ngữ lớn (cần nạp vào memory) hoặc duy trì connection dài để stream data (streaming response), trong khi Serverless Lambda có thời gian timeout hạn chế (ví dụ: 15 phút), không được thiết kế để giữ kết nối liên tục, và tốn thời gian tải memory.
2. **"Cold start" là gì? Ảnh hưởng thế nào đến UX?**
   - "Cold start" là hiện tượng khi ứng dụng bị tắt đi (do một thời gian nhàn rỗi không có request) và phải mất nhiều thời gian để khởi động lại (tải code, dependencies, nạp model...) khi có request mới. Điều này khiến response cho người dùng bị chậm trễ từ vài giây đến cả chục giây, gây cảm giác lag và đem lại trải nghiệm người dùng rất tệ.
3. **Khi nào nên upgrade từ Railway lên Cloud Run?**
   - Nên upgrade khi ứng dụng bắt đầu cần chịu lượng tải khổng lồ ở môi trường Production thật, đòi hỏi độ ổn định siêu cao (SLA tốt), cần tích hợp chặt quy trình với các dịch vụ dữ liệu và bảo mật trong hệ sinh thái Google Cloud Platform (GCP), hoặc cần khả năng "scale to zero" nhưng linh hoạt thiết lập `min-instances` để tránh cold start.

## Part 4: API Security

### Exercise 4.1-4.3: Test results

**Test API Key (Exercise 4.1):**
```bash
# Không có API key (Thất bại)
$ curl -s -X POST https://vinai-day12-production-6dac.up.railway.app/ask -H "Content-Type: application/json" -d '{"question": "Hello"}'
{"detail":"Not authenticated"}

# Có API key hợp lệ (Thành công)
$ curl -s -X POST https://vinai-day12-production-6dac.up.railway.app/ask -H "X-API-Key: my-secret-key" -H "Content-Type: application/json" -d '{"question": "Hello"}'
{"question":"Hello","answer":"MOCK_ANSWER","model":"gpt-mock"}
```

**Test Rate Limiter (Exercise 4.3):**
```bash
# Sau khi gọi liên tục 10 request trong 1 phút, request thứ 11 sẽ trả về lỗi:
$ curl -s -X POST https://vinai-day12-production-6dac.up.railway.app/ask -H "X-API-Key: my-secret-key" -H "Content-Type: application/json" -d '{"question": "Spam"}'
{"detail":"Rate limit exceeded. Try again in 60 seconds."}
```

### Exercise 4.4: Cost guard implementation
- **Cách tiếp cận (Approach)**: Để tránh trường hợp 1 user xài vượt quá ngân sách API (VD: $10/tháng), ta sẽ tích hợp Redis để theo dõi (track) số tiền đã sử dụng của mỗi `user_id`. 
- **Quy trình hoạt động**: Mỗi khi có request, ta tính toán lượng token dự kiến sẽ dùng, quy đổi ra tiền (estimated_cost), và cộng dồn vào key `budget:{user_id}:{YYYY-MM}` trong Redis. Nếu số tiền vượt quá ngân sách cho phép, request sẽ bị chặn lại và trả về mã lỗi 402 Payment Required. Key này được set thời hạn (`expire`) là 32 ngày để tự động reset vào tháng sau.

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
- **5.1 Health checks**: Đã triển khai 2 endpoint là `/health` (Liveness probe - báo cho platform biết process vẫn còn sống) và `/ready` (Readiness probe - kiểm tra kết nối CSDL/Redis đã thông suốt chưa trước khi load balancer đẩy traffic vào).
- **5.2 Graceful shutdown**: Thiết lập module chặn tín hiệu `SIGTERM`. Khi container bị tắt, ứng dụng sẽ không nhận request mới, nhưng vẫn đợi cho các request hiện tại thực thi xong và lưu xong dữ liệu mới đóng hẳn, tránh mất mát dữ liệu của user.
- **5.3 Stateless design**: Refactor toàn bộ code lưu trữ `conversation_history` từ trong RAM (memory dict của process) sang Redis. Nhờ đó, bất kể request được đẩy vào instance (Agent) nào, nó đều có thể đọc/ghi được dữ liệu cũ một cách đồng nhất.
- **5.4 Load balancing**: Ứng dụng mô hình cân bằng tải với Nginx (trong `docker-compose`). Traffic sẽ được Nginx chia đều sang 3 instance Agent, giúp hệ thống không bị "nghẽn cổ chai" (bottleneck) ở một node duy nhất, đồng thời nếu 1 node chết, các node kia vẫn gánh tải bình thường.
