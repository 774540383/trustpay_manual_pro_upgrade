import os, asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from .config import settings
from . import db

main_bot = Bot(settings.main_bot_token)
kyc_bot = Bot(settings.kyc_bot_token)
main_dp = Dispatcher(storage=MemoryStorage())
kyc_dp = Dispatcher(storage=MemoryStorage())

class KycForm(StatesGroup):
    full_name=State(); phone=State(); address=State(); purpose=State(); details=State(); id_image=State(); selfie=State(); confirm=State()
class DepositForm(StatesGroup):
    amount=State(); currency=State(); platform=State(); destination=State(); method=State(); proof=State()
class WithdrawForm(StatesGroup):
    amount=State(); currency=State(); receiver=State(); txid=State(); proof=State()
class TicketForm(StatesGroup): message=State(); attachment=State()

def main_menu(active=False, tid=0):
    rows=[]
    if active:
        rows += [[KeyboardButton(text='📱 فتح لوحة الحساب', web_app=WebAppInfo(url=f"{settings.public_base_url}/app?tid={tid}"))],
                 [KeyboardButton(text='💰 إيداع'), KeyboardButton(text='🏧 سحب')],
                 [KeyboardButton(text='📊 محفظتي'), KeyboardButton(text='💱 أسعار USDT')],
                 [KeyboardButton(text='📦 طلباتي'), KeyboardButton(text='🎁 الإحالات')]]
    rows += [[KeyboardButton(text='🪪 توثيق الحساب')],[KeyboardButton(text='🎧 الدعم'), KeyboardButton(text='📞 واتساب')]]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

def kyc_start_kb(tid:int=0):
    url=f"{settings.public_base_url}/kyc-app?tid={tid}"
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🚀 بدء التوثيق', web_app=WebAppInfo(url=url))]])

def app_kb(tid:int):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='📱 فتح لوحة الحساب', web_app=WebAppInfo(url=f"{settings.public_base_url}/app?tid={tid}"))]])

async def notify_admins(text):
    for aid in settings.admin_id_list:
        try: await main_bot.send_message(aid, text)
        except Exception: pass

async def notify_user(tid:int, text:str):
    try: await main_bot.send_message(tid, text)
    except Exception: pass

@main_dp.message(CommandStart())
async def main_start(m:Message):
    ref=None
    parts=(m.text or '').split(maxsplit=1)
    if len(parts)>1: ref=parts[1].strip()
    db.ensure_user(m.from_user.id, m.from_user.username or '', m.from_user.full_name or '', ref)
    u=db.user(m.from_user.id)
    if u and u['is_active']:
        await m.answer(f"🔐 مرحباً بك في {settings.brand_name}\nحسابك مفعّل ✅\nاضغط فتح لوحة الحساب لتجربة Mini App.", reply_markup=main_menu(True,m.from_user.id))
        await m.answer('لوحة الحساب المصغرة:', reply_markup=app_kb(m.from_user.id))
    else:
        kb=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='🪪 توثيق الحساب', url=f'https://t.me/{(await kyc_bot.me()).username}')],
            [InlineKeyboardButton(text='📞 واتساب', url=settings.whatsapp_url)]])
        await m.answer("🔒 مرحباً بك!\n\nعذراً، لا يمكنك استخدام البوت حتى يتم تفعيل حسابك.\nيرجى توثيق الحساب للمتابعة.", reply_markup=kb)

@main_dp.message(F.text=='📱 فتح لوحة الحساب')
async def open_app(m:Message): await m.answer('افتح لوحة حسابك:', reply_markup=app_kb(m.from_user.id))
@main_dp.message(F.text=='🪪 توثيق الحساب')
async def go_kyc(m:Message): await m.answer('اضغط لفتح بوت التوثيق:', reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='فتح التوثيق', url=f'https://t.me/{(await kyc_bot.me()).username}')]]))
@main_dp.message(F.text=='📞 واتساب')
async def wa(m:Message): await m.answer(settings.whatsapp_url)
@main_dp.message(F.text=='💱 أسعار USDT')
async def price(m:Message):
    p=db.prices(); await m.answer(f"💱 أسعار USDT\n\nشراء: {p['buy_usdt']}\nبيع: {p['sell_usdt']}\nرسوم: {p['percent_fee']}% + {p['fixed_fee']}\nآخر تحديث: {p['updated_at']}")
