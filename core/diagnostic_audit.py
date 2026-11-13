"""PHCN AI 2.0 - Automatic bidirectional diagnostic audit.

Rule-based, transparent decision support. It does not calculate diagnostic
probabilities or claim validated sensitivity/specificity.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from core.clinical_engine import norm, affirmed, has


def _all_text(data: Dict[str, Any]) -> str:
    keys = (
        "reason", "history", "site", "onset", "character", "radiation",
        "associations", "course", "inspection", "palpation", "rom_mmt",
    )
    return " ".join(str(data.get(k, "") or "") for k in keys)


def _positive_tests(data: Dict[str, Any]) -> List[str]:
    return [str(name) for name, value in (data.get("tests") or {}).items()
            if "duong tinh" in norm(value)]


def _explicitly_denies(text: str, terms: Tuple[str, ...]) -> bool:
    """True only for an explicit negation close before a clinical feature."""
    t = norm(text)
    neg = r"(?:khong|khong co|phu nhan|khong ghi nhan|khong thay|chua tung)"
    for term in terms:
        term_n = norm(term)
        for match in re.finditer(re.escape(term_n), t):
            prefix = t[max(0, match.start() - 45):match.start()]
            if re.search(neg + r"(?:\s+[\w]+){0,3}\s*$", prefix):
                return True
    return False


def _spec(label: str, supports=(), contradicts=(), missing=(), caution=""):
    return {
        "label": label,
        "supports": list(supports),
        "contradicts": list(contradicts),
        "missing": list(missing),
        "caution": caution,
    }


# Each item is a clinical pattern to consider, not a definitive diagnosis.
# Phrases are deliberately broad; a positive match is a prompt for clinician review.
CATALOGUE = {
    "Cột sống thắt lưng": [
        _spec("Đau kiểu rễ thắt lưng-cùng / bệnh lý rễ thần kinh",
              [("Đau hoặc dị cảm lan theo chi dưới", ("lan xuong chan", "lan xuong ban chan", "lan xuong ngon chan", "te chan", "kien bo chan")),
               ("Nghiệm pháp căng thần kinh dương tính", ("Lasègue", "SLR", "Bragard"))],
              [("Bệnh nhân xác nhận không có triệu chứng lan", ("khong lan", "khong te", "khong kien bo"))],
              ["Phân bố đau/tê theo vùng da", "Sức cơ theo nhóm cơ/rễ, cảm giác và phản xạ", "Diễn tiến và dấu hiệu thần kinh tiến triển"],
              "Test căng thần kinh dương tính không tự xác nhận chèn ép rễ; cần tương hợp triệu chứng và khám thần kinh."),
        _spec("Đau thắt lưng cơ học không đặc hiệu",
              [("Đau liên quan tư thế hoặc tải", ("tang khi cui", "tang khi nang", "ngoi lau", "dung lau", "giam khi nghi", "dau khi van dong"))],
              [("Có dấu hiệu thần kinh khu trú/tiến triển được mô tả", ("yeu co tien trien", "mat cam giac vung yen ngua", "roi loan co tron"))],
              ["Khả năng chịu tải và yếu tố làm tăng/giảm đau", "Khám thần kinh chi dưới", "Sàng lọc nguyên nhân ngoài cơ xương khớp"],
              "Đau cơ học là kiểu hình, không đồng nghĩa đã xác định cấu trúc gây đau."),
        _spec("Đau quy chiếu từ khớp háng / vùng chậu",
              [("Đau bẹn hoặc vùng háng", ("dau ben", "dau vung ben", "dau khop hang")),
               ("Test kích thích khớp háng dương tính", ("FADIR", "FABER", "Patrick"))],
              [], ["ROM háng, đặc biệt xoay trong và gấp", "Khám khớp háng và vùng chậu"],
              "FABER/FADIR không đặc hiệu; cần xác định chính xác vị trí đau tái hiện."),
    ],
    "Cột sống cổ": [
        _spec("Bệnh lý rễ thần kinh cổ",
              [("Đau/tê lan xuống tay hoặc ngón tay", ("lan xuong tay", "lan xuong ngon tay", "te ngon tay", "te ban tay")),
               ("Spurling dương tính", ("Spurling",))],
              [("Xác nhận không có triệu chứng chi trên", ("khong lan xuong tay", "khong te tay", "khong te ngon tay"))],
              ["Cảm giác theo khoanh da, sức cơ theo myotome, phản xạ", "Phân biệt bệnh lý thần kinh ngoại biên", "Đánh giá dấu hiệu bệnh lý tủy"],
              "Spurling cần tái hiện triệu chứng quen thuộc lan theo chi; đau cổ tại chỗ đơn thuần không đủ."),
        _spec("Bệnh lý tủy cổ cần loại trừ",
              [("Rối loạn dáng đi/thăng bằng hoặc khéo léo bàn tay", ("di loang choang", "mat thang bang", "roi loan dang di", "vuong ve ban tay", "roi loan van dong tinh")),
               ("Dấu hiệu neuron vận động trung ương", ("Babinski", "clonus", "tang phan xa")),
               ("Lhermitte dương tính", ("Lhermitte",))],
              [], ["Khám thần kinh trung ương đầy đủ", "Diễn tiến triệu chứng và đánh giá chuyên khoa khi nghi ngờ"],
              "Nếu nghi bệnh lý tủy hoặc yếu tiến triển, ưu tiên đánh giá y khoa khẩn/sớm tùy mức độ; không tiếp tục xử trí thường quy."),
        _spec("Đau cổ cơ học / đau quy chiếu từ vai",
              [("Đau liên quan vận động/tư thế cổ", ("dau tang khi quay co", "dau khi cu dong co", "co cung co"))],
              [], ["ROM cổ", "Khám vai và thần kinh chi trên", "Dấu hiệu cảnh báo toàn thân"],
              "Không mặc định đau cổ là nguyên nhân của mọi triệu chứng chi trên."),
    ],
    "Khớp vai": [
        _spec("Đau liên quan chóp xoay",
              [("Đau khi nâng/dạng tay hoặc đau về đêm", ("dau khi nang tay", "dau khi dang tay", "dau ve dem", "dau khi nam nghieng")),
               ("Một test liên quan chóp xoay/chạm vai dương tính", ("Jobe", "Neer", "Hawkins"))],
              [("ROM thụ động hạn chế rõ đa hướng được mô tả", ("rom thu dong han che da huong", "han che rom thu dong ca huong"))],
              ["Sức cơ chóp xoay so sánh hai bên", "ROM chủ động và thụ động", "Cung đau và vị trí đau"],
              "Neer/Hawkins/Jobe không xác định riêng rách gân; đau khi test có thể làm giảm lực biểu kiến."),
        _spec("Viêm dính bao khớp vai (đông cứng khớp vai) cần phân biệt",
              [("Hạn chế ROM thụ động, đặc biệt xoay ngoài", ("xoay ngoai thu dong han che", "han che rom thu dong", "dong cung khop vai")),
               ("Cứng khớp tiến triển", ("cung khop", "han che van dong tang dan"))],
              [("ROM thụ động được ghi nhận bảo tồn", ("rom thu dong binh thuong", "rom thu dong bao ton"))],
              ["So sánh ROM chủ động/thụ động nhiều hướng", "Diễn tiến khởi phát và bệnh nền liên quan"],
              "Cần xác minh hạn chế thụ động thật sự; đau đơn thuần không đủ để kết luận đông cứng khớp."),
        _spec("Đau vai quy chiếu từ cột sống cổ / thần kinh",
              [("Đau/tê lan xuống cánh tay hoặc bàn tay", ("lan xuong tay", "te ngon tay", "te ban tay"))],
              [], ["Khám cổ và thần kinh chi trên", "Phân biệt triệu chứng tái hiện bởi vận động cổ hay vai"],
              "Cần khám cả cổ và vai khi biểu hiện chồng lấp."),
    ],
    "Khớp gối": [
        _spec("Tổn thương dây chằng chéo trước (ACL) cần đánh giá",
              [("Cơ chế xoay/trụ chân hoặc chấn thương", ("xoay van", "doi huong dot ngot", "chan thuong khi da bong", "tep goi")),
               ("Lachman dương tính", ("Lachman",)),
               ("Cảm giác gối mất vững", ("goi long leo", "mat vung goi"))],
              [("Không có chấn thương và không mất vững được xác nhận", ("khong chan thuong", "khong mat vung"))],
              ["So sánh Lachman hai bên và điểm cuối", "Tràn dịch/thời điểm sưng", "Khả năng chịu lực và cơ chế chấn thương"],
              "Lachman cần kỹ thuật chuẩn và so sánh hai bên; không suy ra đứt ACL chỉ từ đau gối."),
        _spec("Tổn thương sụn chêm cần phân biệt",
              [("Khóa khớp/kẹt khớp hoặc đau khe khớp", ("khoa khop", "ket khop", "dau khe khop")),
               ("McMurray dương tính", ("McMurray",))],
              [("Không có triệu chứng cơ học được xác nhận", ("khong khoa khop", "khong ket khop"))],
              ["Vị trí đau khe khớp", "Tràn dịch và cơ chế xoay chịu tải", "Khám phối hợp, không dựa một test"],
              "McMurray có giới hạn; test đơn độc không xác nhận rách sụn chêm."),
        _spec("Đau gối liên quan thoái hóa / tải cơ học",
              [("Đau khi chịu tải hoặc cứng khớp", ("dau khi di lai", "dau khi len cau thang", "cung khop buoi sang", "lo xao khop"))],
              [], ["Tuổi, thời gian cứng khớp, khám tràn dịch và ROM", "Mức ảnh hưởng chức năng và khả năng chịu tải"],
              "Cần đối chiếu tiêu chuẩn lâm sàng; hình ảnh học chỉ định theo bối cảnh."),
    ],
    "Khớp háng": [
        _spec("Bệnh lý nội khớp háng cần đánh giá",
              [("Đau bẹn/đau sâu vùng háng", ("dau ben", "dau sau trong ben", "dau sau trong khop hang")),
               ("Test FADIR/FABER dương tính", ("FADIR", "FADIR Test", "FABER", "Patrick"))],
              [], ["ROM háng, nhất là xoay trong và gấp", "Khả năng chịu lực và đau khi vận động", "Loại trừ gãy xương ở người có nguy cơ"],
              "Test kích thích háng không đặc hiệu; FAI không thể kết luận chỉ từ FADIR."),
        _spec("Đau quanh mấu chuyển lớn (GTPS) cần phân biệt",
              [("Đau mặt ngoài háng", ("dau mat ngoai khop hang", "dau mat ngoai dui", "dau vung mau chuyen")),
               ("Đau khi nằm nghiêng bên đau", ("nam nghieng ben dau", "dau khi nam nghieng"))],
              [], ["Ấn đau vùng mấu chuyển lớn", "Đánh giá dạng háng có kháng lực", "Phân biệt đau thắt lưng"],
              "Không đồng nhất mọi đau mặt ngoài háng với viêm bao hoạt dịch."),
        _spec("Đau quy chiếu từ cột sống thắt lưng",
              [("Đau lưng kèm lan/tê chi dưới", ("dau that lung", "lan xuong dui", "te chan"))],
              [], ["Khám thần kinh chi dưới", "Đánh giá ROM háng và cột sống"],
              "Cần khám đồng thời cột sống và khớp háng khi vùng đau chồng lấp."),
    ],
    "Khuỷu tay": [
        _spec("Đau gân duỗi cổ tay vùng lồi cầu ngoài",
              [("Đau mặt ngoài khuỷu khi nắm/duỗi cổ tay", ("dau loi cau ngoai", "dau mat ngoai khuyu", "dau khi nam chat", "dau khi duoi co tay")),
               ("Cozen hoặc Mill dương tính", ("Cozen", "Mill Test"))],
              [], ["Đau khu trú lồi cầu ngoài", "Sức nắm và tải chức năng", "Loại trừ đau quy chiếu từ cổ"],
              "Test kháng lực cần tái hiện đau quen thuộc; không suy ra mức độ rách gân."),
        _spec("Bệnh lý thần kinh trụ vùng khuỷu",
              [("Tê ngón IV-V hoặc bờ trụ bàn tay", ("te ngon ut", "te ngon ap ut", "te bo tru", "te ngon 4", "te ngon 5")),
               ("Tinel ống khuỷu dương tính", ("Tinel Sign ong khuyu", "Tinel ong khuyu"))],
              [], ["Khám cảm giác và sức cơ nội tại bàn tay", "Đánh giá triệu chứng theo tư thế gấp khuỷu"],
              "Tinel đơn độc không xác định vị trí hay mức độ tổn thương thần kinh."),
    ],
    "Cổ tay – bàn tay": [
        _spec("Hội chứng ống cổ tay cần đánh giá",
              [("Tê vùng ngón cái, trỏ, giữa", ("te ngon cai", "te ngon tro", "te ngon giua", "te 3 ngon")),
               ("Phalen hoặc Tinel cổ tay dương tính", ("Phalen", "Tinel Sign co tay", "Tinel co tay"))],
              [], ["Phân bố cảm giác và triệu chứng về đêm", "Sức cơ mô cái", "Phân biệt bệnh lý rễ cổ và thần kinh ngoại biên khác"],
              "Phalen/Tinel không đủ để xác nhận CTS nếu thiếu tương hợp triệu chứng."),
        _spec("Bệnh lý gân De Quervain cần phân biệt",
              [("Đau vùng mỏm trâm quay/ngón cái", ("dau co tay phia ngon cai", "dau mom tram quay", "dau goc ngon cai")),
               ("Finkelstein dương tính", ("Finkelstein",))],
              [], ["Đau khu trú khoang gân duỗi thứ nhất", "Phân biệt thoái hóa khớp nền ngón cái"],
              "Cần thực hiện nghiệm pháp đúng kỹ thuật và xác định vị trí đau tái hiện."),
    ],
    "Cổ chân – bàn chân": [
        _spec("Bong gân dây chằng bên cổ chân",
              [("Cơ chế lật trong bàn chân/chấn thương xoắn", ("lat trong ban chan", "lat co chan", "xoan co chan", "bong gan co chan")),
               ("Đau/sưng vùng ngoài cổ chân", ("dau mat ngoai co chan", "sung mat ngoai co chan")),
               ("Anterior Drawer hoặc Talar Tilt dương tính", ("Anterior Drawer Co chan", "Talar Tilt"))],
              [], ["Đánh giá khả năng chịu lực và điểm đau xương theo quy tắc Ottawa", "Mức độ sưng/bầm và độ vững", "Loại trừ gãy xương"],
              "Không dùng test dây chằng để bỏ qua chỉ định chụp khi có tiêu chuẩn nghi gãy."),
        _spec("Bệnh lý cân gan chân",
              [("Đau gót mặt gan, rõ khi bước những bước đầu", ("dau got chan", "dau long ban chan", "dau buoc chan dau tien", "dau buoi sang khi moi di"))],
              [], ["Điểm đau bám cân gan chân", "Khả năng chịu tải và yếu tố tăng tải", "Phân biệt nguyên nhân thần kinh hoặc gãy xương do stress"],
              "Đau gót có nhiều nguyên nhân; không mặc định là viêm cân gan chân."),
        _spec("Tổn thương gân Achilles cần loại trừ",
              [("Đau đột ngột vùng sau cổ chân/bắp chân", ("dau dot ngot gan got", "nghe tieng pop", "cam giac bi da vao got")),
               ("Thompson dương tính", ("Thompson Test", "Thompson"))],
              [], ["Khám liên tục gân và khả năng gấp gan chân", "Đánh giá y khoa/chẩn đoán hình ảnh khi nghi đứt"],
              "Nghi đứt gân Achilles cần đánh giá y khoa sớm; tránh tự thử tải mạnh."),
    ],
    "Thần kinh & Khác": [
        _spec("Hội chứng neuron vận động trung ương cần đánh giá",
              [("Yếu/liệt một bên hoặc rối loạn vận động", ("liet nua nguoi", "yeu nua nguoi", "yeu tay chan mot ben")),
               ("Dấu hiệu bó tháp/co cứng", ("Babinski", "co cung", "tang phan xa", "Modified Ashworth"))],
              [], ["Thời điểm khởi phát và diễn tiến", "Khám thần kinh đầy đủ", "Sàng lọc dấu hiệu đột quỵ cấp nếu khởi phát đột ngột"],
              "Yếu liệt khởi phát đột ngột là tình huống cấp cứu; không dùng tab này để trì hoãn xử trí."),
        _spec("Suy giảm thăng bằng/chức năng vận động cần lượng giá",
              [("Mất thăng bằng hoặc té ngã", ("mat thang bang", "te nga", "di khong vung", "choang vang")),
               ("Romberg hoặc đánh giá thăng bằng bất thường", ("Romberg", "thang bang kem"))],
              [], ["Đánh giá dáng đi, chuyển tư thế và nguy cơ té ngã", "Phân biệt tiền đình, cảm giác sâu, thị giác và nguyên nhân tim mạch/thần kinh"],
              "Cần xác định cơ chế mất thăng bằng trước khi lựa chọn bài tập."),
    ],
}


def _evaluate(spec: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    text = _all_text(data)
    tests = _positive_tests(data)
    test_text = " ".join(tests)
    support, contradict, missing = [], [], []

    for label, terms in spec["supports"]:
        if affirmed(text, *terms) or has(test_text, *terms):
            support.append(label)
        elif _explicitly_denies(text, terms):
            contradict.append("Phủ định được ghi nhận: " + label.lower())
        else:
            missing.append(label)

    for label, terms in spec["contradicts"]:
        if _explicitly_denies(text, terms) or affirmed(text, *terms):
            contradict.append(label)

    if support and contradict:
        status = "Có dữ kiện hai chiều – cần xác minh"
    elif support:
        status = "Có dữ kiện gợi ý – chưa xác định"
    elif contradict:
        status = "Ít tương hợp với dữ liệu hiện có"
    else:
        status = "Chưa đủ dữ liệu để đánh giá"

    return {
        "name": spec["label"], "status": status,
        "supporting": support, "opposing": list(dict.fromkeys(contradict)),
        "unverified_features": missing,
        "recommended_checks": spec["missing"],
        "caution": spec["caution"],
    }


def run_bidirectional_audit(data: Dict[str, Any], base_analysis: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Forward pattern generation + reverse expectation checking, automatically."""
    region = str(data.get("region", "Chưa xác định"))
    specs = CATALOGUE.get(region, [])
    candidates = [_evaluate(spec, data) for spec in specs]

    # Forward pass: retain patterns with at least one observed supporting feature.
    forward = [c for c in candidates if c["supporting"]]
    # Reverse pass: every candidate is checked against expected, contradictory,
    # and unverified findings. No missing feature is silently treated as absent.
    reverse = candidates

    contradictions: List[str] = []
    text = _all_text(data)
    radiation = str(data.get("radiation", "") or "")
    history = " ".join(str(data.get(k, "") or "") for k in ("reason", "history", "site", "associations"))
    if has(history, "lan xuong tay", "lan xuong chan", "te ngon tay", "te chan") and has(radiation, "khong lan", "khong te"):
        contradictions.append("Bệnh sử mô tả lan/tê nhưng trường Hướng lan lại ghi không lan/không tê.")

    # Test widget legacy wording conflates 'not performed' with 'negative'.
    test_states = data.get("tests") or {}
    unknown_tests = [name for name, value in test_states.items() if "duong tinh" not in norm(value)]
    if unknown_tests:
        contradictions.append(
            "Không thể đối soát âm tính thật vì giao diện hiện tại gộp 'Chưa làm' và 'Âm tính'. "
            "Các test sau được xem là CHƯA XÁC ĐỊNH, không dùng để loại trừ: " + ", ".join(unknown_tests)
        )

    red_flags = (base_analysis or {}).get("red_flags", [])
    if red_flags:
        overall = "ƯU TIÊN AN TOÀN – chưa đưa ra định hướng PHCN thường quy"
    elif contradictions:
        overall = "CẦN XÁC MINH – dữ liệu chưa nhất quán hoặc trạng thái test chưa rõ"
    elif forward:
        overall = "CÓ GIẢ THUYẾT ĐỂ ĐỐI CHIẾU – chưa phải chẩn đoán xác định"
    else:
        overall = "CHƯA ĐỦ DỮ LIỆU – chưa hình thành kiểu hình đủ tương hợp"

    return {
        "region": region,
        "overall": overall,
        "forward": forward,
        "reverse": reverse,
        "contradictions": contradictions,
        "unknown_tests": unknown_tests,
        "red_flags": red_flags,
        "base_hypotheses": (base_analysis or {}).get("hypotheses", []),
        "limitations": [
            "Đây là đối soát quy tắc theo từ khóa và mẫu lâm sàng, không phải mô hình đã được thẩm định trên quần thể bệnh nhân.",
            "Không tính xác suất hậu nghiệm, LR, độ nhạy hoặc độ đặc hiệu khi chưa có nguồn dữ liệu phù hợp.",
            "Không tìm thấy một dấu hiệu trong ghi chép không có nghĩa là dấu hiệu đó âm tính.",
            "Cần bác sĩ xác minh trực tiếp bệnh sử, kỹ thuật test, khám thần kinh/chức năng và cận lâm sàng khi có chỉ định.",
        ],
    }


