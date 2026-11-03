const fs=require('fs');
const {Document,Packer,Paragraph,TextRun,HeadingLevel,Table,TableRow,TableCell,WidthType,ShadingType,LevelFormat,PageBreak,AlignmentType,Footer,Header,PageNumber,BorderStyle}=require('docx');
// text with [..] placeholders highlighted
function runs(t,o={}){const out=[];String(t).split(/(\[[^\]]+\])/).forEach(p=>{if(!p)return;const ph=/^\[.*\]$/.test(p);out.push(new TextRun({text:p,...o,...(ph?{highlight:'yellow',bold:true}:{})}));});return out;}
const P=(t,o={})=>new Paragraph({spacing:{after:120},...o.p,children:runs(t,o.r)});
const H1=t=>new Paragraph({heading:HeadingLevel.HEADING_1,children:[new TextRun(t)]});
const H2=t=>new Paragraph({heading:HeadingLevel.HEADING_2,children:[new TextRun(t)]});
const BL=t=>new Paragraph({numbering:{reference:'b',level:0},spacing:{after:60},children:runs(t)});
const NL=(t,ref)=>new Paragraph({numbering:{reference:ref,level:0},spacing:{after:60},children:runs(t)});
const LB=(l,t)=>new Paragraph({spacing:{after:100},children:[new TextRun({text:l+' ',bold:true}),...runs(t)]});
const W=9026;
function cell(t,w,head){return new TableCell({width:{size:w,type:WidthType.DXA},margins:{top:70,bottom:70,left:110,right:110},shading:head?{type:ShadingType.CLEAR,fill:'1F3864',color:'auto'}:undefined,children:[new Paragraph({children:runs(t,{bold:!!head,color:head?'FFFFFF':undefined,size:19})})]});}
function table(widths,rows){return new Table({width:{size:W,type:WidthType.DXA},columnWidths:widths,rows:rows.map((r,i)=>new TableRow({tableHeader:i==0,children:r.map((t,k)=>cell(t,widths[k],i==0))}))});}
const K=[];let nref=0;const numCfg=[];
function steps(arr){const ref='n'+(nref++);numCfg.push({reference:ref,levels:[{level:0,format:LevelFormat.DECIMAL,text:'%1.',alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:500,hanging:300}}}}]});arr.forEach(t=>K.push(NL(t,ref)));}
// ---------- Cover
K.push(new Paragraph({spacing:{before:2400,after:200},children:[new TextRun({text:'LEGITIMUS',bold:true,size:28,color:'1F3864'})]}));
K.push(new Paragraph({spacing:{after:120},children:[new TextRun({text:'Moldova Corporate Services Desk',bold:true,size:48,color:'1F3864'})]}));
K.push(new Paragraph({spacing:{after:600},children:[new TextRun({text:'Partnership Proposal for International Corporate Service Providers, Law and Consulting Firms',size:28,color:'2E5597'})]}));
K.push(P('Chișinău, Republic of Moldova · October 2026'));
K.push(P('DRAFT FOR INTERNAL APPROVAL. Not for distribution until the managing partner has completed and approved all highlighted fields.',{r:{bold:true,color:'C00000'}}));
K.push(P('Highlighted items in [square brackets] are not yet confirmed by LEGITIMUS and must be completed or deleted before this document is shared.',{r:{italics:true}}));
K.push(new Paragraph({children:[new PageBreak()]}));
// ---------- 1
K.push(H1('1. Purpose of this proposal'));
K.push(P('LEGITIMUS invites international corporate service providers, company formation specialists, and law and consulting firms to work with us as their local legal partner in the Republic of Moldova.'));
K.push(P('Our goal is long-term cooperation. We want to support your clients through incorporation and then through the life of their Moldovan business: corporate housekeeping, contracts, employment, regulatory compliance, data protection, transactions, and accounting and tax administration through our accounting partner MyAccounting.'));
// ---------- 2
K.push(H1('2. About LEGITIMUS'));
K.push(table([3000,6026],[['Item','Details'],['Legal form','[e.g. Birou de avocați / Birou asociat de avocați: TO CONFIRM]'],['Address','[Street, Chișinău, Republic of Moldova]'],['Responsible partner for the Desk','[Name, title]'],['Bar membership','[Union of Advocates of the Republic of Moldova: registration details TO CONFIRM]'],['Working languages','[English / Romanian / Russian: TO CONFIRM]'],['Team','[Number of advocates and key practice areas: TO CONFIRM]'],['Accounting partner','MyAccounting [legal name, form and relationship to LEGITIMUS: TO CONFIRM]'],['Contact','[Email] · [Phone] · [Website]']]));
// ---------- 3
K.push(H1('3. Why Moldova, and why now'));
K.push(BL('Moldova is an EU candidate country. Accession negotiations have formally started: the cluster on Fundamentals opened on 15 June 2026 and the cluster on External Relations on 14 July 2026 (source: Council of the European Union, consilium.europa.eu/en/policies/moldova).'));
K.push(BL('A new personal data protection framework applies from 23 August 2026: Law No. 195/2024 replaced Law No. 133/2011 and follows the GDPR model (source: Moldpres, 2026). Companies operating in Moldova may need to review their data processing documentation.'));
K.push(BL('Moldova borders Romania (EU) and Ukraine, which makes it relevant for providers that already serve clients in those markets.'));
K.push(P('We do not make forecasts about the timing of EU accession or about tax outcomes. Each client situation is assessed individually.',{r:{italics:true}}));
// ---------- 4
K.push(H1('4. What the Desk covers'));
const SV=[
['4.1 Company Incorporation & Corporate Structuring',['Advice on the choice of legal form (e.g. SRL, branch, representative office) and shareholding structure','Preparation of constitutional documents and registration filings [TO CONFIRM process with the Public Services Agency]','Review of foreign shareholder documents and legalisation requirements','Support with bank account opening documentation (opening of an account is at the bank\'s discretion and cannot be guaranteed)']],
['4.2 Corporate Governance & Secretarial Support',['Shareholder and director resolutions, minutes and registers','Changes of directors, shareholders, share capital, articles and registered address','Beneficial ownership information updates [TO CONFIRM scope]','Annual corporate housekeeping and deadline monitoring']],
['4.3 Ongoing Legal Advisory',['Monthly legal support packages for operating companies','A single point of contact for day-to-day legal questions in Moldova','Legal opinions (e.g. capacity, good standing) [TO CONFIRM languages and types]']],
['4.4 Commercial Contracts',['Drafting and review of supply, service, distribution, lease and IT contracts','Bilingual documentation [TO CONFIRM language pairs]']],
['4.5 Regulatory & Compliance',['Licensing and permits for regulated activities [TO CONFIRM sectors]','AML/KYC documentation for client companies','Interaction with public authorities within the scope of the engagement']],
['4.6 Data Protection & Privacy',['Gap assessment against Law No. 195/2024','Privacy notices, records of processing, data processing agreements','Cross-border data transfer documentation [TO CONFIRM scope]']],
['4.7 Employment & HR Legal Support',['Employment contracts and internal regulations','Hiring of foreign nationals: work and residence permit support [TO CONFIRM that LEGITIMUS provides this]','Terminations and employment disputes [TO CONFIRM litigation scope]']],
['4.8 Investment Transactions & M&A',['Legal due diligence on Moldovan companies and assets','Share and asset deals, investment structuring, closing support [TO CONFIRM track record to be cited]']],
['4.9 Accounting & Tax Administration (through MyAccounting)',['Bookkeeping, tax returns and financial statements','Payroll','VAT and tax registrations [TO CONFIRM split between LEGITIMUS and MyAccounting]','Accounting services are provided by MyAccounting under a separate engagement [TO CONFIRM]']]];
SV.forEach(([h,b])=>{K.push(H2(h));b.forEach(x=>K.push(BL(x)));});
K.push(P('Timelines depend on the specific case, on documents provided by the client and on public authorities. Indicative timelines are agreed per engagement [TO CONFIRM standard response time].',{r:{italics:true}}));
// ---------- 5 Models
K.push(new Paragraph({children:[new PageBreak()]}));
K.push(H1('5. Three ways to work with us'));
K.push(table([1700,2442,2442,2442],[['','Model A: New Jurisdiction Partner','Model B: Local Execution Partner','Model C: Long-Term Legal Desk'],['Designed for','Providers that do not yet list Moldova','Providers that already offer Moldova','International law and consulting firms and global corporate service providers'],['Core idea','Add Moldova to your catalogue; LEGITIMUS acts as your local legal partner','An additional or alternative local partner for execution and ongoing support','Ongoing legal support for your clients in Moldova, with accounting through MyAccounting'],['Typical start','First client request','Pilot of 1–3 matters','Framework agreement, then client onboarding']]));
const M=[
['Model A — New Jurisdiction Partner',
 'International providers whose published catalogue does not include Moldova.',
 ['Add Moldova to your offer without opening an office or hiring staff','Answer client requests from neighbouring markets with a qualified local legal partner','Turn one-off incorporations into ongoing legal, corporate and accounting support','One local point of contact instead of sourcing a new provider for each request'],
 ['You send the client request using a short intake form','LEGITIMUS runs a conflict check and KYC/AML under Moldovan law','We confirm the document list, scope and fee estimate [TO CONFIRM response time]','Engagement is signed [direct with the client or through the partner: TO AGREE]','We carry out the work and report status to you','After incorporation, the client can move to ongoing support (legal retainer and/or MyAccounting)'],
 [['Client origination, first-level KYC, client relationship','Partner'],['Moldovan legal work, documents, filings, KYC under Moldovan law','LEGITIMUS'],['Bookkeeping and tax reporting','MyAccounting'],['Invoicing','[TO AGREE]']],
 ['Contracting model: direct engagement or subcontracting','Commercial mechanics in line with Moldovan professional rules for advocates [referral arrangements TO CONFIRM]','Initial package to list Moldova in your catalogue','Branding and how LEGITIMUS is presented','Non-exclusivity and scope']],
['Model B — Local Execution Partner',
 'Providers that already offer company services in Moldova.',
 ['A second local partner reduces dependence on a single provider','Legal opinions and advice that require a qualified advocate','More revenue per client through post-incorporation services','Agreed reporting standards and response times [SLA TO AGREE]'],
 ['Pilot with 1–3 matters through the intake form','Conflict check and KYC/AML','Fixed quote based on the Partner Rate Card','Execution with status reporting in the agreed format','Framework agreement after a successful pilot'],
 [['Client relationship','Partner (or jointly: TO AGREE)'],['Legal execution and responsibility for legal documents','LEGITIMUS'],['Accounting (optional)','MyAccounting'],['Invoicing','[LEGITIMUS to partner, or LEGITIMUS to client: TO AGREE]']],
 ['Whether white-label or subcontracting arrangements are permitted under Moldovan rules for advocates [TO CONFIRM]','Partner pricing and volume thresholds','Service levels for response and reporting','Professional indemnity insurance requirements [TO CONFIRM]','Non-exclusivity and transition from an existing provider']],
['Model C — Long-Term Legal Desk',
 'International law firms, consulting firms and global corporate service providers whose clients need continuous legal support in Moldova.',
 ['Predictable local support for clients with operations in Moldova','One monthly arrangement instead of ad hoc instructions','Coverage of legal changes, such as the new data protection law','Legal and accounting support coordinated in one place'],
 ['Framework cooperation agreement','Client onboarding: KYC, conflict check, assigned responsible advocate','Monthly support through an hours package or fixed fee [TO CONFIRM]','Periodic reporting to the partner, subject to client consent and professional secrecy'],
 [['Global client relationship','Partner'],['Moldovan legal advice and representation','LEGITIMUS'],['Accounting, payroll and tax','MyAccounting'],['Coordination','[Responsible partner at LEGITIMUS: TO ASSIGN]']],
 ['Package structure and overflow hourly rates','Client consent for information sharing with the partner','Vendor onboarding requirements (insurance, policies, due diligence)','Working languages [TO CONFIRM]']]];
