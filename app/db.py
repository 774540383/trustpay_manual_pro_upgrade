import sqlite3, secrets, string, os
from datetime import datetime
from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
 telegram_id INTEGER PRIMARY KEY,
 username TEXT,
 full_name TEXT,
 phone TEXT,
 is_active INTEGER DEFAULT 0,
 kyc_status TEXT DEFAULT 'غير موثق',
 level TEXT DEFAULT 'عادي',
 balance_usdt REAL DEFAULT 0,
 balance_local REAL DEFAULT 0,
 frozen_balance REAL DEFAULT 0,
 points INTEGER DEFAULT 0,
 referral_code TEXT,
 referred_by INTEGER,
 created_at TEXT,
 last_seen TEXT
);
CREATE TABLE IF NOT EXISTS kyc_requests(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 request_no TEXT UNIQUE,
 telegram_id INTEGER,
 full_name TEXT,
 phone TEXT,
 address TEXT,
 purpose TEXT,
 details TEXT,
 id_image TEXT,
 selfie_image TEXT,
 status TEXT DEFAULT 'قيد المراجعة',
 reject_reason TEXT,
 created_at TEXT,
 reviewed_at TEXT
);
CREATE TABLE IF NOT EXISTS deposit_orders(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 order_no TEXT UNIQUE,
 telegram_id INTEGER,
 amount_usdt REAL,
 currency TEXT,
 platform TEXT,
 destination TEXT,
 payment_method_id INTEGER,
 proof TEXT,
 status TEXT DEFAULT 'قيد المراجعة',
 admin_note TEXT,
 created_at TEXT,
 reviewed_at TEXT
);
CREATE TABLE IF NOT EXISTS withdraw_orders(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 order_no TEXT UNIQUE,
 telegram_id INTEGER,
 amount_usdt REAL,
 currency TEXT,
 local_receiver TEXT,
 usdt_txid TEXT,
 proof TEXT,
 status TEXT DEFAULT 'قيد المراجعة',
 admin_note TEXT,
 created_at TEXT,
 reviewed_at TEXT
);
CREATE TABLE IF NOT EXISTS operations(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 telegram_id INTEGER,
 op_type TEXT,
 amount REAL,
 network TEXT,
 wallet TEXT,
 proof TEXT,
 status TEXT DEFAULT 'قيد المراجعة',
 created_at TEXT
);
CREATE TABLE IF NOT EXISTS transactions(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 telegram_id INTEGER,
 tx_type TEXT,
 amount_usdt REAL DEFAULT 0,
 amount_local REAL DEFAULT 0,
 description TEXT,
 related_order TEXT,
 created_at TEXT
);
CREATE TABLE IF NOT EXISTS payment_methods(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT,
 currency TEXT,
 account_name TEXT,
 account_number TEXT,
 phone TEXT,
 network TEXT,
 address TEXT,
 instructions TEXT,
 is_active INTEGER DEFAULT 1,
 created_at TEXT
);
CREATE TABLE IF NOT EXISTS prices(
 id INTEGER PRIMARY KEY CHECK(id=1),
 buy_usdt REAL DEFAULT 540,
 sell_usdt REAL DEFAULT 545,
 fixed_fee REAL DEFAULT 0,
 percent_fee REAL DEFAULT 1.5,
 updated_at TEXT
);
CREATE TABLE IF NOT EXISTS loyalty_levels(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT,
 daily_limit REAL,
 monthly_limit REAL,
 fee_percent REAL,
 priority INTEGER,
 perks TEXT
);
CREATE TABLE IF NOT EXISTS referrals(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 referrer_id INTEGER,
 referred_id INTEGER,
 reward_usdt REAL DEFAULT 0,
 status TEXT DEFAULT 'معلق',
 created_at TEXT
);
CREATE TABLE IF NOT EXISTS tickets(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 telegram_id INTEGER,
 message TEXT,
 attachment TEXT,
 admin_reply TEXT,
 status TEXT DEFAULT 'مفتوحة',
 created_at TEXT,
 updated_at TEXT
);
CREATE TABLE IF NOT EXISTS notifications(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 telegram_id INTEGER,
 title TEXT,
 body TEXT,
 is_read INTEGER DEFAULT 0,
 created_at TEXT
);
CREATE TABLE IF NOT EXISTS audit_logs(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 actor TEXT,
 action TEXT,
 target TEXT,
 created_at TEXT
);
"""

def conn():
    os.makedirs(os.path.dirname(settings.database_path), exist_ok=True)
    c=sqlite3.connect(settings.database_path)
    c.row_factory=sqlite3.Row
    return c

def _safe_alter(c, table, coldef):
    col=coldef.split()[0]
    cols=[r['name'] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]
    if col not in cols:
        try: c.execute(f"ALTER TABLE {table} ADD COLUMN {coldef}")
        except Exception: pass

def init_db():
    with conn() as c:
        c.executescript(SCHEMA)
        # migrate older DB safely
        for cd in ["phone TEXT","kyc_status TEXT DEFAULT 'غير موثق'","balance_local REAL DEFAULT 0","frozen_balance REAL DEFAULT 0","points INTEGER DEFAULT 0","referral_code TEXT","referred_by INTEGER","last_seen TEXT"]:
            _safe_alter(c,'users',cd)
        seed_defaults(c)

def seed_defaults(c):
    # prices
    c.execute("INSERT OR IGNORE INTO prices(id,buy_usdt,sell_usdt,fixed_fee,percent_fee,updated_at) VALUES(1,540,545,0,1.5,?)",(now(),))
    # payment methods default only if empty
    count=c.execute("SELECT COUNT(*) n FROM payment_methods").fetchone()['n']
    if count==0:
        rows=[
            ('محفظة جيب','USD','عبد الرحمن جميل عبد الله احمد','', '734931350','','','حساب محفظة جيب - دولار أمريكي',1,now()),
            ('محفظة جيب','SAR','عبد الرحمن جميل عبد الله احمد','', '734931350','','','حساب محفظة جيب - ريال سعودي',1,now()),
            ('بنك الكريمي','USD','عبد الرحمن جميل عبد الله احمد','3093983563','','','','حساب دولار أمريكي',1,now()),
            ('بنك الكريمي','SAR','عبد الرحمن جميل عبد الله احمد','3094096088','','','','حساب ريال سعودي',1,now()),
            ('بنك القطيبي','USD','عبد الرحمن جميل عبد الله احمد','476870181','','','','حساب دولار أمريكي',1,now()),
            ('بنك القطيبي','SAR','عبد الرحمن جميل عبد الله احمد','476870181','','','','حساب ريال سعودي',1,now()),
            ('USDT BEP20','USDT','TrustPay USDT Wallet','','','BNB Smart Chain (BEP20)','0x0633bee3d780bc83ec704641fd0d366843b9e2aa','لا ترسل NFT. USDT فقط على شبكة BSC/BEP20',1,now()),
        ]
        c.executemany("INSERT INTO payment_methods(name,currency,account_name,account_number,phone,network,address,instructions,is_active,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)", rows)
    if c.execute("SELECT COUNT(*) n FROM loyalty_levels").fetchone()['n']==0:
        levels=[('عادي',500,3000,1.5,4,'حدود أساسية'),('فضي',1000,8000,1.2,3,'رسوم أقل ومراجعة أسرع'),('ذهبي',3000,20000,0.9,2,'أولوية ومراجعة أسرع'),('VIP',10000,100000,0.5,1,'أعلى حدود وأقل رسوم')]
        c.executemany("INSERT INTO loyalty_levels(name,daily_limit,monthly_limit,fee_percent,priority,perks) VALUES(?,?,?,?,?,?)", levels)

def now(): return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def rand_no(prefix='KYC'):
    code=''.join(secrets.choice(string.ascii_uppercase+string.digits) for _ in range(8))
    return f"{prefix}-{datetime.now().strftime('%Y%m%d')}-{code}"

def ensure_user(tid:int, username='', full_name='', ref=None):
    code='TP'+''.join(secrets.choice(string.ascii_uppercase+string.digits) for _ in range(7))
    with conn() as c:
        old=c.execute("SELECT * FROM users WHERE telegram_id=?",(tid,)).fetchone()
        if not old:
            referred_by=None
            if ref:
                r=c.execute("SELECT telegram_id FROM users WHERE referral_code=?",(ref,)).fetchone()
                if r and r['telegram_id']!=tid: referred_by=r['telegram_id']
            c.execute("INSERT INTO users(telegram_id,username,full_name,referral_code,referred_by,created_at,last_seen) VALUES(?,?,?,?,?,?,?)",(tid,username,full_name,code,referred_by,now(),now()))
            if referred_by:
                c.execute("INSERT INTO referrals(referrer_id,referred_id,created_at) VALUES(?,?,?)",(referred_by,tid,now()))
        else:
            c.execute("UPDATE users SET username=?, full_name=?, last_seen=? WHERE telegram_id=?",(username,full_name,now(),tid))

def user(tid:int):
    with conn() as c: return c.execute("SELECT * FROM users WHERE telegram_id=?",(tid,)).fetchone()

def stats():
    with conn() as c:
        return {
            'users': c.execute("SELECT COUNT(*) n FROM users").fetchone()['n'],
            'kyc_pending': c.execute("SELECT COUNT(*) n FROM kyc_requests WHERE status='قيد المراجعة'").fetchone()['n'],
            'dep_pending': c.execute("SELECT COUNT(*) n FROM deposit_orders WHERE status='قيد المراجعة'").fetchone()['n'],
            'wd_pending': c.execute("SELECT COUNT(*) n FROM withdraw_orders WHERE status='قيد المراجعة'").fetchone()['n'],
            'completed': c.execute("SELECT COUNT(*) n FROM transactions").fetchone()['n'],
            'fees': 0,
        }

def prices():
    with conn() as c: return c.execute("SELECT * FROM prices WHERE id=1").fetchone()

def update_prices(buy,sell,fixed,percent):
    with conn() as c: c.execute("UPDATE prices SET buy_usdt=?,sell_usdt=?,fixed_fee=?,percent_fee=?,updated_at=? WHERE id=1",(buy,sell,fixed,percent,now()))

def payment_methods(currency=None, active=True):
    with conn() as c:
        q="SELECT * FROM payment_methods WHERE 1=1"; params=[]
        if active: q+=" AND is_active=1"
        if currency: q+=" AND currency=?"; params.append(currency)
        q+=" ORDER BY id DESC"
        return c.execute(q,params).fetchall()

def add_payment_method(data):
    with conn() as c:
        c.execute("INSERT INTO payment_methods(name,currency,account_name,account_number,phone,network,address,instructions,is_active,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (data.get('name'),data.get('currency'),data.get('account_name'),data.get('account_number'),data.get('phone'),data.get('network'),data.get('address'),data.get('instructions'),1,now()))

def set_payment_active(mid, active):
    with conn() as c: c.execute("UPDATE payment_methods SET is_active=? WHERE id=?",(1 if active else 0,mid))

def active_kyc(tid:int):
    with conn() as c: return c.execute("SELECT * FROM kyc_requests WHERE telegram_id=? AND status IN ('قيد المراجعة','مقبول') ORDER BY id DESC LIMIT 1",(tid,)).fetchone()

def create_kyc(data:dict):
    no=rand_no('KYC')
    with conn() as c:
        c.execute("""INSERT INTO kyc_requests(request_no,telegram_id,full_name,phone,address,purpose,details,id_image,selfie_image,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?)""",(no,data['telegram_id'],data['full_name'],data['phone'],data['address'],data['purpose'],data.get('details',''),data['id_image'],data['selfie_image'],now()))
        c.execute("UPDATE users SET phone=?, kyc_status='قيد المراجعة' WHERE telegram_id=?",(data['phone'],data['telegram_id']))
        add_notification_tx(c,data['telegram_id'],'تم إرسال طلب التوثيق',f'رقم الطلب: {no}')
    return no

def list_kyc(status=None):
    with conn() as c:
        if status: return c.execute("SELECT * FROM kyc_requests WHERE status=? ORDER BY id DESC",(status,)).fetchall()
        return c.execute("SELECT * FROM kyc_requests ORDER BY id DESC LIMIT 200").fetchall()

def get_kyc(rid:int):
    with conn() as c: return c.execute("SELECT * FROM kyc_requests WHERE id=?",(rid,)).fetchone()

def review_kyc(rid:int, status:str, reason='', actor='admin'):
    with conn() as c:
        req=c.execute("SELECT * FROM kyc_requests WHERE id=?",(rid,)).fetchone()
        if not req: return None
        c.execute("UPDATE kyc_requests SET status=?, reject_reason=?, reviewed_at=? WHERE id=?",(status,reason,now(),rid))
        if status=='مقبول':
            c.execute("UPDATE users SET is_active=1, kyc_status='مقبول' WHERE telegram_id=?",(req['telegram_id'],))
            add_notification_tx(c,req['telegram_id'],'تم قبول التوثيق','حسابك أصبح مفعلاً ويمكنك استخدام خدمات TrustPay.')
        else:
            c.execute("UPDATE users SET kyc_status='مرفوض' WHERE telegram_id=?",(req['telegram_id'],))
            add_notification_tx(c,req['telegram_id'],'تم رفض التوثيق',reason or 'يرجى التواصل مع الدعم.')
        c.execute("INSERT INTO audit_logs(actor,action,target,created_at) VALUES(?,?,?,?)",(actor,status,req['request_no'],now()))
        return req

def create_deposit(tid, amount, currency, platform, destination, payment_method_id, proof):
    no=rand_no('DEP')
    with conn() as c:
        c.execute("INSERT INTO deposit_orders(order_no,telegram_id,amount_usdt,currency,platform,destination,payment_method_id,proof,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(no,tid,amount,currency,platform,destination,payment_method_id,proof,now()))
        add_notification_tx(c,tid,'طلب إيداع قيد المراجعة',f'رقم الطلب: {no}')
    return no

def create_withdraw(tid, amount, currency, local_receiver, proof, txid=''):
    no=rand_no('WDR')
    with conn() as c:
        c.execute("INSERT INTO withdraw_orders(order_no,telegram_id,amount_usdt,currency,local_receiver,proof,usdt_txid,created_at) VALUES(?,?,?,?,?,?,?,?)",(no,tid,amount,currency,local_receiver,proof,txid,now()))
        add_notification_tx(c,tid,'طلب سحب قيد المراجعة',f'رقم الطلب: {no}')
    return no

def list_deposits():
    with conn() as c: return c.execute("SELECT d.*, p.name pay_name, p.account_name FROM deposit_orders d LEFT JOIN payment_methods p ON d.payment_method_id=p.id ORDER BY d.id DESC LIMIT 200").fetchall()

def list_withdraws():
    with conn() as c: return c.execute("SELECT * FROM withdraw_orders ORDER BY id DESC LIMIT 200").fetchall()

def my_deposits(tid):
    with conn() as c: return c.execute("SELECT * FROM deposit_orders WHERE telegram_id=? ORDER BY id DESC LIMIT 50",(tid,)).fetchall()

def my_withdraws(tid):
    with conn() as c: return c.execute("SELECT * FROM withdraw_orders WHERE telegram_id=? ORDER BY id DESC LIMIT 50",(tid,)).fetchall()

def review_deposit(oid,status,note='',actor='admin'):
    with conn() as c:
        o=c.execute("SELECT * FROM deposit_orders WHERE id=?",(oid,)).fetchone()
        if not o: return None
        c.execute("UPDATE deposit_orders SET status=?, admin_note=?, reviewed_at=? WHERE id=?",(status,note,now(),oid))
        if status=='مكتمل':
            c.execute("UPDATE users SET points=points+10 WHERE telegram_id=?",(o['telegram_id'],))
            c.execute("INSERT INTO transactions(telegram_id,tx_type,amount_usdt,description,related_order,created_at) VALUES(?,?,?,?,?,?)",(o['telegram_id'],'إيداع',o['amount_usdt'],'إيداع USDT منفذ',o['order_no'],now()))
            add_notification_tx(c,o['telegram_id'],'تم تنفيذ الإيداع',f"طلبك {o['order_no']} اكتمل بنجاح.")
        else: add_notification_tx(c,o['telegram_id'],'تم رفض الإيداع',note or 'يرجى التواصل مع الدعم.')
        c.execute("INSERT INTO audit_logs(actor,action,target,created_at) VALUES(?,?,?,?)",(actor,status,o['order_no'],now()))
        return o

def review_withdraw(oid,status,note='',actor='admin'):
    with conn() as c:
        o=c.execute("SELECT * FROM withdraw_orders WHERE id=?",(oid,)).fetchone()
        if not o: return None
        c.execute("UPDATE withdraw_orders SET status=?, admin_note=?, reviewed_at=? WHERE id=?",(status,note,now(),oid))
        if status=='مكتمل':
            c.execute("UPDATE users SET points=points+10 WHERE telegram_id=?",(o['telegram_id'],))
            c.execute("INSERT INTO transactions(telegram_id,tx_type,amount_usdt,description,related_order,created_at) VALUES(?,?,?,?,?,?)",(o['telegram_id'],'سحب',o['amount_usdt'],'سحب منفذ',o['order_no'],now()))
            add_notification_tx(c,o['telegram_id'],'تم تنفيذ السحب',f"طلبك {o['order_no']} اكتمل بنجاح.")
        else: add_notification_tx(c,o['telegram_id'],'تم رفض السحب',note or 'يرجى التواصل مع الدعم.')
        c.execute("INSERT INTO audit_logs(actor,action,target,created_at) VALUES(?,?,?,?)",(actor,status,o['order_no'],now()))
        return o

def my_transactions(tid):
    with conn() as c: return c.execute("SELECT * FROM transactions WHERE telegram_id=? ORDER BY id DESC LIMIT 100",(tid,)).fetchall()

def add_notification_tx(c,tid,title,body):
    c.execute("INSERT INTO notifications(telegram_id,title,body,created_at) VALUES(?,?,?,?)",(tid,title,body,now()))

def notifications(tid):
    with conn() as c: return c.execute("SELECT * FROM notifications WHERE telegram_id=? ORDER BY id DESC LIMIT 50",(tid,)).fetchall()

def add_ticket(tid:int, msg:str, attachment=''):
    with conn() as c:
        c.execute("INSERT INTO tickets(telegram_id,message,attachment,created_at,updated_at) VALUES(?,?,?,?,?)",(tid,msg,attachment,now(),now()))
        add_notification_tx(c,tid,'تم فتح تذكرة دعم','سيتم الرد عليك قريباً.')

def list_tickets():
    with conn() as c: return c.execute("SELECT * FROM tickets ORDER BY id DESC LIMIT 200").fetchall()

def reply_ticket(tid, reply, status='مغلقة'):
    with conn() as c:
        t=c.execute("SELECT * FROM tickets WHERE id=?",(tid,)).fetchone()
        if not t: return None
        c.execute("UPDATE tickets SET admin_reply=?, status=?, updated_at=? WHERE id=?",(reply,status,now(),tid))
        add_notification_tx(c,t['telegram_id'],'رد جديد على تذكرتك',reply)
        return t

def referrals(tid):
    with conn() as c: return c.execute("SELECT * FROM referrals WHERE referrer_id=? ORDER BY id DESC",(tid,)).fetchall()

def list_ops():
    # compatibility
    with conn() as c: return c.execute("SELECT * FROM operations ORDER BY id DESC LIMIT 200").fetchall()

def create_operation(tid:int, op_type:str, amount:float, network='', wallet='', proof=''):
    with conn() as c: c.execute("INSERT INTO operations(telegram_id,op_type,amount,network,wallet,proof,created_at) VALUES(?,?,?,?,?,?,?)",(tid,op_type,amount,network,wallet,proof,now()))
