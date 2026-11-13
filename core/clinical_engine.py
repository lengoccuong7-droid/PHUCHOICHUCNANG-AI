"""PHCN AI 1.9 - Engine suy luận lâm sàng có đối soát ngược.
Offline, giải thích được; không thay thế bác sĩ khám trực tiếp.
"""
from __future__ import annotations
import re, unicodedata
from typing import Dict, List, Any


def norm(s: Any) -> str:
    s = str(s or "").lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s)


def has(text: str, *terms: str) -> bool:
    t = norm(text)
    return any(norm(x) in t for x in terms)


def affirmed(text: str, *terms: str) -> bool:
    """Match a finding while avoiding common explicit negations immediately before it."""
    t = norm(text)
    for term in terms:
        term_n = norm(term)
        start = 0
        while True:
            idx = t.find(term_n, start)
            if idx < 0:
                break
            prefix = t[max(0, idx - 24):idx]
            if not re.search(r"\b(khong|khong co|phu nhan|khong ghi nhan|khong thay)\s*$", prefix):
                return True
            start = idx + len(term_n)
    return False


def _test_state(results: Dict[str, str]) -> Dict[str, List[str]]:
    """The legacy UI combines 'not done' and 'negative'. Never treat it as negative."""
    positive, unknown = [], []
    for name, value in (results or {}).items():
        if "duong tinh" in norm(value):
            positive.append(name)
        else:
            unknown.append(name)
    return {"positive": positive, "unknown": unknown}


