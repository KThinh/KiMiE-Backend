"""Mô tả chi tiết + câu chuyện cho 13 sản phẩm mẫu, khoá theo tên sản phẩm.

Dùng ở 2 nơi:
  - create_db.py: seed database mới.
  - app.py (startup): điền vào database đang chạy cho các sản phẩm mẫu chưa có câu chuyện
    (story IS NULL) — không ghi đè nội dung người bán đã tự viết.

Đoạn văn phân cách bằng dòng trống; frontend hiển thị với white-space: pre-line."""

PRODUCT_CONTENT: dict[str, dict[str, str]] = {
    # ------------------------------------------------------------------ Bát Tràng
    "Bộ ấm trà men hỏa biến": {
        "description": (
            "Bộ ấm trà men hỏa biến xanh ngọc gồm ấm, chén, đĩa lót và khay hoa xanh — đủ cho một buổi trà "
            "sum vầy bên gia đình hay tiếp khách quý.\n\n"
            "Điều làm nên sự đặc biệt của bộ ấm nằm ở lớp men hỏa biến: men được pha từ tro, đá và khoáng "
            "chất, rồi \"giao phó\" cho ngọn lửa. Trong lò nung trên 1.200°C, men chảy, loang và kết tinh "
            "theo cách không ai sắp đặt trước được — chỗ đậm như mặt hồ sâu, chỗ nhạt như sương sớm, đôi chỗ "
            "ánh lên những đường vân như cánh chuồn chuồn. Vì vậy không có hai bộ ấm nào giống hệt nhau.\n\n"
            "Thân ấm dày dặn, giữ nhiệt tốt nên trà ngấm đều, hương thơm lâu. Vòi ấm được tạo dáng và thử "
            "rót nhiều lần để nước chảy gọn, ngắt dứt khoát, không rớt giọt ra khay. Nắp ấm khít, có lỗ "
            "thoát hơi nhỏ giúp rót êm tay.\n\n"
            "Phù hợp để pha trà xanh, trà sen, ô long hay trà thảo mộc; cũng là món quà tân gia, mừng thọ "
            "hay biếu đối tác mang đậm hồn Việt."
        ),
        "story": (
            "Ở xưởng Gốm Minh Long, người ta gọi mẻ men hỏa biến là \"mẻ của trời\". Ông Trần Văn Minh — "
            "người đã ba đời theo nghề gốm ở Bát Tràng — kể rằng thợ có thể pha men, chọn đất, canh lửa, "
            "nhưng khoảnh khắc men biến sắc thì chỉ có ngọn lửa quyết định.\n\n"
            "Có những đêm cả xưởng thức trắng bên lò. Lửa phải lên đều, không được vội; khi nhiệt chạm đỉnh, "
            "người thợ lắng nghe tiếng lò, nhìn màu lửa qua lỗ thăm để biết lúc nào nên dừng. Sáng hôm sau "
            "mở lò, cả nhà quây lại như chờ một đứa trẻ chào đời. Có mẻ men lên xanh ngọc trong veo, có mẻ "
            "loang tím, có mẻ hỏng cả — và họ chấp nhận điều đó như một phần của nghề.\n\n"
            "Bộ ấm bạn đang xem là một trong những chiếc \"được trời thương\". Mỗi vệt loang trên thân ấm là "
            "dấu vết duy nhất của đúng một đêm lửa, không thể làm lại lần thứ hai.\n\n"
            "Ông Minh hay nói: \"Chén trà ngon không chỉ nhờ trà, mà nhờ người ngồi cùng.\" Mong rằng bộ ấm "
            "này sẽ là cái cớ để những người thân yêu ngồi lại bên nhau lâu hơn một chút."
        ),
    },
    "Hũ đựng trà Mã Đáo Thành Công": {
        "description": (
            "Hũ đựng trà bằng sứ Bát Tràng, phủ men xanh sâu và vẽ vàng họa tiết \"Mã Đáo Thành Công\" — "
            "đàn ngựa phi nước đại, bờm tung trong gió.\n\n"
            "Lòng hũ tráng men kín, không hút ẩm, không ám mùi, giữ cho trà khô và thơm lâu. Nắp hũ được mài "
            "khớp với miệng, đậy vào là kín, hạn chế không khí và hơi ẩm lọt vào — điều mà người sành trà rất "
            "coi trọng.\n\n"
            "Nét vàng được vẽ hoàn toàn bằng tay rồi nung lần nữa ở nhiệt độ thấp để vàng bám chắc vào men, "
            "bền màu theo năm tháng. Dưới ánh đèn, những đường vàng ánh lên trên nền xanh thẫm, vừa sang "
            "trọng vừa cổ kính.\n\n"
            "Không chỉ để đựng trà, chiếc hũ còn thích hợp đựng hạt, mứt Tết, hoặc đặt trên kệ phòng khách, "
            "bàn làm việc như một vật phẩm phong thủy cầu may mắn."
        ),
        "story": (
            "\"Mã đáo thành công\" — ngựa về là thành công. Ngày xưa, khi người đi xa trở về trên lưng ngựa, "
            "đó là tin vui báo việc đã thành. Từ đó, hình ảnh đàn ngựa phi trở thành lời chúc cho mọi khởi "
            "đầu: làm ăn hanh thông, thi cử đỗ đạt, đường xa bình an.\n\n"
            "Để vẽ được đàn ngựa trên một mặt cong, người thợ không thể dùng khuôn in. Họ phải xoay hũ thật "
            "chậm, tay giữ bút vững, mỗi nét bờm, nét chân phải liền một hơi — run tay một chút là con ngựa "
            "mất đi khí thế. Một chiếc hũ có thể mất trọn một ngày chỉ riêng phần vẽ vàng.\n\n"
            "Ở Bát Tràng, nhiều gia đình vẫn giữ thói quen mua hũ trà mới vào dịp đầu năm, như gửi gắm một "
            "lời chúc cho cả năm sắp tới. Có người đặt hũ cho con trước kỳ thi, có người tặng bạn mở cửa "
            "hàng, có người biếu cha mẹ đựng trà mỗi sáng.\n\n"
            "Khi bạn mở nắp hũ, hương trà bay lên — và đàn ngựa vàng vẫn đang phi về phía trước, mang theo "
            "lời chúc của người thợ gốm gửi đến bạn."
        ),
    },
    "Đĩa trưng bày hoa sen ánh trăng": {
        "description": (
            "Đĩa trưng bày bằng gốm Bát Tràng, kết hợp kỹ thuật đắp nổi và vẽ màu thủ công, tái hiện cảnh hồ "
            "sen đêm rằm dưới ánh trăng.\n\n"
            "Từng cánh sen được đắp bằng tay từ đất mịn, nặn mỏng dần về phía mép để có độ cong tự nhiên như "
            "sen thật. Sau đó người nghệ nhân tô màu nhiều lớp — hồng phớt ở đầu cánh, trắng ngà ở gốc, lá "
            "sen xanh chuyển sắc — tạo chiều sâu khi nhìn nghiêng. Vầng trăng phía sau được để men trơn, "
            "ánh lên dịu nhẹ như ánh trăng thật.\n\n"
            "Đĩa đi kèm giá đỡ, có thể đặt trên kệ, tủ trưng bày, bàn thờ gia tiên hoặc treo tường. Phù hợp "
            "với không gian phòng khách, phòng trà, sảnh khách sạn hay văn phòng mang phong cách Á Đông.\n\n"
            "Đây là sản phẩm dùng để trưng bày; không dùng đựng thức ăn và không rửa bằng máy."
        ),
        "story": (
            "Người Việt yêu sen vì sen \"gần bùn mà chẳng hôi tanh mùi bùn\". Nhưng ở xưởng gốm, sen còn gắn "
            "với một kỷ niệm khác: những đêm hè, khi lò nghỉ, các thợ trẻ hay ra hồ đầu làng hóng mát. Trăng "
            "rằm soi xuống mặt nước, sen khép cánh, thoảng hương — và từ những đêm như thế, ý tưởng chiếc đĩa "
            "\"hoa sen ánh trăng\" ra đời.\n\n"
            "Kỹ thuật đắp nổi đòi hỏi sự kiên nhẫn hiếm có. Đất phải đủ dẻo để nặn, nhưng không được quá ướt "
            "kẻo cánh sen sụp khi phơi. Mỗi cánh đắp xong lại phải chờ se mặt mới đắp cánh tiếp theo. Khi vào "
            "lò, chỉ cần chênh lệch độ co giữa cánh sen và mặt đĩa là cả tác phẩm có thể nứt. Không ít chiếc "
            "đĩa đã phải bỏ đi ngay trước khi hoàn thành.\n\n"
            "Vì vậy, mỗi chiếc đĩa lành lặn ra khỏi lò được người thợ nâng niu như một bức tranh. Không có "
            "hai đóa sen nào giống nhau, bởi chúng được nặn bằng tay, vào những ngày khác nhau, với những tâm "
            "trạng khác nhau.\n\n"
            "Treo chiếc đĩa trong nhà, bạn đang giữ lại một đêm trăng hồ sen của làng gốm — tĩnh lặng, thanh "
            "khiết, và rất Việt Nam."
        ),
    },
    "Bình hút lộc Mã Đáo Thành Công": {
        "description": (
            "Bình hút lộc dáng tròn đầy, bụng phình, miệng thu nhỏ — kiểu dáng được dân gian ví như chiếc túi "
            "chứa lộc, \"vào nhiều ra ít\". Thân bình vẽ tay họa tiết \"Mã Đáo Thành Công\" trên nền men cao "
            "cấp, viền vàng tinh tế.\n\n"
            "Bình được tạo hình trên bàn xoay, phơi khô tự nhiên nhiều ngày trước khi tráng men và nung ở "
            "nhiệt độ cao, cho xương gốm chắc, gõ vào nghe tiếng thanh. Nét vẽ đàn ngựa được thực hiện hoàn "
            "toàn thủ công, có chiều sâu và sức sống mà hình in không thể có được.\n\n"
            "Theo quan niệm phong thủy, bình hút lộc nên đặt ở phòng khách, quầy thu ngân, bàn làm việc hoặc "
            "góc tài lộc của ngôi nhà, miệng bình hướng vào trong. Có thể để trống, cắm hoa hoặc bỏ vào vài "
            "đồng xu, hạt gạo như một nghi thức cầu may.\n\n"
            "Món quà ý nghĩa cho dịp khai trương, tân gia, thăng chức hay mừng năm mới."
        ),
        "story": (
            "Ở làng gốm, người ta tin rằng đồ vật cũng có \"vía\". Một chiếc bình được làm vào ngày đẹp, bởi "
            "người thợ đang vui, sẽ mang lại may mắn cho chủ nhân. Vì thế, những chiếc bình hút lộc ở xưởng "
            "Gốm Minh Long thường được bắt đầu vào những ngày đầu tháng âm lịch.\n\n"
            "Ông Minh kể, có lần một người khách quen đặt bình để mở quán ăn nhỏ. Năm đó quán đông khách, "
            "năm sau anh quay lại đặt thêm ba chiếc cho em trai và hai người bạn cùng khởi nghiệp. \"Tôi "
            "không dám nói bình làm ra tiền,\" ông cười, \"nhưng người ta có thêm niềm tin, mà có niềm tin "
            "thì làm gì cũng hăng hái hơn.\"\n\n"
            "Dáng bình được tạo trên bàn xoay chỉ trong vài phút, nhưng để có được dáng ấy, người thợ đã mất "
            "nhiều năm luyện tay. Phần bụng phải đầy mà không nặng nề, cổ phải thu mà không gượng ép — giống "
            "như một người no đủ mà vẫn khiêm nhường.\n\n"
            "Mong rằng chiếc bình sẽ mang đến cho bạn không chỉ tài lộc, mà cả sự an yên và niềm tin để bước "
            "tiếp trên con đường mình đã chọn."
        ),
    },
    "Bình sen vàng kim men xanh đồng": {
        "description": (
            "Bình cắm hoa dòng cao cấp, phủ men xanh đồng trầm ấm, đắp nổi hoa sen và điểm vàng kim — một "
            "trong những dòng sản phẩm đòi hỏi tay nghề cao nhất của xưởng.\n\n"
            "Men xanh đồng có sắc xanh rêu cổ, khi nung đúng lửa sẽ cho bề mặt mịn, ánh lên nhẹ nhàng như đồ "
            "đồng lâu năm. Trên nền men ấy, những đóa sen được đắp nổi bằng tay, sau đó dát vàng kim và nung "
            "thêm một lần để vàng bám chặt, bền màu, không bong tróc.\n\n"
            "Bình có thể cắm hoa tươi (sen, ly, lan, đào, mai…) hoặc để trơn làm vật trang trí. Đặt ở phòng "
            "khách, sảnh, bàn thờ, phòng trà, bình tạo điểm nhấn sang trọng mà vẫn trầm mặc, không phô "
            "trương.\n\n"
            "Mỗi chiếc bình đều được kiểm tra kỹ trước khi giao và đóng gói nhiều lớp chống sốc."
        ),
        "story": (
            "Sen là loài hoa gắn với người Việt từ đình chùa đến mái nhà. Khi xưởng quyết định làm dòng bình "
            "cao cấp nhất của mình, không ai phân vân: phải là hoa sen.\n\n"
            "Nhưng để sen hiện lên đẹp trên nền men xanh đồng là cả một hành trình thử nghiệm. Những mẻ đầu, "
            "men quá tối khiến sen chìm hẳn; có mẻ vàng bị loang, có mẻ cánh sen nứt chân. Người thợ phải "
            "điều chỉnh tỉ lệ men, độ dày lớp đắp, nhiệt độ từng lần nung — gần một năm mới có được chiếc "
            "bình đầu tiên khiến cả xưởng hài lòng.\n\n"
            "Một chiếc bình hoàn chỉnh đi qua ba lần lửa: lửa nung xương, lửa nung men và lửa nung vàng. Mỗi "
            "lần vào lò là một lần đánh cược. Vì vậy số lượng mỗi năm rất ít, và mỗi chiếc đều được đánh số "
            "riêng trong sổ của xưởng.\n\n"
            "Khi cắm một cành sen thật vào chiếc bình sen bằng gốm, hai đóa sen — một của đất trời, một của "
            "đôi bàn tay người thợ — đứng cạnh nhau. Đó là khoảnh khắc mà người làm gốm mong bạn sẽ được "
            "ngắm."
        ),
    },
    "Đĩa sứ bầu dục men lam": {
        "description": (
            "Đĩa sứ dáng bầu dục, vẽ men lam cổ điển trên nền trắng ngà — dòng men đã gắn bó với gốm Bát "
            "Tràng qua nhiều thế kỷ.\n\n"
            "Họa tiết được vẽ tay bằng bút lông với men lam (có thành phần cô-ban) trước khi phủ men trong và "
            "nung ở nhiệt độ cao. Nhờ vậy, nét vẽ nằm dưới lớp men, không phai, không trầy xước khi sử dụng "
            "hằng ngày. Sắc lam đậm nhạt khác nhau theo từng nét bút, tạo cảm giác mềm mại, có hồn.\n\n"
            "Dáng bầu dục rộng, lòng nông, rất hợp để bày cá hấp, gà luộc, xôi, bánh hoặc đĩa trái cây ngày "
            "Tết. Khi không dùng, đặt đĩa lên giá cũng là một vật trang trí trang nhã cho tủ bếp hay phòng "
            "ăn.\n\n"
            "An toàn khi đựng thực phẩm, dùng được trong lò vi sóng và máy rửa bát (nên rửa tay để giữ đĩa "
            "đẹp lâu hơn)."
        ),
        "story": (
            "Nếu hỏi một người lớn tuổi ở miền Bắc về chiếc đĩa men lam, nhiều người sẽ nhớ ngay đến mâm cỗ "
            "ngày Tết của bà, của mẹ: đĩa gà luộc vàng ươm, đĩa giò, đĩa xôi gấc đỏ — tất cả nằm trên những "
            "chiếc đĩa trắng viền lam quen thuộc.\n\n"
            "Men lam là \"tiếng nói\" lâu đời của gốm Bát Tràng. Người thợ vẽ lam phải có tay rất vững, vì men "
            "thấm vào cốt gốm ngay khi chạm bút, không thể tẩy xóa. Một nét hỏng là phải làm lại cả chiếc "
            "đĩa. Các thợ trẻ thường tập vẽ hàng trăm chiếc lá, cánh hoa trên giấy trước khi được cầm bút vẽ "
            "lên gốm.\n\n"
            "Chiếc đĩa bầu dục này được làm theo dáng đĩa cũ mà xưởng vẫn giữ lại từ thời ông nội của ông Minh "
            "— dáng đĩa từng dùng trong những bữa cỗ làng. Chỉ có kích thước và lớp men là được điều chỉnh "
            "cho hợp với gian bếp hôm nay.\n\n"
            "Dọn một món ăn lên chiếc đĩa men lam, bạn đang tiếp nối một thói quen đẹp của bao thế hệ gia "
            "đình Việt: bữa cơm không chỉ để no, mà để sum họp."
        ),
    },
    # ------------------------------------------------------------------ Vạn Phúc
    "Cà vạt lụa tơ tằm": {
        "description": (
            "Cà vạt dệt từ 100% lụa tơ tằm Vạn Phúc, sắc đỏ đô sang trọng với hoa văn chìm chỉ hiện rõ khi "
            "ánh sáng chiếu nghiêng.\n\n"
            "Lụa tơ tằm có độ bóng tự nhiên, mềm và rủ, thắt nút gọn, không bị nhăn gãy như cà vạt sợi tổng "
            "hợp. Sợi tơ thoáng khí, mát khi trời nóng, ấm khi trời lạnh — đeo cả ngày vẫn dễ chịu. Lớp lót "
            "bên trong giúp cà vạt giữ form, buông thẳng đẹp.\n\n"
            "Hoa văn chìm được dệt trực tiếp trên khung, không in, không thêu, nên bền theo thời gian và mang "
            "vẻ đẹp kín đáo, lịch lãm. Phù hợp với vest công sở, lễ cưới, hội nghị, các dịp trang trọng.\n\n"
            "Kèm hộp quà — món quà ý nghĩa cho cha, chồng, người yêu, đồng nghiệp hay đối tác nước ngoài muốn "
            "mang về một chút tinh hoa Việt."
        ),
        "story": (
            "Làng Vạn Phúc bên bờ sông Nhuệ đã dệt lụa từ hơn một nghìn năm trước. Tiếng khung cửi lách cách "
            "từng là âm thanh quen thuộc của cả làng, và lụa Vạn Phúc từng được chọn để may trang phục cho "
            "triều đình.\n\n"
            "Bà Nguyễn Thị Hoa, chủ xưởng Lụa Hoa, kể rằng cà vạt là sản phẩm bà \"nghĩ mãi mới dám làm\". "
            "Lụa truyền thống vốn dành cho áo dài, khăn choàng — mềm mại, nữ tính. Để dệt ra một tấm lụa đủ "
            "đanh cho cà vạt mà vẫn giữ được độ mềm của tơ tằm, xưởng phải thử nhiều cách xe sợi, mật độ dệt "
            "khác nhau.\n\n"
            "Chiếc cà vạt đầu tiên bà làm tặng chồng trong ngày cưới con gái. Hôm ấy, nhiều khách hỏi mua, và "
            "từ đó cà vạt lụa trở thành một dòng sản phẩm riêng của xưởng.\n\n"
            "Mỗi lần thắt chiếc cà vạt này, bạn mang theo một chút của làng lụa nghìn năm — không ồn ào, chỉ "
            "lặng lẽ ánh lên khi gặp ánh sáng, như chính phong cách của người Vạn Phúc."
        ),
    },
    "Khăn lụa vân sen hồng": {
        "description": (
            "Khăn lụa tơ tằm dệt vân sen, phối sắc hồng nhẹ nhàng. Hoa văn sen được dệt chìm trong mặt lụa, "
            "ẩn hiện khi khăn chuyển động hoặc khi soi dưới nắng.\n\n"
            "Chất lụa mỏng, nhẹ, rủ mềm theo dáng vai, có thể quàng cổ, choàng vai, buộc tóc, thắt túi xách "
            "hoặc làm điểm nhấn cho áo dài. Lụa tơ tằm thấm hút tốt, mát vào mùa hè và giữ ấm nhẹ khi trời "
            "se lạnh.\n\n"
            "Khăn được dệt thủ công trên khung tại Vạn Phúc, nhuộm màu kỹ lưỡng để sắc hồng lên đều và giữ "
            "được độ tươi lâu. Mép khăn được viền tay tỉ mỉ.\n\n"
            "Có nhiều màu để lựa chọn: hồng phấn, xanh ngọc, vàng nhạt. Kèm hộp quà sang trọng."
        ),
        "story": (
            "Vân sen là một trong những hoa văn được người Vạn Phúc dệt từ rất lâu. Điều kỳ diệu của lụa vân "
            "là hoa văn không nằm trên bề mặt, mà nằm \"bên trong\" tấm lụa — chỉ hiện ra khi có ánh sáng, "
            "giống như vẻ đẹp kín đáo của người phụ nữ Á Đông.\n\n"
            "Để dệt được hoa văn ấy, người thợ phải chuẩn bị bìa hoa văn rất công phu, tính toán từng sợi tơ "
            "nổi, sợi tơ chìm. Chỉ cần lệch một sợi là đóa sen sẽ méo. Khi khung cửi chạy, người thợ phải "
            "luôn để mắt đến từng đường go, nối lại ngay khi sợi tơ đứt.\n\n"
            "Bà Hoa nhớ mẹ bà luôn có một chiếc khăn lụa vân trong tủ, chỉ mang ra vào những ngày đặc biệt: "
            "Tết, đám cưới con, buổi họp lớp sau ba mươi năm. Chiếc khăn ấy giờ đã ngả màu, nhưng bà vẫn giữ "
            "như một kỷ vật.\n\n"
            "Mong rằng chiếc khăn vân sen hồng này cũng sẽ theo bạn qua những ngày đáng nhớ, và một ngày nào "
            "đó trở thành kỷ vật được trao lại cho người thương."
        ),
    },
    "Khăn tơ ngũ sắc xanh cam": {
        "description": (
            "Khăn tơ tằm phối ngũ sắc với gam chủ đạo xanh — cam rực rỡ, dệt thủ công tại làng Vạn Phúc.\n\n"
            "Các dải màu được nhuộm và phối khéo léo để chuyển sắc mềm mại, không gắt. Khi quàng lên, khăn "
            "tạo điểm nhấn tươi sáng cho trang phục trơn màu, áo sơ mi, váy liền hay áo dài cách tân.\n\n"
            "Sợi tơ có độ bóng tự nhiên, mềm, nhẹ và thoáng — thích hợp dùng cả bốn mùa. Có thể quàng cổ, "
            "choàng vai, làm khăn đội đầu hoặc buộc quai túi.\n\n"
            "Hiện có hai phối màu: Xanh - Cam và Hồng - Tím. Nên giặt tay nhẹ nhàng bằng nước lạnh, phơi nơi "
            "thoáng mát, tránh nắng gắt."
        ),
        "story": (
            "Ngũ sắc — năm màu — là quan niệm lâu đời của người Á Đông về sự hài hòa giữa trời đất và con "
            "người. Năm màu đứng cạnh nhau, không màu nào lấn át màu nào, như một gia đình đông vui mà "
            "vẫn êm ấm.\n\n"
            "Chiếc khăn này ra đời từ một mùa hè ở Vạn Phúc. Những người thợ trẻ trong xưởng Lụa Hoa muốn "
            "làm một sản phẩm thật tươi, thật trẻ để những bạn gái thành phố cũng thích đeo lụa mỗi ngày, "
            "chứ không chỉ để dành cho dịp lễ. Họ chọn sắc xanh của lá dâu và sắc cam của buổi chiều trên "
            "sông Nhuệ làm hai màu chủ đạo.\n\n"
            "Để phối màu, tơ được nhuộm riêng từng phần, sau đó người thợ phải căn chỉnh rất kỹ trên khung "
            "dệt để các dải màu chuyển tiếp đều đặn. Những tấm đầu tiên bị loang, bị lệch, và phải mất "
            "nhiều tuần mới ra được tấm khăn ưng ý.\n\n"
            "Bà Hoa nói vui: \"Lụa nghìn năm tuổi rồi, nhưng không có nghĩa là lụa phải già.\" Chiếc khăn "
            "ngũ sắc là cách làng nghề cổ trò chuyện với thế hệ hôm nay."
        ),
    },
    "Áo dài lụa tơ tằm Hà Đông": {
        "description": (
            "Áo dài may từ lụa tơ tằm Hà Đông nguyên tấm, dệt hoa văn cẩm giao trang nhã — họa tiết hình học "
            "đan xen, tượng trưng cho sự gắn kết bền lâu.\n\n"
            "Lụa nguyên tấm cho thân áo mềm, rủ, ôm nhẹ theo dáng người mà vẫn thoáng mát. Bề mặt lụa có độ "
            "bóng dịu, khi bước đi tà áo bay nhẹ, hoa văn ẩn hiện theo từng chuyển động.\n\n"
            "Áo được cắt may tỉ mỉ bởi thợ may áo dài lâu năm: đường ráp vai, nách và eo được xử lý khéo để "
            "áo vào form đẹp. Phù hợp mặc dịp Tết, lễ cưới, lễ tốt nghiệp, chụp ảnh, sự kiện văn hóa hoặc làm "
            "đồng phục lễ tân cao cấp.\n\n"
            "Màu sắc: đỏ đô, xanh ngọc, vàng đồng. Size S, M, L, XL — vui lòng xem hướng dẫn chọn size theo "
            "số đo vòng ngực. Giặt tay nhẹ, là ở nhiệt độ thấp mặt trái vải."
        ),
        "story": (
            "\"The Hà Đông\" từng là niềm tự hào của bao thế hệ phụ nữ Hà Nội. Tấm lụa ấy được dệt ở làng "
            "Vạn Phúc, nơi nghề tằm tơ đã có từ hơn một nghìn năm.\n\n"
            "Hoa văn cẩm giao trên chiếc áo này là những hình học nhỏ đan cài vào nhau không dứt. Các cụ "
            "trong làng bảo đó là hình ảnh của tình nghĩa: sợi này giữ sợi kia, người này nương người kia, "
            "đan vào nhau mới thành tấm lụa bền. Vì thế, lụa cẩm giao thường được chọn may áo cưới, áo mừng "
            "thọ, áo cho những ngày quan trọng nhất đời người.\n\n"
            "Từ lúc ươm tơ, dệt lụa đến khi thành một chiếc áo dài là nhiều tuần làm việc của nhiều đôi bàn "
            "tay. Bà Hoa thường dặn thợ may: \"Đường kéo phải đi một lần cho dứt khoát, lụa tốt không chịu "
            "được mũi kim vụng.\"\n\n"
            "Khi khoác lên mình tà áo dài lụa Hà Đông, bạn không chỉ mặc một bộ trang phục đẹp — bạn đang "
            "khoác lên cả một dòng chảy văn hóa, nơi sự dịu dàng và bền bỉ của người phụ nữ Việt được dệt "
            "vào từng sợi tơ."
        ),
    },
    # ------------------------------------------------------------------ Phú Vinh
    "Hộp đựng đồ mây tre đan": {
        "description": (
            "Hộp đựng đồ đan tay từ mây tre Phú Vinh theo kỹ thuật nong đôi — hai lớp nan đan chồng khít, "
            "giúp hộp chắc chắn, giữ form lâu mà vẫn nhẹ.\n\n"
            "Nguyên liệu mây, tre được chọn lọc, luộc, phơi và xử lý chống mối mọt, ẩm mốc trước khi đan. Nan "
            "được chẻ đều, vót nhẵn để bề mặt mịn tay, không xước. Nắp hộp đậy khít, có thể dùng đựng trang "
            "sức, đồ may vá, mỹ phẩm, giấy tờ, đồ chơi trẻ em hay bánh kẹo.\n\n"
            "Có 3 cỡ: Nhỏ (15cm), Vừa (20cm), Lớn (25cm) — đo theo đường kính đáy hộp. Có thể chọn cả bộ để "
            "xếp lồng vào nhau, gọn gàng mà đẹp mắt.\n\n"
            "Màu mây tự nhiên, ấm áp, hợp với phong cách tối giản, Bắc Âu hay Đông Dương. Lau bằng khăn ẩm, "
            "để nơi khô thoáng."
        ),
        "story": (
            "Ở Phú Vinh, trẻ con lớn lên giữa những bó mây, bó giang phơi đầy sân. Ông Lê Văn Phú — chủ xưởng "
            "Mây Tre Phú An — kể rằng ông học đan từ năm lên tám, bắt đầu bằng việc ngồi chẻ nan cho bà. \"Nan "
            "chẻ chưa đều thì chưa được ngồi đan,\" ông nhớ lại lời bà dặn.\n\n"
            "Kỹ thuật nong đôi là \"vốn liếng\" của làng: hai lớp nan đan chồng lên nhau, lớp trong đỡ lớp "
            "ngoài, nên đồ đan Phú Vinh nổi tiếng bền. Ngày trước, người ta dùng hộp, rương mây để đựng quần "
            "áo, giấy tờ quý — có những chiếc theo một gia đình qua cả hai, ba thế hệ.\n\n"
            "Một chiếc hộp nhỏ như thế này mất khoảng một ngày công đan, chưa kể thời gian chọn mây, luộc, "
            "phơi, xử lý chống mối mọt. Mỗi đường nan đều do tay người thợ siết, nên độ căng đều đặn của nó "
            "là dấu hiệu của cả nhiều năm luyện nghề.\n\n"
            "Mong rằng chiếc hộp sẽ giữ giúp bạn những món đồ nhỏ thân thương — và một ngày nào đó, chính nó "
            "cũng trở thành một món đồ thân thương trong nhà."
        ),
    },
    "Túi đeo chéo mây tre đan": {
        "description": (
            "Túi đeo chéo đan tay từ mây tự nhiên, quai mây uốn tròn, thân túi đan hoa văn xương cá — kiểu đan "
            "đặc trưng của làng nghề Phú Vinh.\n\n"
            "Túi được phối da ở dây đeo và khóa cài, tạo vẻ hiện đại mà vẫn giữ hồn mộc mạc của mây tre. Lòng "
            "túi có lót vải, đủ chỗ cho điện thoại, ví, son, kính mát và vài vật dụng nhỏ.\n\n"
            "Hoa văn xương cá tạo nên những đường chéo song song nhịp nhàng, vừa đẹp mắt vừa giúp thân túi "
            "cứng cáp, không bị bẹp méo. Túi nhẹ, hợp đi biển, đi phố, dã ngoại, cà phê cuối tuần hay chụp "
            "ảnh.\n\n"
            "Hai màu: mây tự nhiên và mây nhuộm nâu. Tránh để túi ngâm nước lâu; nếu bị ướt, lau khô và hong "
            "nơi thoáng gió."
        ),
        "story": (
            "Hoa văn xương cá ở Phú Vinh được truyền lại qua nhiều thế hệ. Những đường nan chéo nhau, nối "
            "tiếp không dứt, gợi nhớ đến những con cá trong ao làng — thứ đã nuôi sống bao gia đình nông "
            "thôn.\n\n"
            "Chiếc túi đeo chéo ra đời khi con gái ông Phú lên Hà Nội học đại học. Cô muốn mang một thứ gì "
            "đó của quê theo mình, nhưng phải đủ \"xinh\" để đeo đi học, đi chơi cùng bạn bè. Thế là hai cha "
            "con ngồi bàn: giữ hoa văn xương cá của ông bà, thêm quai mây tròn và dây da cho trẻ trung.\n\n"
            "Chiếc túi đầu tiên được bạn bè cô hỏi mua liên tục. Từ đó, xưởng bắt đầu làm túi để bán, và "
            "nhiều phụ nữ trong làng có thêm việc làm mỗi khi nông nhàn.\n\n"
            "Mỗi chiếc túi là một nhịp cầu nhỏ giữa làng quê và phố thị, giữa đôi tay của người cha và "
            "bước chân của người con. Đeo nó lên vai, bạn mang theo một chút gió đồng Phú Vinh đi khắp nơi."
        ),
    },
    "Túi đan ruột mây hình chữ nhật": {
        "description": (
            "Túi dáng hộp chữ nhật đan từ ruột mây Phú Vinh — phần lõi mềm, dẻo bên trong sợi mây, cho nan "
            "mảnh, đều tăm tắp và bề mặt mịn màng.\n\n"
            "Nhờ nan ruột mây nhỏ, túi có những đường đan dày, khít, tạo nên kết cấu tinh tế như vải dệt. Dáng "
            "hộp vuông vức, đứng form, phù hợp phong cách thanh lịch, cổ điển. Quai cầm chắc tay, có thể xách "
            "tay hoặc kẹp nách.\n\n"
            "Lòng túi đủ rộng cho ví, điện thoại, sổ tay nhỏ và đồ trang điểm. Thích hợp đi tiệc, đi làm, dạo "
            "phố, du lịch, hoặc phối cùng áo dài và trang phục truyền thống.\n\n"
            "Ruột mây đã được xử lý chống ẩm mốc, mối mọt. Bảo quản nơi khô ráo, nhồi giấy vào lòng túi khi "
            "không dùng để giữ form."
        ),
        "story": (
            "Trong một sợi mây, phần vỏ cứng thường được dùng để đan đồ cần độ chắc, còn phần ruột mềm bên "
            "trong lại dành cho những sản phẩm cần sự tinh tế. Người thợ Phú Vinh gọi đan ruột mây là việc "
            "của \"tay kim\" — phải nhẫn nại như người khâu vá.\n\n"
            "Ruột mây được chuốt qua lỗ sắt để nan tròn và đều, sau đó phơi khô, tẩy và xử lý kỹ. Khi đan, "
            "người thợ phải giữ lực siết đều trên từng hàng nan, chỉ cần một hàng lỏng là cả mặt túi sẽ lệch. "
            "Một chiếc túi có thể mất vài ngày mới hoàn thành.\n\n"
            "Ông Phú kể, những người đan ruột mây giỏi nhất trong xưởng đều là các bà, các mẹ đã ngoài năm "
            "mươi tuổi. Họ vừa đan vừa trò chuyện, kể chuyện con cháu, chuyện mùa màng — và có lẽ những câu "
            "chuyện ấy cũng được đan vào từng hàng nan.\n\n"
            "Cầm chiếc túi trên tay, bạn sẽ cảm nhận được sự mịn màng của những sợi mây đã qua hàng nghìn lần "
            "chạm tay — một vẻ đẹp chậm rãi, bền bỉ giữa nhịp sống vội vàng."
        ),
    },
}