def render_audit_report(result: Dict[str, Any]) -> str:
    def bullets(items):
        return "\n".join("- " + str(x) for x in items) if items else "- Chưa có dữ liệu ghi nhận."

    lines = [
        "PHCN AI 2.0 – ĐỐI SOÁT CHẨN ĐOÁN HAI CHIỀU TỰ ĐỘNG",
        f"Vùng khám: {result['region']}",
        f"Kết quả kiểm soát: {result['overall']}",
        "\nI. CHIỀU THUẬN – GIẢ THUYẾT CÓ DỮ KIỆN GỢI Ý",
    ]
    if result["forward"]:
        for item in result["forward"]:
            lines += [f"\n- {item['name']} ({item['status']})",
                      "  Dữ kiện gợi ý: " + ("; ".join(item["supporting"]) or "Chưa ghi nhận"),
                      "  Điểm chưa tương hợp: " + ("; ".join(item["opposing"]) or "Chưa ghi nhận rõ"),
                      "  Dấu hiệu kỳ vọng chưa có thông tin: " + ("; ".join(item["unverified_features"]) or "Không còn mục chưa xác minh trong nhóm dấu hiệu này"),
                      "  Khám/đánh giá bổ sung: " + ("; ".join(item["recommended_checks"]) or "Không có")]
    else:
        lines.append("- Chưa có giả thuyết nào có dữ kiện gợi ý đủ để đưa lên chiều thuận.")

    lines.append("\nII. CHIỀU NGƯỢC – KIỂM TRA LẠI TỪNG GIẢ THUYẾT")
    for item in result["reverse"]:
        lines.append(f"\n- {item['name']}: {item['status']}")
        lines.append("  Ủng hộ: " + ("; ".join(item["supporting"]) or "Chưa thấy dữ kiện trong ghi chép"))
        lines.append("  Chống lại: " + ("; ".join(item["opposing"]) or "Chưa ghi nhận dữ kiện chống lại rõ ràng"))
        lines.append("  Dấu hiệu kỳ vọng chưa có thông tin: " + ("; ".join(item["unverified_features"]) or "Không còn mục chưa xác minh trong nhóm dấu hiệu này"))
        lines.append("  Khám/đánh giá bổ sung: " + ("; ".join(item["recommended_checks"]) or "Không có"))
        lines.append("  Lưu ý: " + item["caution"])

    lines += ["\nIII. MÂU THUẪN / GIỚI HẠN DỮ LIỆU", bullets(result["contradictions"]),
              "\nIV. GIỚI HẠN VÀ AN TOÀN", bullets(result["limitations"]),
              "\nKết luận: Báo cáo chỉ hỗ trợ đối chiếu lâm sàng, không xác lập chẩn đoán và không thay thế khám trực tiếp."]
    return "\n".join(lines)
