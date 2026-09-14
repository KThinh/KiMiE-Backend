"""Entry point cho Hugging Face Spaces (SDK = gradio). Space chạy trực tiếp file này
(`python app.py`), nên nó phải nằm ở gốc repo và tự khởi động server — khác với chạy local
bằng `uvicorn app.app:app --reload` (dùng khi dev, xem README).

File này lấy nguyên app FastAPI thật ở app/app.py (toàn bộ API + trang web tĩnh đã mount ở đó),
gắn thêm 1 giao diện Gradio nhỏ tại /gradio (bắt buộc phải có ít nhất 1 thứ dùng Gradio để đúng
quy ước SDK "gradio" của Spaces) rồi tự chạy uvicorn trên cổng 7860 — cổng cố định mà Spaces
dùng cho mọi SDK không phải Docker (không cấu hình được qua README như app_port của SDK Docker).
"""

import gradio as gr
import uvicorn

from app.app import app as fastapi_app

with gr.Blocks(title="KIMVIE API") as gradio_ui:
    gr.Markdown(
        "# KIMVIE API\n"
        "Đây là backend của KIMVIE — trang thương mại điện tử cho các làng nghề thủ công. "
        "Trang web thật (nếu repo frontend được mount cạnh backend) nằm ở đường dẫn gốc `/`, "
        "tài liệu API (Swagger UI) ở [`/docs`](/docs), health check ở [`/api/health`](/api/health).\n\n"
        "(Lưu ý: trang này chỉ để xác nhận Space chạy đúng — vào bằng `/gradio/` có dấu `/` cuối,"
        " thiếu dấu `/` sẽ ra 404 do cách Gradio mount vào FastAPI.)"
    )

app = gr.mount_gradio_app(fastapi_app, gradio_ui, path="/gradio")

# app/app.py mount trang web tĩnh ở "/" bằng StaticFiles — đó là 1 route "Mount" khớp MỌI path
# (catch-all), nên nếu nó đứng trước route /gradio trong danh sách routes thì sẽ trả 404 trước
# khi Starlette kịp thử /gradio. Đẩy mọi Mount("/") xuống cuối để các route cụ thể hơn (bao gồm
# /gradio) luôn được thử trước — sort ổn định nên không đổi thứ tự tương đối giữa các route khác.
app.router.routes.sort(key=lambda route: getattr(route, "path", "") in ("", "/"))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