M.forEach(([h,f,b,s,roles,c])=>{
  K.push(H2(h));K.push(LB('Designed for:',f));
  K.push(new Paragraph({spacing:{after:60},children:[new TextRun({text:'Benefits for the partner',bold:true})]}));b.forEach(x=>K.push(BL(x)));
  K.push(new Paragraph({spacing:{before:80,after:60},children:[new TextRun({text:'How a request is handed over',bold:true})]}));steps(s);
  K.push(new Paragraph({spacing:{before:80,after:60},children:[new TextRun({text:'Who does what',bold:true})]}));
  K.push(table([5526,3500],[['Task','Responsible'],...roles]));
  K.push(new Paragraph({spacing:{before:120,after:60},children:[new TextRun({text:'Commercial points to agree',bold:true})]}));c.forEach(x=>K.push(BL(x)));
});
// ---------- 6
K.push(new Paragraph({children:[new PageBreak()]}));
K.push(H1('6. How we work'));
[['Engagement and conflicts.','Every matter starts with a conflict check and a written engagement letter.'],
 ['KYC/AML.','We identify clients and beneficial owners and apply the anti-money-laundering requirements that apply to LEGITIMUS under Moldovan law. We may decline instructions.'],
 ['Professional secrecy.','Client information is protected by advocate–client privilege. Information is shared with partners only with the client\'s consent or as the engagement allows.'],
 ['Data protection.','We process personal data in line with Law No. 195/2024 and can sign data processing terms with partners [TO CONFIRM template].'],
 ['Communication and reporting.','A named contact person for each partner, status updates in the agreed format, and work in [English / Romanian / Russian: TO CONFIRM].'],
 ['Service levels.','[Response time and reporting frequency: TO AGREE per partnership].'],
 ['Liability and insurance.','[Professional indemnity insurance details: TO CONFIRM].']].forEach(([a,b])=>K.push(LB(a,b)));