def analyze_case(data: Dict[str, Any]) -> Dict[str, Any]:
    region = data.get("region", "Chưa xác định")
    tests = _test_state(data.get("tests", {}))
    pos = tests["positive"]
    unknown_tests = tests["unknown"]
    history = " ".join(str(data.get(k, "") or "") for k in ["reason", "history", "site", "onset", "character", "radiation", "associations", "course"])
    exam = " ".join(str(data.get(k, "") or "") for k in ["inspection", "palpation", "rom_mmt"])
    all_text = norm(history + " " + exam)
    red_checked = data.get("red_flags", {})
    red_positive = [label for label, checked in red_checked.items() if checked]

    # Symptom-derived warning terms: prompts review; not a diagnosis.
    warning_terms = {
        "Rối loạn cơ tròn / bí tiểu / mất kiểm soát đại tiểu tiện": ["bi tieu", "bi tieu", "tieu khong tu chu", "dai tien khong tu chu", "mat kiem soat dai tieu tien"],
        "Yếu cơ tiến triển / yếu hai chân / dáng đi xấu nhanh": ["yeu tang dan", "yeu tien trien", "yeu hai chan", "di lai xau nhanh"],
        "Tê vùng yên ngựa": ["te vung yen ngua", "te vung hoi am"],
        "Sốt / rét run / dấu nhiễm trùng": ["sot", "ret run", "nhiem trung"],
        "Tiền sử ung thư / sụt cân không chủ ý": ["ung thu", "sut can khong chu y"],
        "Chấn thương đáng kể / không chịu lực được": ["chan thuong manh", "nga cao", "khong chiu luc duoc", "khong the chiu luc"],
    }
    inferred_warnings=[]
    for label, terms in warning_terms.items():
        if affirmed(all_text, *terms): inferred_warnings.append(label)
    all_red = list(dict.fromkeys(red_positive + inferred_warnings))

    missing=[]
    required = [("Lý do khám", "reason"), ("Vị trí triệu chứng", "site"), ("Diễn tiến", "course"), ("Khám thực thể", "inspection"), ("ROM/MMT", "rom_mmt")]
    for label,key in required:
        if not str(data.get(key, "") or "").strip(): missing.append(label)
    if not data.get("radiation", "").strip(): missing.append("Hướng lan / xác nhận không lan")
    if not data.get("tests"): missing.append("Kết quả nghiệm pháp")

    # Explicitly separate findings that support, oppose, or remain unknown.
    supporting=[]; opposing=[]; unresolved=[]; hypotheses=[]
    radicular = affirmed(history, "lan xuong chan", "lan xuong ban chan", "lan xuong ngon chan", "lan xuong tay", "te bi", "kien bo")
    no_radiation = has(data.get("radiation", ""), "khong lan", "khong co huong lan", "khong lan xa")
    mechanical = affirmed(history, "khoa khop", "ket khop", "luc cuc", "sung sau van dong", "dau khi xoay")
    groin = affirmed(history, "dau ben", "dau vung ben", "dau mat truoc khop hang", "dau hang")
    weakness = affirmed(exam, "yeu co", "mat luc", "suc co giam")
    trauma = affirmed(history, "nga", "va dap", "chan thuong", "xoay van")

    # Region-specific pattern hypotheses. No single special test is treated as confirmatory.
    if region == "Cột sống thắt lưng":
        if radicular and any("Lasègue" in x or "SLR" in x or "Bragard" in x for x in pos):
            hypotheses.append("Kiểu hình đau thắt lưng kèm triệu chứng kiểu rễ thần kinh: cần khám thần kinh theo rễ và đối chiếu phân bố đau/tê.")
            supporting += ["Có mô tả triệu chứng lan hoặc dị cảm", "Có ít nhất một nghiệm pháp căng thần kinh được ghi dương tính"]
        elif radicular:
            hypotheses.append("Có triệu chứng lan/dị cảm; chưa đủ dữ liệu để quy kết bệnh lý rễ thần kinh.")
            supporting.append("Bệnh sử có mô tả lan hoặc dị cảm")
        else:
            hypotheses.append("Đau thắt lưng chưa phân nhóm được từ dữ liệu hiện có; cần phân biệt đau cơ học, đau quy chiếu, đau kiểu rễ và nguyên nhân ngoài cơ xương khớp.")
        if no_radiation and radicular: opposing.append("Bệnh sử có mô tả lan nhưng trường hướng lan lại ghi không lan: cần xác minh trực tiếp.")
        if has(all_text, "tang khi cui", "tang khi ngoi lau", "giam khi di lai"): supporting.append("Có mô tả liên quan tư thế/tải cơ học")
    elif region == "Cột sống cổ":
        arm_rad = has(history, "lan xuong tay", "lan xuong ngon tay", "te ngon tay", "te ban tay")
        if arm_rad and "Spurling Test" in pos:
            hypotheses.append("Có kiểu hình nghi kích thích rễ thần kinh cổ; cần đối chiếu cảm giác, sức cơ, phản xạ theo khoanh tủy và loại trừ bệnh lý tủy.")
            supporting += ["Triệu chứng lan/dị cảm chi trên", "Spurling được ghi dương tính"]
        elif arm_rad:
            hypotheses.append("Có triệu chứng chi trên; cần phân biệt nguồn gốc cổ, thần kinh ngoại biên và bệnh lý vai.")
            supporting.append("Có mô tả lan/tê chi trên")
        else:
            hypotheses.append("Chưa đủ dữ liệu phân loại đau cổ; cần đánh giá vận động cổ, thần kinh chi trên và dấu hiệu bệnh lý tủy.")
        if "Lhermitte Sign" in pos or "Babinski Sign" in pos: all_red.append("Dấu hiệu gợi ý tổn thương đường dẫn truyền trung ương/tủy: cần đánh giá y khoa sớm")
    elif region == "Khớp vai":
        cuff_tests=[x for x in pos if any(k in x for k in ["Jobe", "Neer", "Hawkins"])]
        if cuff_tests and has(history, "dau khi nang tay", "dau khi dang tay", "dau ve dem", "dau khi nam nghieng"):
            hypotheses.append("Kiểu hình đau vai liên quan chóp xoay/chạm dưới mỏm cùng có thể được cân nhắc; các test dương tính không tự xác nhận rách gân.")
            supporting += ["Có test vai liên quan chóp xoay/chạm vai dương tính", "Bệnh sử có đau khi nâng/dạng tay hoặc đau về đêm"]
        elif cuff_tests:
            hypotheses.append("Có test vai dương tính nhưng bệnh sử chưa đủ tương hợp; cần xác minh vị trí đau, cung đau, sức cơ và ROM thụ động.")
        else:
            hypotheses.append("Chưa đủ dữ liệu phân nhóm đau vai; cần phân biệt bệnh lý chóp xoay, đông cứng khớp vai, khớp cùng-đòn và đau quy chiếu từ cổ.")
        if has(exam, "rom thu dong han che", "han che rom thu dong", "xoay ngoai han che"): supporting.append("Ghi nhận hạn chế ROM thụ động; cần đối chiếu kiểu hạn chế đa hướng")
    elif region == "Khớp gối":
        if "Lachman Test" in pos:
            hypotheses.append("Lachman dương tính làm tăng nghi ngờ mất vững dây chằng chéo trước; cần so sánh hai bên, đánh giá điểm cuối và bối cảnh chấn thương.")
            supporting.append("Lachman được ghi dương tính")
        if "McMurray Test" in pos and mechanical:
            hypotheses.append("Có thể cân nhắc tổn thương sụn chêm khi triệu chứng cơ học phù hợp; McMurray đơn độc không xác nhận rách sụn chêm.")
            supporting.append("McMurray dương tính kèm triệu chứng cơ học")
        if not hypotheses: hypotheses.append("Chưa đủ dữ liệu phân loại đau gối; cần đánh giá tràn dịch, chịu lực, ROM, vị trí đau và cơ chế chấn thương.")
    elif region == "Khớp háng":
        if groin and ("FADIR Test" in pos or "FABER / Patrick Test" in pos):
            hypotheses.append("Đau vùng bẹn kèm test khớp háng dương tính: cần đánh giá bệnh lý nội khớp háng; không thể kết luận FAI chỉ từ FADIR.")
            supporting += ["Đau vùng bẹn được mô tả", "Có test kích thích khớp háng dương tính"]
        else: hypotheses.append("Chưa đủ dữ liệu phân loại đau háng; cần phân biệt nội khớp, quanh khớp, cột sống thắt lưng và nguyên nhân vùng chậu.")
    else:
        hypotheses.append(f"Vùng {region}: chưa có bộ quy tắc suy luận chuyên biệt đã được thẩm định trong phiên bản này. Chỉ tổng hợp dữ liệu và yêu cầu bác sĩ đánh giá.")

    # Contradiction / reverse-audit layer.
    if trauma and has(history, "khong chan thuong", "khong co chan thuong"): opposing.append("Có mâu thuẫn giữa mô tả chấn thương và phủ nhận chấn thương.")
    if no_radiation and radicular: opposing.append("Mô tả hướng lan không nhất quán với phần triệu chứng khác.")
    if weakness and not has(exam, "ben", "trai", "phai", "2 ben"): unresolved.append("Có ghi yếu cơ nhưng chưa rõ nhóm cơ, bên và mức MMT.")
    if not pos: unresolved.append("Không có nghiệm pháp nào được ghi dương tính; điều này không đồng nghĩa đã loại trừ bệnh lý.")
    if unknown_tests: unresolved.append("Các test sau đang ở trạng thái 'Chưa làm / Âm tính'; hệ thống không thể phân biệt chưa thực hiện với âm tính: " + ", ".join(unknown_tests))
    if not str(data.get("rom_mmt", "") or "").strip(): unresolved.append("Chưa có số đo ROM/MMT nên chưa thể lượng giá hạn chế vận động hoặc suy giảm sức cơ.")
    if not str(data.get("inspection", "") or "").strip(): unresolved.append("Chưa có mô tả nhìn: sưng, biến dạng, teo cơ, dáng đi hoặc tư thế.")

    # Confidence is deliberately capped; no validated score/likelihood ratio is claimed.
    evidence_domains = sum(bool(x) for x in [history.strip(), exam.strip(), pos])
    if all_red:
        confidence="Không đưa ra kết luận PHCN trước khi đánh giá nguy cơ/cờ đỏ."
    elif evidence_domains >= 3 and supporting and not opposing:
        confidence="Mức định hướng: trung bình; cần xác minh bằng khám trực tiếp và dữ liệu còn thiếu."
    else:
        confidence="Mức định hướng: thấp; dữ liệu hiện tại chưa đủ để kết luận."

    safety=[]
    if all_red:
        safety.append("Có dấu hiệu cảnh báo được chọn hoặc phát hiện trong bệnh sử. Ưu tiên đánh giá y khoa trực tiếp; không tự động bắt đầu bài tập/điều trị thường quy trước khi làm rõ nguy cơ.")
    else:
        safety.append("Chưa ghi nhận cờ đỏ trong các mục hiện có; điều này KHÔNG loại trừ bệnh lý nghiêm trọng vì danh mục sàng lọc hiện tại còn giới hạn.")
    safety.append("Không dùng kết quả test đơn lẻ để xác nhận hoặc loại trừ chẩn đoán.")

    return {
        "region": region, "hypotheses": list(dict.fromkeys(hypotheses)),
        "supporting": list(dict.fromkeys(supporting)), "opposing": list(dict.fromkeys(opposing)),
        "unresolved": list(dict.fromkeys(unresolved)), "missing": missing,
        "red_flags": all_red, "confidence": confidence, "safety": safety,
        "positive_tests": pos, "unknown_tests": unknown_tests,
        "summary": str(data.get("reason", "") or "Chưa ghi nhận lý do khám")
    }


