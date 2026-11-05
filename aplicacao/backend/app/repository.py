"""SQLite com transações explícitas e catálogo imutável de vínculos."""
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from .schemas import IDS


def now():
    return datetime.now(timezone.utc).isoformat()


def encode(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,allow_nan=False)


class Connection(sqlite3.Connection):
    def __exit__(self,*args):
        try: return super().__exit__(*args)
        finally: self.close()


class Repository:
    def __init__(self,root):
        self.root=root
        self.base_path=root/'codex/base_padronizada.json'
        self.base_bytes=self.base_path.read_bytes()
        self.base=json.loads(self.base_bytes)
        self.digest=hashlib.sha256(self.base_bytes).hexdigest()
        self.db=root/'codex/dados/runtime/pmisb.sqlite'

    def connect(self,write=False):
        if write:
            conn=sqlite3.connect(self.db,timeout=15,factory=Connection)
        else:
            conn=sqlite3.connect(self.db.resolve().as_uri()+'?mode=ro',uri=True,timeout=15,factory=Connection)
        conn.execute('PRAGMA foreign_keys=ON')
        return conn

    def initialize(self):
        self.db.parent.mkdir(parents=True,exist_ok=True)
        snapshot=self.root/'codex/dados/snapshots'/self.digest[:16]
        snapshot.mkdir(parents=True,exist_ok=True)
        for name,data in [('base_padronizada.json',self.base_bytes),('manifesto.json',encode({'sha256':self.digest,'origem':'codex/base_padronizada.json','versao':1}).encode())]:
            path=snapshot/name
            if not path.exists():
                path.write_bytes(data)
        with self.connect(True) as c:
            c.executescript('''
                CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS origins(kind TEXT NOT NULL,id TEXT NOT NULL,PRIMARY KEY(kind,id));
                CREATE TABLE IF NOT EXISTS records(kind TEXT NOT NULL,id TEXT NOT NULL,revision INTEGER NOT NULL,data TEXT NOT NULL,PRIMARY KEY(kind,id));
                CREATE TABLE IF NOT EXISTS links(kind TEXT NOT NULL,id TEXT NOT NULL,origin_kind TEXT NOT NULL,origin_id TEXT NOT NULL,
                    FOREIGN KEY(kind,id) REFERENCES records(kind,id), FOREIGN KEY(origin_kind,origin_id) REFERENCES origins(kind,id));
                CREATE TABLE IF NOT EXISTS history(sequence INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT NOT NULL,id TEXT NOT NULL,operation TEXT NOT NULL,at TEXT NOT NULL,before_json TEXT,after_json TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS evidence(id TEXT PRIMARY KEY,name TEXT NOT NULL,sha256 TEXT NOT NULL,file TEXT NOT NULL);
            ''')
            existing=c.execute("SELECT value FROM metadata WHERE key='base_sha256'").fetchone()
            if existing and existing[0]!=self.digest:
                raise ValueError('Snapshot do banco difere da base; restaure a versão correspondente.')
            c.execute("INSERT OR IGNORE INTO metadata VALUES('base_sha256',?)",(self.digest,))
            c.execute("INSERT OR IGNORE INTO metadata VALUES('revision','0')")
            for key,idfield in [('indicadores_principais','indicador_id'),('indicadores_desempenho','indicador_id'),('metas','meta_id'),('acoes_previstas','acao_id'),('projetos','projeto_id'),('investimentos_previstos','investimento_id')]:
                c.executemany('INSERT OR IGNORE INTO origins VALUES (?,?)',[(key,r[idfield]) for r in self.base[key]])
            c.executemany('INSERT OR IGNORE INTO origins VALUES (?,?)',[('linhas_investimento',r['linha_id']) for r in self.base['investimentos_previstos']])

    def revision(self,c=None):
        if not self.db.exists(): return 0
        if c is not None: return int(c.execute("SELECT value FROM metadata WHERE key='revision'").fetchone()[0])
        with self.connect() as connection: return self.revision(connection)

    @contextmanager
    def transaction(self):
        c=self.connect(True)
        try:
            c.execute('BEGIN IMMEDIATE')
            yield c
            c.commit()
        except BaseException:
            c.rollback()
            raise
        finally:
            c.close()

    def records(self,kind,c=None):
        if not self.db.exists(): return []
        if c is not None:
            return [json.loads(r[0]) for r in c.execute('SELECT data FROM records WHERE kind=? ORDER BY rowid',(kind,))]
        with self.connect() as connection: return self.records(kind,connection)

    def state(self):
        result={k:self.records(k) for k in IDS}
        result['historico']=[]
        if self.db.exists():
            with self.connect() as c:
                result['historico']=[dict(sequencia=s,tipo=k,id=i,operacao=o,data_registro=t,antes=json.loads(b) if b else None,depois=json.loads(a)) for s,k,i,o,t,b,a in c.execute('SELECT * FROM history ORDER BY sequence')]
        return result

    def put(self,c,kind,record,links=()):
        id=record[IDS[kind]]
        old=c.execute('SELECT revision,data FROM records WHERE kind=? AND id=?',(kind,id)).fetchone()
        revision=old[0]+1 if old else 1
        saved={**record,'revisao':revision}
        c.execute('INSERT INTO records VALUES(?,?,?,?) ON CONFLICT(kind,id) DO UPDATE SET revision=excluded.revision,data=excluded.data',(kind,id,revision,encode(saved)))
        c.execute('DELETE FROM links WHERE kind=? AND id=?',(kind,id))
        c.executemany('INSERT INTO links VALUES(?,?,?,?)',[(kind,id,k,v) for k,v in links])
        c.execute('INSERT INTO history(kind,id,operation,at,before_json,after_json) VALUES(?,?,?,?,?,?)',(kind,id,'retificacao' if old else 'inclusao',now(),old[1] if old else None,encode(saved)))
        c.execute("UPDATE metadata SET value=CAST(value AS INTEGER)+1 WHERE key='revision'")
        return saved