@main_dp.message(F.text=='📊 محفظتي')
async def balance(m:Message):
    u=db.user(m.from_user.id); await m.answer(f"💼 محفظتي\n\nUSDT: {u['balance_usdt'] if u else 0}\nمحلي: {u['balance_local'] if u else 0}\nمجمد: {u['frozen_balance'] if u else 0}\nالمستوى: {u['level'] if u else 'عادي'}\nالنقاط: {u['points'] if u else 0}", reply_markup=app_kb(m.from_user.id))
@main_dp.message(F.text=='📦 طلباتي')
async def orders(m:Message):
    deps=db.my_deposits(m.from_user.id); wds=db.my_withdraws(m.from_user.id)
    txt='📦 آخر طلباتك\n\nالإيداعات:\n' + ('\n'.join([f"{x['order_no']} - {x['amount_usdt']} - {x['status']}" for x in deps[:5]]) or 'لا يوجد')
    txt+='\n\nالسحوبات:\n' + ('\n'.join([f"{x['order_no']} - {x['amount_usdt']} - {x['status']}" for x in wds[:5]]) or 'لا يوجد')
    await m.answer(txt, reply_markup=app_kb(m.from_user.id))
@main_dp.message(F.text=='🎁 الإحالات')
async def refs(m:Message):
    u=db.user(m.from_user.id); refs=db.referrals(m.from_user.id)
    await m.answer(f"🎁 الإحالات\n\nكودك: {u['referral_code']}\nرابطك: https://t.me/{(await main_bot.me()).username}?start={u['referral_code']}\nعدد الإحالات: {len(refs)}\nنقاطك: {u['points']}")

@main_dp.message(F.text=='💰 إيداع')
async def dep(m:Message, state:FSMContext):
    u=db.user(m.from_user.id)
    if not u or not u['is_active']: return await m.answer('يجب توثيق الحساب أولاً.')
    await state.set_state(DepositForm.amount); await m.answer('أدخل مبلغ الإيداع USDT:')
@main_dp.message(DepositForm.amount)
async def dep_amount(m:Message, state:FSMContext):
    try: amount=float(m.text.replace(',','.'))
    except: return await m.answer('اكتب مبلغ صحيح.')
    await state.update_data(amount=amount); await state.set_state(DepositForm.currency)
    await m.answer('اختر العملة التي ستدفع بها:', reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='USD'),KeyboardButton(text='SAR')]], resize_keyboard=True, one_time_keyboard=True))
@main_dp.message(DepositForm.currency)
async def dep_curr(m:Message, state:FSMContext):
    if m.text not in ['USD','SAR']: return await m.answer('اختر USD أو SAR')
    await state.update_data(currency=m.text); await state.set_state(DepositForm.platform); await m.answer('اكتب اسم المنصة أو الخدمة: Binance / Bybit / OKX / أخرى')
@main_dp.message(DepositForm.platform)
async def dep_platform(m:Message, state:FSMContext):
    await state.update_data(platform=m.text); await state.set_state(DepositForm.destination); await m.answer('اكتب عنوان محفظتك أو UID أو ملاحظات التحويل:')
@main_dp.message(DepositForm.destination)
async def dep_dest(m:Message, state:FSMContext):
    await state.update_data(destination=m.text); data=await state.get_data(); methods=db.payment_methods(data['currency'])
    if not methods: return await m.answer('لا توجد طرق دفع متاحة حالياً.')
    lines=['اختر طريقة الدفع بإرسال الرقم:']
    for x in methods: lines.append(f"{x['id']} - {x['name']} - {x['currency']}\nالاسم: {x['account_name']}\nالحساب/الهاتف: {x['account_number'] or x['phone']}\n{x['instructions']}")
    await state.set_state(DepositForm.method); await m.answer('\n\n'.join(lines))
@main_dp.message(DepositForm.method)
async def dep_method(m:Message, state:FSMContext):
    if not m.text.isdigit(): return await m.answer('أرسل رقم طريقة الدفع فقط.')
    await state.update_data(payment_method_id=int(m.text)); await state.set_state(DepositForm.proof); await m.answer('بعد التحويل أرسل صورة إثبات التحويل.')
@main_dp.message(DepositForm.proof, F.photo)
async def dep_proof(m:Message, state:FSMContext):
    data=await state.get_data(); os.makedirs(settings.upload_dir, exist_ok=True)
    path=os.path.join(settings.upload_dir, f"deposit_{m.from_user.id}_{m.message_id}.jpg")
    await main_bot.download(m.photo[-1], destination=path)
    no=db.create_deposit(m.from_user.id, data['amount'], data['currency'], data['platform'], data['destination'], data['payment_method_id'], path)
    await state.clear(); await m.answer(f'✅ تم استلام طلب الإيداع وهو قيد المراجعة.\nرقم الطلب: {no}', reply_markup=main_menu(True,m.from_user.id))
    await notify_admins(f"طلب إيداع جديد {no}\nالمستخدم: {m.from_user.id}\nالمبلغ: {data['amount']} USDT")