def render_report(result: Dict[str, Any]) -> str:
    def bullets(items): return "\n".join("- " + x for x in items) if items else "- Chưa có dữ liệu đủ để nhận định."
    sections = [
        "PHCN AI 1.9 – BÁO CÁO HỖ TRỢ SUY LUẬN LÂM SÀNG",
        f"Vùng khám: {result['region']}",
        "\n1. GIẢ THUYẾT / ĐỊNH HƯỚNG CẦN KIỂM CHỨNG\n" + bullets(result['hypotheses']),
        "\n2. DỮ KIỆN ỦNG HỘ\n" + bullets(result['supporting']),
        "\n3. DỮ KIỆN CHỐNG LẠI / MÂU THUẪN\n" + bullets(result['opposing']),
        "\n4. DỮ LIỆU CHƯA RÕ / CẦN BỔ SUNG\n" + bullets(result['unresolved']),
        "\n5. DỮ LIỆU CÒN THIẾU\n" + bullets(result['missing']),
        "\n6. CẢNH BÁO AN TOÀN\n" + bullets(result['red_flags'] + result['safety']),
        "\n7. MỨC ĐỘ TIN CẬY\n- " + result['confidence'],
        "\n8. KẾT LUẬN SỬ DỤNG\n- Đây là hỗ trợ tổng hợp dữ liệu, không phải chẩn đoán xác định. Bác sĩ cần đối chiếu khám trực tiếp, bệnh sử đầy đủ, cận lâm sàng khi có chỉ định và hướng dẫn chuyên môn hiện hành.",
    ]
    return "\n".join(sections)
