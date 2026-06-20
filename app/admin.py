from fastapi import FastAPI, Request, Form, Depends, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets, os
from .config import settings
from . import db

app=FastAPI(title=f"{settings.brand_name} Admin")
templates=Jinja2Templates(directory="app/templates")
security=HTTPBasic()

def auth(creds:HTTPBasicCredentials=Depends(security)):
    ok_user=secrets.compare_digest(creds.username, settings.admin_username)
    ok_pass=secrets.compare_digest(creds.password, settings.admin_password)
    if not (ok_user and ok_pass):
        raise HTTPException(status_code=401, detail="Unauthorized", headers={"WWW-Authenticate":"Basic"})
    return creds.username

@app.get('/health')
def health(): return {'ok': True, 'brand': settings.brand_name}

@app.get('/', response_class=HTMLResponse)
def root(request:Request, admin=Depends(auth)):
    return RedirectResponse('/admin/dashboard')

@app.get('/admin/login', response_class=HTMLResponse)
def login_hint(request:Request, admin=Depends(auth)):
    return RedirectResponse('/admin/dashboard')

@app.get('/admin/dashboard', response_class=HTMLResponse)
def dashboard(request:Request, admin=Depends(auth)):
    return templates.TemplateResponse('dashboard.html', {
        'request':request,'brand':settings.brand_name,'stats':db.stats(),
        'kycs':db.list_kyc(),'deposits':db.list_deposits(),'withdraws':db.list_withdraws(),
        'tickets':db.list_tickets(),'prices':db.prices(),'methods':db.payment_methods(active=False)
    })

@app.get('/app', response_class=HTMLResponse)
def mini_app(request:Request, tid:int=0):
    u=db.user(tid) if tid else None
    return templates.TemplateResponse('mini_app.html', {
        'request':request,'brand':settings.brand_name,'u':u,'tid':tid,
        'prices':db.prices(),'methods':db.payment_methods(active=True),
        'deposits':db.my_deposits(tid) if tid else [], 'withdraws':db.my_withdraws(tid) if tid else [],
        'txs':db.my_transactions(tid) if tid else [], 'notes':db.notifications(tid) if tid else [],
        'refs':db.referrals(tid) if tid else [],
        'usdt_wallets':[m for m in db.payment_methods('USDT')]
    })


@app.get('/kyc-app', response_class=HTMLResponse)
def kyc_app(request:Request, tid:int=0):
    return templates.TemplateResponse('kyc_app.html', {'request':request,'brand':settings.brand_name,'tid':tid})

@app.post('/kyc-app/submit', response_class=HTMLResponse)
async def kyc_app_submit(request:Request, telegram_id:int=Form(...), full_name:str=Form(...), phone:str=Form(...), address:str=Form(...), purpose:str=Form(...), details:str=Form(''), id_image:UploadFile=File(...), selfie_image:UploadFile=File(...)):
    os.makedirs(settings.upload_dir, exist_ok=True)
    db.ensure_user(telegram_id, '', full_name, None)
    suffix=db.rand_no('KYCIMG')
    id_path=os.path.join(settings.upload_dir, f"id_{telegram_id}_{suffix}_{id_image.filename}")
    selfie_path=os.path.join(settings.upload_dir, f"selfie_{telegram_id}_{suffix}_{selfie_image.filename}")
    with open(id_path,'wb') as f: f.write(await id_image.read())
    with open(selfie_path,'wb') as f: f.write(await selfie_image.read())
    no=db.create_kyc({'telegram_id':telegram_id,'full_name':full_name,'phone':phone,'address':address,'purpose':purpose,'details':details,'id_image':id_path,'selfie_image':selfie_path})
    return templates.TemplateResponse('kyc_success.html', {'request':request,'brand':settings.brand_name,'request_no':no})

@app.post('/app/deposit')
async def app_deposit(tid:int=Form(...), amount:float=Form(...), currency:str=Form(...), platform:str=Form(''), destination:str=Form(''), payment_method_id:int=Form(...), proof:UploadFile=File(...)):
    os.makedirs(settings.upload_dir, exist_ok=True)
    path=os.path.join(settings.upload_dir, f"dep_{tid}_{db.rand_no('P')}_{proof.filename}")
    with open(path,'wb') as f: f.write(await proof.read())
    db.create_deposit(tid, amount, currency, platform, destination, payment_method_id, path)
    return RedirectResponse(f'/app?tid={tid}', status_code=303)

@app.post('/app/withdraw')
async def app_withdraw(tid:int=Form(...), amount:float=Form(...), currency:str=Form(...), local_receiver:str=Form(...), usdt_txid:str=Form(''), proof:UploadFile=File(...)):
    os.makedirs(settings.upload_dir, exist_ok=True)
    path=os.path.join(settings.upload_dir, f"wdr_{tid}_{db.rand_no('P')}_{proof.filename}")
    with open(path,'wb') as f: f.write(await proof.read())
    db.create_withdraw(tid, amount, currency, local_receiver, path, usdt_txid)
    return RedirectResponse(f'/app?tid={tid}', status_code=303)