@main_dp.message(F.text=='🏧 سحب')
async def wd(m:Message, state:FSMContext):
    u=db.user(m.from_user.id)
    if not u or not u['is_active']: return await m.answer('يجب توثيق الحساب أولاً.')
    wallets=db.payment_methods('USDT')
    txt='حوّل USDT إلى محفظة الإدارة ثم أرسل الإثبات:\n\n'
    for w in wallets: txt+=f"الشبكة: {w['network']}\nالعنوان: {w['address']}\n{w['instructions']}\n\n"
    await state.set_state(WithdrawForm.amount); await m.answer(txt+'أدخل مبلغ السحب USDT:')
@main_dp.message(WithdrawForm.amount)
async def wd_amount(m:Message, state:FSMContext):
    try: amount=float(m.text.replace(',','.'))
    except: return await m.answer('اكتب مبلغ صحيح.')
    await state.update_data(amount=amount); await state.set_state(WithdrawForm.currency)
    await m.answer('اختر العملة المحلية التي تريد الاستلام بها:', reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='USD'),KeyboardButton(text='SAR')]], resize_keyboard=True, one_time_keyboard=True))
@main_dp.message(WithdrawForm.currency)
async def wd_curr(m:Message, state:FSMContext):
    if m.text not in ['USD','SAR']: return await m.answer('اختر USD أو SAR')
    await state.update_data(currency=m.text); await state.set_state(WithdrawForm.receiver); await m.answer('اكتب بيانات حسابك المحلي للاستلام: البنك، الاسم، رقم الحساب/الهاتف')
@main_dp.message(WithdrawForm.receiver)
async def wd_receiver(m:Message, state:FSMContext):
    await state.update_data(local_receiver=m.text); await state.set_state(WithdrawForm.txid); await m.answer('أرسل TXID أو اكتب تخطي:')
@main_dp.message(WithdrawForm.txid)
async def wd_txid(m:Message, state:FSMContext):
    await state.update_data(usdt_txid='' if m.text=='تخطي' else m.text); await state.set_state(WithdrawForm.proof); await m.answer('أرسل صورة إثبات تحويل USDT:')
@main_dp.message(WithdrawForm.proof, F.photo)
async def wd_proof(m:Message, state:FSMContext):
    data=await state.get_data(); os.makedirs(settings.upload_dir, exist_ok=True)
    path=os.path.join(settings.upload_dir, f"withdraw_{m.from_user.id}_{m.message_id}.jpg")
    await main_bot.download(m.photo[-1], destination=path)
    no=db.create_withdraw(m.from_user.id, data['amount'], data['currency'], data['local_receiver'], path, data.get('usdt_txid',''))
    await state.clear(); await m.answer(f'✅ تم إنشاء طلب السحب وهو قيد المراجعة.\nرقم الطلب: {no}', reply_markup=main_menu(True,m.from_user.id))
    await notify_admins(f"طلب سحب جديد {no}\nالمستخدم: {m.from_user.id}\nالمبلغ: {data['amount']} USDT")

@main_dp.message(F.text=='🎧 الدعم')
async def support(m:Message, state:FSMContext): await state.set_state(TicketForm.message); await m.answer('اكتب رسالتك للدعم:')
@main_dp.message(TicketForm.message)
async def ticket_msg(m:Message, state:FSMContext):
    db.add_ticket(m.from_user.id,m.text); await state.clear(); await m.answer('تم فتح تذكرتك بنجاح. ويمكنك إرفاق الصور من Mini App.', reply_markup=app_kb(m.from_user.id))

@kyc_dp.message(CommandStart())
async def kyc_start_msg(m:Message):
    db.ensure_user(m.from_user.id, m.from_user.username or '', m.from_user.full_name or '')
    old=db.active_kyc(m.from_user.id)
    if old and old['status']=='قيد المراجعة': return await m.answer(f"لديك طلب قيد المراجعة: {old['request_no']}")
    if old and old['status']=='مقبول': return await m.answer('حسابك موثق بالفعل ✅')
    await m.answer(f"مرحباً بك في بوت توثيق {settings.brand_name}! 👋\nيرجى الضغط على الزر أدناه لبدء عملية التوثيق.", reply_markup=kyc_start_kb(m.from_user.id))

