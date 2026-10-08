from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont('DV','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DVB','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily('DV',normal='DV',bold='DVB',italic='DV',boldItalic='DVB')
N=ParagraphStyle('n',fontName='DV',fontSize=9.2,leading=12.6,spaceAfter=4)
S=ParagraphStyle('s',parent=N,fontSize=8,leading=10.4,spaceAfter=0)
H1=ParagraphStyle('h1',fontName='DVB',fontSize=15,leading=19,textColor=colors.HexColor('#1F3864'),spaceAfter=4)
H2=ParagraphStyle('h2',fontName='DVB',fontSize=11,leading=14,textColor=colors.HexColor('#2E5597'),spaceBefore=8,spaceAfter=4)
B=ParagraphStyle('b',parent=N,leftIndent=10,bulletIndent=0)
def tbl(rows,widths):
  data=[[Paragraph(str(x),ParagraphStyle('hh',parent=S,fontName='DVB',textColor=colors.white) if i==0 else S) for x in r] for i,r in enumerate(rows)]
  t=Table(data,colWidths=[w*mm for w in widths],repeatRows=1)
  t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1F3864')),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#BFBFBF')),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F2F5FA')])]))
  return t
st=[]
st.append(Paragraph('Executive Recommendation',H1))
st.append(Paragraph('<b>Кому:</b> управляющему партнёру LEGITIMUS · <b>От:</b> Агент 02 (Partnership Intelligence Analyst) · <b>Дата:</b> 8 октября 2026 г.',N))
st.append(Paragraph('<b>Тема:</b> международные провайдеры корпоративных услуг, с которыми стоит начать переговоры о регистрации и юридическом сопровождении компаний в Молдове',N))
st.append(Paragraph('Главный вывод',H2))
st.append(Paragraph('Из 20 провайдеров в базе агента 01 реальную модель сотрудничества с LEGITIMUS удалось обосновать для 10. Пять из них рекомендую в первую очередь. Три уже продают регистрацию в Молдове, но собственного офиса в Кишинёве у них не найдено: <b>Accace, BridgeWest, Healy Consultants</b>. Значит, им, вероятно, нужен местный исполнитель (это допущение). Ещё две работают в соседних странах или официально принимают внешние рекомендации: <b>Eurofast, Commitbiz</b>. Сайты компаний из среды исследования открыть не удалось, поэтому выводы опираются на поисковую выдачу, в основном по официальным доменам. Перед первым контактом ключевые факты нужно сверить на сайтах.',N))
st.append(Paragraph('Первая очередь: к кому обращаться',H2))
rows=[['Компания / балл','Почему','К кому и через какой канал','Что предложить и первый шаг'],
['<b>Accace</b> (Словакия)<br/>82/100','Продаёт услуги в Молдове (есть отдельная страница), офиса в Кишинёве не найдено. Рынки без своих филиалов покрываются через сеть Accace Circle. Клиенты на постоянном аутсорсинге дают повторяющуюся юридическую работу.','Alžbeta Košinár, Business Development & Community Lead, Accace Circle (Medium); CEO Mihaela Pašek-Virlan (Medium). Канал: circle.accace.com. Общий email не подтверждён.','Роль юридического партнёра по Молдове внутри Circle. Первый шаг: письменно выяснить, кто сейчас оказывает услуги в Молдове и есть ли место для юридического партнёра.'],
['<b>Eurofast</b> (Кипр)<br/>76/100','Группа в Юго-Восточной и Центральной Европе: 24 офиса в 20 странах, в том числе Бухарест и Киев. Молдова не найдена. Активна: новый MD в 2025 г., вакансии 2026 г. (агент 01 ошибочно считал её неактивной).','Antonis Gavrielides и Irena Damianou, Managing Directors (Medium). Канал: info@eurofast.eu (найден только в стороннем источнике, нужно сверить).','Местный корреспондент или юрист по Молдове для клиентов из Румынии и Украины. Спросить, приходят ли запросы по Молдове. Возражение: группа может открыть собственный офис.'],
['<b>BridgeWest</b><br/>75/100','Продаёт регистрацию в Молдове и работает через сеть независимых юрфирм (на сайте есть страница «Partner Law Firms»). Кто партнёр в Молдове, не установлено.','office@bridgewest.eu; раздел «Join Our Network». Co-founder Vlad Cuc (Low, только заголовок LinkedIn). Штаб-квартира неясна: Кипр или Мальта.','Статус партнёра сети по Молдове. Первый шаг: узнать, свободно ли это место. Риск: акцент на готовых компаниях и офшорах, нужна оценка по AML.'],
['<b>Healy Consultants</b> (Hawksford)<br/>74/100','Есть страницы по Молдове; на сайте отзывы партнёрских юрфирм. Входит в группу Hawksford: долгосрочные corporate services.','healy@hawksford.com; SG +65 6031 0332. Группа: Michel van Leeuwen, Group CEO Hawksford (Medium, данные 2023 г.).','White-label исполнение в Молдове. Возражения: вероятно, местный исполнитель уже есть; фиксированные цены сжимают маржу субподрядчика; требования Hawksford к проверке поставщиков (KYC).'],
['<b>Commitbiz</b> (ОАЭ)<br/>70/100','Опубликовано двустороннее реферальное соглашение. Есть офис в Бухаресте и клиенты из Восточной Европы и СНГ.','Manu Thomas V, Managing Director (Medium, пресс-релиз авг. 2025). Канал: info@commitbiz.com, /contact-us.','Взаимные рекомендации: Молдова ↔ ОАЭ/GCC. ВАЖНО: опубликованная ставка 20% — это их условие, не наше. Нужно проверить, допускает ли этика адвокатов Молдовы раздел гонорара. Офис в Москве требует KYC.']]
st.append(tbl(rows,[30,47,47,52]))
st.append(Paragraph('Вторая очередь',H2))
for t in ['<b>The Sovereign Group</b> (69): предлагает профессиональным фирмам white-label (агент 01 ошибочно считал, что программы нет). Контакты: Sebastien Philipona, Head of BD Malta &amp; Cyprus; Nicholas Cully, Group Sales Director. Молдова и CEE не найдены.',
'<b>TMF Group</b> (67): в 2025 г. начал сотрудничать с LAWorld, сетью независимых юрфирм; есть офис в Румынии. Вход через Gabriel Sincu, Country Manager Romania (данные ноя. 2024 г.). Строгий отбор поставщиков.',
'<b>Uniwide</b> (60): партнёрская программа для юрфирм, найденная агентом 01, при повторной проверке не подтвердилась. Сначала проверить её. Оценка агента 01 (81) завышена.',
'<b>Vistra</b> (59): офис в Бухаресте подтверждён, CEO Kim Jenkins (с июля 2025 г.). Корпоративные закупки, низкая доступность ЛПР.',
'<b>Virtuzone</b> (59): двусторонние рекомендации ОАЭ ↔ Молдова. С 2025 г. входит в Ascentium; партнёрства, вероятно, решаются централизованно. Оценка агента 01 (82) завышена.']:
  st.append(Paragraph(t,B,bulletText='•'))
