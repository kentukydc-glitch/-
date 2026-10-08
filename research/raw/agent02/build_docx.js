const fs=require('fs');
const {Document,Packer,Paragraph,TextRun,HeadingLevel,Table,TableRow,TableCell,WidthType,ShadingType,LevelFormat,PageBreak,AlignmentType,Footer,PageNumber,ExternalHyperlink,BorderStyle}=require('docx');
const A=JSON.parse(fs.readFileSync('final.json')).filter(c=>c.status.startsWith('TOP-10'));
const K=[['profile_fit','Соответствие профилю LEGITIMUS',20],['recurring_client_potential','Потенциал клиентов на постоянное обслуживание',30],['local_legal_partner_cooperation','Сотрудничество с местным юр. партнёром',20],['moldova_commercial_interest','Коммерческий интерес к Молдове',15],['decision_maker_accessibility','Доступность ЛПР',15]];
const j=v=>Array.isArray(v)?v.join('; '):(v==null?'':String(v));
const P=(t,o={})=>new Paragraph({spacing:{after:80},...o,children:[new TextRun({text:t,...(o.run||{})})]});
const LV=(label,val)=>new Paragraph({spacing:{after:80},children:[new TextRun({text:label+': ',bold:true}),new TextRun(j(val)||'not found')]});
const BL=t=>new Paragraph({numbering:{reference:'b',level:0},spacing:{after:40},children:[new TextRun(j(t))]});
const H1=t=>new Paragraph({heading:HeadingLevel.HEADING_1,children:[new TextRun(t)]});
const H2=t=>new Paragraph({heading:HeadingLevel.HEADING_2,children:[new TextRun(t)]});
const W=9026;
function cell(t,w,head){return new TableCell({width:{size:w,type:WidthType.DXA},margins:{top:60,bottom:60,left:100,right:100},
  shading:head?{type:ShadingType.CLEAR,fill:'1F3864',color:'auto'}:undefined,
  children:[new Paragraph({children:[new TextRun({text:j(t),bold:!!head,color:head?'FFFFFF':undefined,size:18})]})]});}
function table(widths,rows){return new Table({width:{size:W,type:WidthType.DXA},columnWidths:widths,rows:rows.map((r,i)=>new TableRow({tableHeader:i==0,children:r.map((t,k)=>cell(t,widths[k],i==0))}))});}
const kids=[];
kids.push(new Paragraph({heading:HeadingLevel.TITLE,children:[new TextRun('TOP-10 Partnership Dossiers')]}));
kids.push(P('LEGITIMUS | International Partnerships · Агент 02: Partnership Intelligence Analyst',{run:{bold:true}}));
kids.push(P('Дата проверки: 8 октября 2026 г. Конфиденциально, для внутреннего использования.'));
kids.push(H2('Как читать досье'));
[ 'Каждый ключевой вывод сопровождается источником и уровнем достоверности: High (официальный сайт или реестр), Medium (сниппет с официального домена или авторитетная пресса), Low (сторонний каталог или косвенные данные).',
  'ASSUMPTION — аналитическое допущение, не факт. «not found» значит, что сведения не найдены, а не что их нет.',
  'Сайты компаний из среды исследования открыть не удалось (ограничение сетевой политики). Проверка шла по поисковой выдаче, прежде всего по официальным доменам. Перед первым контактом откройте указанные ссылки.',
  'Фактические сведения о компаниях приведены на английском, как в источниках.',
  'Заинтересованность компаний в сотрудничестве не подтверждена: это оценка аналитика. Финансовые условия не предлагаются, кроме опубликованных самими компаниями.',
  'Никаких контактов с компаниями не было.'].forEach(t=>kids.push(BL(t)));