@app.post('/app/ticket')
async def app_ticket(tid:int=Form(...), message:str=Form(...), attachment:UploadFile|None=File(None)):
    path=''
    if attachment and attachment.filename:
        os.makedirs(settings.upload_dir, exist_ok=True)
        path=os.path.join(settings.upload_dir, f"ticket_{tid}_{db.rand_no('T')}_{attachment.filename}")
        with open(path,'wb') as f: f.write(await attachment.read())
    db.add_ticket(tid,message,path)
    return RedirectResponse(f'/app?tid={tid}', status_code=303)

@app.get('/app/statement')
def statement(tid:int=0):
    u=db.user(tid)
    txs=db.my_transactions(tid)
    lines=[f"TrustPay Statement", f"User: {u['full_name'] if u else tid}", f"Telegram ID: {tid}", ""]
    for t in txs:
        lines.append(f"{t['created_at']} | {t['tx_type']} | {t['amount_usdt']} USDT | {t['description']}")
    pdf = make_simple_pdf('\n'.join(lines))
    return Response(pdf, media_type='application/pdf', headers={'Content-Disposition': f'attachment; filename=statement_{tid}.pdf'})

def make_simple_pdf(text:str)->bytes:
    safe=text.encode('latin-1','replace').decode('latin-1')
    stream="BT /F1 10 Tf 50 780 Td "
    for line in safe.split('\n')[:55]:
        line=line.replace('(','[').replace(')',']')[:100]
        stream+=f"({line}) Tj 0 -14 Td "
    stream+="ET"
    objs=[]
    objs.append("1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj")
    objs.append("2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj")
    objs.append("3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj")
    objs.append("4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj")
    objs.append(f"5 0 obj << /Length {len(stream)} >> stream\n{stream}\nendstream endobj")
    pdf="%PDF-1.4\n"; offsets=[]
    for o in objs:
        offsets.append(len(pdf.encode('latin-1'))); pdf+=o+'\n'
    xref=len(pdf.encode('latin-1'))
    pdf+=f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n"
    for off in offsets: pdf+=f"{off:010d} 00000 n \n"
    pdf+=f"trailer << /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF"
    return pdf.encode('latin-1')

@app.get('/kyc/{rid}', response_class=HTMLResponse)
def kyc_detail(rid:int, request:Request, admin=Depends(auth)):
    item=db.get_kyc(rid)
    if not item: raise HTTPException(404)
    return templates.TemplateResponse('kyc_detail.html', {'request':request,'brand':settings.brand_name,'r':item})

@app.post('/kyc/{rid}/review')
def kyc_review(rid:int, status:str=Form(...), reason:str=Form(''), admin=Depends(auth)):
    db.review_kyc(rid,status,reason,admin)
    return RedirectResponse('/admin/dashboard', status_code=303)

@app.post('/deposit/{oid}/review')
def dep_review(oid:int, status:str=Form(...), note:str=Form(''), admin=Depends(auth)):
    db.review_deposit(oid,status,note,admin)
    return RedirectResponse('/admin/dashboard', status_code=303)

@app.post('/withdraw/{oid}/review')
def wd_review(oid:int, status:str=Form(...), note:str=Form(''), admin=Depends(auth)):
    db.review_withdraw(oid,status,note,admin)
    return RedirectResponse('/admin/dashboard', status_code=303)

@app.post('/ticket/{tid}/reply')
def ticket_reply(tid:int, reply:str=Form(...), status:str=Form('مغلقة'), admin=Depends(auth)):
    db.reply_ticket(tid,reply,status)
    return RedirectResponse('/admin/dashboard', status_code=303)

@app.post('/admin/prices')
def prices_update(buy_usdt:float=Form(...), sell_usdt:float=Form(...), fixed_fee:float=Form(...), percent_fee:float=Form(...), admin=Depends(auth)):
    db.update_prices(buy_usdt,sell_usdt,fixed_fee,percent_fee)
    return RedirectResponse('/admin/dashboard', status_code=303)

@app.post('/admin/payment-methods')
def add_method(name:str=Form(...), currency:str=Form(...), account_name:str=Form(''), account_number:str=Form(''), phone:str=Form(''), network:str=Form(''), address:str=Form(''), instructions:str=Form(''), admin=Depends(auth)):
    db.add_payment_method(locals())
    return RedirectResponse('/admin/dashboard', status_code=303)

@app.post('/admin/payment-methods/{mid}/toggle')
def toggle_method(mid:int, active:int=Form(...), admin=Depends(auth)):
    db.set_payment_active(mid, bool(active))
    return RedirectResponse('/admin/dashboard', status_code=303)

@app.get('/file')
def file(path:str, admin=Depends(auth)):
    return FileResponse(path)