st.append(Paragraph('Отложено и исключено',H2))
st.append(Paragraph('<b>GSL</b> (65): <b>отложено</b>. Штаб-квартира в Москве, российская клиентура, материалы о переводе бизнеса «под санкциями». Поиск по спискам OFAC, ЕС и OpenSanctions совпадений не дал, но это не формальная проверка. До любого контакта нужны формальный санкционный и PEP-скрининг и решение партнёра. <b>Исключены (7):</b> Shuraa, Sleek, InCorp Global, Avyanco, Creation BC, IQ-EQ (нет понятной взаимовыгодной модели или работают только в своём регионе) и SFM (не удалось подтвердить, что компания действует). <b>Резерв:</b> Riz &amp; Mona, Tetra Consultants (в основном разовые регистрации).',N))
st.append(Paragraph('Качество данных агента 01',H2))
st.append(Paragraph('Проверено 150 утверждений: 76 подтверждены, 6 ошибочны, 7 устарели, 17 не подтверждены, 41 требует дополнительной проверки, 3 дубликата. Главные поправки: Eurofast активна; у Sovereign есть white-label; у Vistra подтверждён офис в Румынии; по TMF и Avyanco вместо «Молдовы нет» правильно «не найдено»; у BridgeWest найден адрес на Мальте. Агент 01 завысил оценки компаний из ОАЭ и Uniwide, но балл Eurofast у него совпал (76); при этом агент 01 сомневался, что компания активна.',N))
st.append(Paragraph('Препятствия, которые стоит ожидать',H2))
for t in ['У провайдеров, уже продающих Молдову, вероятно, есть действующий местный исполнитель. LEGITIMUS придётся предложить лучшее качество, скорость или языки, либо роль резервного исполнителя.',
 'Объём заказов по Молдове, скорее всего, небольшой. Ценность партнёрства в долгосрочном сопровождении, а не в разовых регистрациях.',
 'Крупные группы (Hawksford, TMF, Vistra) требуют проверки поставщика: KYC, страхование ответственности, договоры об уровне сервиса (SLA).',
 'Реферальные вознаграждения нужно проверить на соответствие правилам адвокатской этики Молдовы до обсуждения условий.',
 'Провайдеры с офшорной направленностью означают повышенную нагрузку по AML для бюро.']:
  st.append(Paragraph(t,B,bulletText='•'))
st.append(Paragraph('Рекомендуемые шаги',H2))
for i,t in enumerate(['Сверить ключевые факты по пяти компаниям первой очереди на их сайтах. Для этого нужно открыть доступ к сайтам в сетевых настройках среды.',
 'Подготовить одностраничное описание возможностей LEGITIMUS на английском (услуги, языки, сроки, подход к KYC). Без него первый контакт слабый.',
 'Получить заключение о допустимости реферальных вознаграждений и раздела гонорара.',
 'Обновить письма. Черновики агента 01 написаны для Accace, BridgeWest, Commitbiz, Virtuzone и Uniwide. Для новой первой очереди нужны письма Eurofast и Healy, а письмо Accace лучше адресовать Alžbeta Košinár.',
 'GSL: формальный санкционный скрининг, затем решение партнёра.'],1):
  st.append(Paragraph(f'{i}. {t}',B))
st.append(Spacer(1,6))
st.append(Paragraph('<i>Никаких контактов с компаниями не было. Интерес компаний к партнёрству — оценка аналитика, а не подтверждённый факт. Подробности в файлах Verified Partners Database.xlsx и TOP-10 Partnership Dossiers.docx.</i>',S))
def foot(c,d):
  c.setFont('DV',7.5);c.drawRightString(A4[0]-15*mm,10*mm,f'LEGITIMUS · Executive Recommendation · стр. {d.page}')
SimpleDocTemplate('/home/user/-/research/agent02/Executive Recommendation.pdf',pagesize=A4,leftMargin=15*mm,rightMargin=15*mm,topMargin=14*mm,bottomMargin=16*mm,title='Executive Recommendation',author='Agent 02').build(st,onFirstPage=foot,onLaterPages=foot)