kids.push(H2('Сводка TOP-10'));
kids.push(table([500,2900,900,2226,2500],[['#','Компания','Балл','Статус','Формат'],...A.map((c,i)=>[i+1,c.name,c.total+'/100',c.status,c.dossier.preferred_format])]));
kids.push(P('GSL (65/100) не включён в TOP-10 до формальной санкционной проверки (см. Executive Recommendation).',{spacing:{before:120}}));
A.forEach((c,i)=>{
  const d=c.dossier,ct=c.contacts,m=c.moldova;
  kids.push(new Paragraph({children:[new PageBreak()]}));
  kids.push(H1(`${i+1}. ${c.name}`));
  kids.push(table([2200,6826],[['Поле','Значение'],['Статус',c.status],['Итоговый балл',c.total+' / 100'],['Сайт',c.website],['Штаб-квартира',c.hq],['Дата проверки',c.check_date]]));
  kids.push(H2('Company Profile'));
  kids.push(LV('Основные услуги',d.main_services));
  kids.push(LV('Международная география',d.geography));
  kids.push(LV('Фактическая специализация',c.specialization));
  kids.push(LV('Долгосрочные услуги',`${j(c.long_term_services.value)}: ${j(c.long_term_services.evidence)}`));
  kids.push(LV('Признаки разовых продаж',c.one_off_signals));
  kids.push(H2('Moldova Opportunity'));
  kids.push(LV('Текущий статус Молдовы',`${m.value} (как оказывается: ${m.delivery}). ${j(m.evidence)} [достоверность: ${m.confidence}]`));
  kids.push(LV('Источники',m.sources));
  kids.push(LV('Потребность в локальном партнёре',d.local_partner_need));
  kids.push(LV('Сотрудничество с независимыми юрфирмами',`${j(c.law_firm_cooperation.value)}: ${j(c.law_firm_cooperation.evidence)} [${c.law_firm_cooperation.confidence}]`));
  kids.push(LV('Потенциал долгосрочного юр. обслуживания',d.long_term_legal_potential));
  kids.push(H2('Decision Maker'));
  if(c.decision_makers.length) c.decision_makers.forEach(x=>kids.push(BL(`${x.name}, ${x.title}. Достоверность: ${x.confidence}. Источник: ${x.source}`)));
  else kids.push(P('Подтверждённое имя не найдено.'));
  kids.push(LV('Публичный канал связи',[ct.email,ct.phone,ct.contact_page].filter(Boolean).join(' | ')));
  kids.push(LV('Актуальность контактов',`${ct.current} (достоверность: ${ct.confidence})`));
  kids.push(H2('Partnership Strategy'));
  kids.push(LV('Почему LEGITIMUS может быть интересен',d.why_legitimus_interesting));
  kids.push(LV('Что предложить',d.what_to_offer));
  kids.push(LV('Предпочтительный формат',d.preferred_format));
  kids.push(new Paragraph({spacing:{after:40},children:[new TextRun({text:'Возможные возражения:',bold:true})]}));
  (Array.isArray(d.objections)?d.objections:[d.objections]).forEach(o=>kids.push(BL(o)));
  kids.push(LV('Рекомендуемый первый шаг',d.first_step));
  kids.push(H2('Обоснование оценки'));
  kids.push(table([2600,900,5526],[['Критерий','Балл','Обоснование'],...K.map(([k,n,mx])=>[n,`${c.scores[k].score}/${mx}`,c.scores[k].why])]));
  const flags=c.audit.filter(x=>x.status!=='confirmed');
  kids.push(H2('Проверка данных агента 01: расхождения и открытые вопросы'));
  if(flags.length) flags.forEach(x=>kids.push(BL(`[${x.status}] ${x.claim}: ${x.note}`)));
  else kids.push(P('Расхождений нет.'));
});
const doc=new Document({creator:'Agent 02',title:'TOP-10 Partnership Dossiers',
 styles:{default:{document:{run:{font:'Arial',size:20}}},paragraphStyles:[
  {id:'Heading1',name:'Heading 1',basedOn:'Normal',next:'Normal',quickFormat:true,run:{size:30,bold:true,color:'1F3864'},paragraph:{spacing:{before:120,after:160},outlineLevel:0}},
  {id:'Heading2',name:'Heading 2',basedOn:'Normal',next:'Normal',quickFormat:true,run:{size:24,bold:true,color:'2E5597'},paragraph:{spacing:{before:200,after:80},outlineLevel:1}}]},
 numbering:{config:[{reference:'b',levels:[{level:0,format:LevelFormat.BULLET,text:'•',alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:500,hanging:250}}}}]}]},
 sections:[{properties:{page:{margin:{top:1200,bottom:1200,left:1440,right:1440}}},
  footers:{default:new Footer({children:[new Paragraph({alignment:AlignmentType.RIGHT,children:[new TextRun({text:'LEGITIMUS · TOP-10 Partnership Dossiers · стр. ',size:16}),new TextRun({children:[PageNumber.CURRENT],size:16})]})]})},
  children:kids}]});
Packer.toBuffer(doc).then(b=>fs.writeFileSync('/home/user/-/research/agent02/TOP-10 Partnership Dossiers.docx',b));