@kyc_dp.callback_query(F.data=='kyc_start')
async def start_form(c, state:FSMContext):
    await c.message.answer('يرجى الضغط على زر بدء التوثيق لفتح صفحة التوثيق.')
    await c.answer()
@kyc_dp.message(KycForm.full_name)
async def k_name(m,state): await state.update_data(full_name=m.text); await state.set_state(KycForm.phone); await m.answer('رقم الهاتف اليمني، مثال 7xxxxxxxx:')
@kyc_dp.message(KycForm.phone)
async def k_phone(m,state):
    if not m.text.strip().startswith('7') or len(m.text.strip())<9: return await m.answer('الرقم غير صحيح. ابدأ بـ 7 واكتب الرقم كاملاً.')
    await state.update_data(phone=m.text.strip()); await state.set_state(KycForm.address); await m.answer('عنوان السكن بالتفصيل:')
@kyc_dp.message(KycForm.address)
async def k_addr(m,state):
    await state.update_data(address=m.text); await state.set_state(KycForm.purpose)
    await m.answer('اختر الغرض من شراء USDT:', reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='الإيداع إلى منصة تداول')],[KeyboardButton(text='شراء منتجات أو خدمات')],[KeyboardButton(text='غرض شخصي')]], resize_keyboard=True, one_time_keyboard=True))
@kyc_dp.message(KycForm.purpose)
async def k_purpose(m,state):
    if m.text not in ['الإيداع إلى منصة تداول','شراء منتجات أو خدمات','غرض شخصي']: return await m.answer('اختر من الأزرار.')
    await state.update_data(purpose=m.text); await state.set_state(KycForm.details)
    msg='اكتب اسم منصة التداول:' if m.text=='الإيداع إلى منصة تداول' else ('اكتب اسم الموقع أو المتجر:' if m.text=='شراء منتجات أو خدمات' else 'اكتب الغرض الشخصي أو أرسل كلمة تخطي:')
    await m.answer(msg)
@kyc_dp.message(KycForm.details)
async def k_details(m,state): await state.update_data(details='' if m.text=='تخطي' else m.text); await state.set_state(KycForm.id_image); await m.answer('صورة الهوية\n\nأرسل/التقط صورة الهوية بوضوح.')
@kyc_dp.message(KycForm.id_image, F.photo)
async def k_id(m,state):
    os.makedirs(settings.upload_dir, exist_ok=True); path=os.path.join(settings.upload_dir,f"id_{m.from_user.id}_{m.message_id}.jpg")
    await kyc_bot.download(m.photo[-1], destination=path); await state.update_data(id_image=path); await state.set_state(KycForm.selfie); await m.answer('الصورة الشخصية\n\nأرسل صورة سيلفي واضحة.')
@kyc_dp.message(KycForm.selfie, F.photo)
async def k_selfie(m,state):
    path=os.path.join(settings.upload_dir,f"selfie_{m.from_user.id}_{m.message_id}.jpg")
    await kyc_bot.download(m.photo[-1], destination=path); await state.update_data(selfie_image=path); data=await state.get_data(); await state.set_state(KycForm.confirm)
    await m.answer(f"مراجعة المعلومات\n\nالاسم: {data['full_name']}\nالهاتف: {data['phone']}\nالعنوان: {data['address']}\nالغرض: {data['purpose']}\nتفاصيل: {data.get('details','')}\n\nالشروط والأحكام:\n1️⃣ أتعهد بأن جميع المعلومات والصور صحيحة.\n2️⃣ أوافق على استخدام بياناتي للتحقق من هويتي.\n3️⃣ أفهم أن TrustPay لا يمثل منصة استثمارية.\n\nللموافقة اكتب: أوافق")
@kyc_dp.message(KycForm.confirm)
async def k_confirm(m,state):
    if 'أوافق' not in m.text: return await m.answer('لإرسال الطلب اكتب: أوافق')
    data=await state.get_data(); data['telegram_id']=m.from_user.id
    no=db.create_kyc(data); await state.clear()
    await m.answer(f"✅ تم إرسال طلب التوثيق بنجاح!\nرقم الطلب: {no}\n\nحالة الطلب: قيد المراجعة\nالوقت المتوقع للمراجعة: من 5 - 30 دقيقة")
    await notify_admins(f"طلب KYC جديد: {no}\nالمستخدم: {m.from_user.id}\nراجع لوحة الإدارة.")

async def run_bots():
    await asyncio.gather(main_dp.start_polling(main_bot), kyc_dp.start_polling(kyc_bot))