// ---------- 7
K.push(H1('7. Commercial framework'));
K.push(BL('Fees are set out in a Partner Rate Card shared after an initial call and agreed in writing for each engagement.'));
K.push(BL('State fees, notary costs, translations and apostilles are passed through at cost unless agreed otherwise.'));
K.push(BL('Any referral, fee-sharing or subcontracting arrangement will be offered only to the extent permitted by the rules governing advocates in the Republic of Moldova [TO CONFIRM following internal review].'));
K.push(BL('Accounting services are priced and contracted by MyAccounting [TO CONFIRM].'));
// ---------- 8
K.push(H1('8. Suggested next steps'));
steps(['Introductory call to understand your client flows and Moldova demand','Choose the model (A, B or C) and agree the intake form','Pilot on initial matters','Framework cooperation agreement']);
K.push(H1('Contact'));
K.push(P('[Name, title] · LEGITIMUS · [Address], Chișinău, Republic of Moldova · [Email] · [Phone] · [Website]'));
K.push(P('This document is a general description of proposed cooperation. It is not legal advice and is not an offer to enter into a contract. Services are provided only under a signed engagement letter and subject to conflict and KYC checks.',{r:{italics:true,size:17}}));
const doc=new Document({creator:'LEGITIMUS',title:'Moldova Corporate Services Desk — Partnership Proposal',
 styles:{default:{document:{run:{font:'Arial',size:21}}},paragraphStyles:[
  {id:'Heading1',name:'Heading 1',basedOn:'Normal',next:'Normal',quickFormat:true,run:{size:30,bold:true,color:'1F3864'},paragraph:{spacing:{before:300,after:140},outlineLevel:0}},
  {id:'Heading2',name:'Heading 2',basedOn:'Normal',next:'Normal',quickFormat:true,run:{size:24,bold:true,color:'2E5597'},paragraph:{spacing:{before:200,after:80},outlineLevel:1}}]},
 numbering:{config:[{reference:'b',levels:[{level:0,format:LevelFormat.BULLET,text:'•',alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:500,hanging:250}}}}]},...numCfg]},
 sections:[{properties:{page:{margin:{top:1300,bottom:1200,left:1440,right:1440}}},
  headers:{default:new Header({children:[new Paragraph({alignment:AlignmentType.RIGHT,children:[new TextRun({text:'LEGITIMUS · Moldova Corporate Services Desk · DRAFT',size:16,color:'808080'})]})]})},
  footers:{default:new Footer({children:[new Paragraph({alignment:AlignmentType.RIGHT,children:[new TextRun({text:'Page ',size:16}),new TextRun({children:[PageNumber.CURRENT],size:16})]})]})},
  children:K}]});
Packer.toBuffer(doc).then(b=>fs.writeFileSync('/home/user/-/research/agent03/LEGITIMUS_Partnership_Proposal.docx',b));
