r"""Demo SQL chay that bang sqlite3 - hoc kem docs/HOC_SQL.md.

Bang mau dung XUYEN SUOT ca bai giang: phong_ban, nhan_vien, doanh_so.
Database nam trong BO NHO (:memory:), khong dong gi vao dia -> go sai bao nhieu cung duoc,
tat di chay lai la sach.

Cach chay (tu thu muc goc du an):
  venv\Scripts\python.exe docs\hoc\demo_sql.py             # TUONG TAC: tu go SQL, xem ket qua ngay
  venv\Scripts\python.exe docs\hoc\demo_sql.py --demo      # chay lai TAT CA vi du trong bai giang
  venv\Scripts\python.exe docs\hoc\demo_sql.py --demo 8    # chi chay vi du muc 8 (window function)
  venv\Scripts\python.exe docs\hoc\demo_sql.py --baitap    # loi giai 10 bai tap cuoi bai
  venv\Scripts\python.exe docs\hoc\demo_sql.py --baitap 7  # loi giai bai 7
  venv\Scripts\python.exe docs\hoc\demo_sql.py --index     # DO THOI GIAN 200k dong: truoc/sau khi tao index

Chi dung thu vien chuan (sqlite3). Chu trong file nay khong dau de khong loi font console Windows.
"""

import argparse
import sqlite3
import textwrap
import time

NGAN = "-" * 92
DAI = "=" * 92

# --------------------------------------------------------------------------------------
# BANG MAU - moi vi du trong bai giang deu chay tren dung bo du lieu nay
# --------------------------------------------------------------------------------------
SCHEMA_SQL = """
DROP TABLE IF EXISTS doanh_so;
DROP TABLE IF EXISTS nhan_vien;
DROP TABLE IF EXISTS phong_ban;

CREATE TABLE phong_ban (
    phong_id  INTEGER PRIMARY KEY,
    ten_phong TEXT NOT NULL,
    dia_diem  TEXT NOT NULL
);

CREATE TABLE nhan_vien (
    nv_id      INTEGER PRIMARY KEY,
    ho_ten     TEXT NOT NULL,
    phong_id   INTEGER REFERENCES phong_ban(phong_id),  -- co the NULL: chua phan phong
    luong      INTEGER,                                 -- trieu VND/thang, co the NULL
    ngay_vao   TEXT NOT NULL,                           -- 'YYYY-MM-DD'
    quan_ly_id INTEGER REFERENCES nhan_vien(nv_id)      -- NULL = khong co sep
);

CREATE TABLE doanh_so (
    ds_id     INTEGER PRIMARY KEY,
    nv_id     INTEGER NOT NULL REFERENCES nhan_vien(nv_id),
    thang     TEXT NOT NULL,      -- 'YYYY-MM'
    doanh_thu INTEGER NOT NULL    -- trieu VND
);

INSERT INTO phong_ban (phong_id, ten_phong, dia_diem) VALUES
    (10, 'Ky thuat',   'Ha Noi'),
    (20, 'Kinh doanh', 'Ho Chi Minh'),
    (30, 'Nhan su',    'Ha Noi'),
    (40, 'Nghien cuu', 'Da Nang');      -- phong nay CHUA co nhan vien nao

INSERT INTO nhan_vien (nv_id, ho_ten, phong_id, luong, ngay_vao, quan_ly_id) VALUES
    (1, 'An',   10,   25, '2021-03-01', NULL),
    (2, 'Binh', 10,   18, '2022-06-15', 1),
    (3, 'Chi',  10,   18, '2023-01-10', 1),
    (4, 'Dung', 20,   22, '2020-11-20', 1),
    (5, 'Ha',   20,   15, '2023-07-01', 4),
    (6, 'Khoa', 30,   12, '2024-02-05', 1),
    (7, 'Linh', 30, NULL, '2024-09-01', 6),   -- thu viec: CHUA chot luong -> NULL
    (8, 'Minh', NULL, 14, '2025-01-15', 1);   -- CHUA phan phong -> phong_id NULL

INSERT INTO doanh_so (ds_id, nv_id, thang, doanh_thu) VALUES
    (1,  2, '2025-01',  60), (2,  2, '2025-02', 150), (3,  2, '2025-03',  90), (4,  2, '2025-04',  70),
    (5,  4, '2025-01', 120), (6,  4, '2025-02', 150), (7,  4, '2025-03',  90), (8,  4, '2025-04', 200),
    (9,  5, '2025-01',  80), (10, 5, '2025-02',  95), (11, 5, '2025-03', 130), (12, 5, '2025-04', 110);
"""


def tao_db():
    """Tao database trong bo nho voi du lieu mau.

    isolation_level=None = che do autocommit: minh tu go BEGIN/COMMIT/ROLLBACK
    thi no moi mo transaction -> hoc muc 11 cho ro rang.
    """
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_SQL)
    return conn


# --------------------------------------------------------------------------------------
# In ket qua duoi dang bang ASCII
# --------------------------------------------------------------------------------------
def _o(v):
    if v is None:
        return "NULL"
    if isinstance(v, float):
        return f"{v:.4f}".rstrip("0").rstrip(".")
    return str(v)


def in_bang(cur, max_dong=30):
    if cur.description is None:
        print("  OK (cau lenh khong tra ve du lieu)")
        return
    cot = [d[0] for d in cur.description]
    dong = cur.fetchall()
    van = [[_o(v) for v in d] for d in dong]
    phai = [
        any(isinstance(d[i], (int, float)) for d in dong)
        and all(d[i] is None or isinstance(d[i], (int, float)) for d in dong)
        for i in range(len(cot))
    ]
    rong = [max([len(cot[i])] + [len(r[i]) for r in van]) for i in range(len(cot))]
    ke = "  +" + "+".join("-" * (w + 2) for w in rong) + "+"
    print(ke)
    print("  | " + " | ".join(cot[i].ljust(rong[i]) for i in range(len(cot))) + " |")
    print(ke)
    for r in van[:max_dong]:
        print("  | " + " | ".join(
            r[i].rjust(rong[i]) if phai[i] else r[i].ljust(rong[i]) for i in range(len(cot))
        ) + " |")
    print(ke)
    if len(van) > max_dong:
        print(f"  ... con {len(van) - max_dong} dong nua")
    print(f"  ({len(van)} dong)")


def chay_sql(conn, sql):
    """Chay 1 hoac nhieu cau lenh, in ket qua cua tung cau."""
    for cau in [c.strip() for c in sql.split(";") if c.strip()]:
        try:
            in_bang(conn.execute(cau))
        except sqlite3.Error as e:
            print(f"  LOI SQL: {e}")


def chay_vi_du(conn, ma, tieu_de, sql, ghi_chu=""):
    tieu = f"--- Vi du {ma}: {tieu_de} "
    print("\n" + tieu + "-" * max(3, 92 - len(tieu)))
    for line in textwrap.dedent(sql).strip().splitlines():
        print("    " + line)
    print()
    chay_sql(conn, sql)
    if ghi_chu:
        for line in textwrap.wrap(ghi_chu, 88):
            print("  => " + line)


# --------------------------------------------------------------------------------------
# VI DU - ma so trung voi muc trong HOC_SQL.md
# --------------------------------------------------------------------------------------
VI_DU = [
    # ---------------- 3. SELECT / WHERE / ORDER BY ----------------
    ("3.1", "Xem toan bo mot bang", """
        SELECT * FROM nhan_vien;
    """, "SELECT * = lay het cot. Di lam thi hiem khi dung *, luon liet ke cot can dung."),

    ("3.2", "Chon cot, tinh toan, dat ten lai (alias)", """
        SELECT ho_ten, luong, luong * 12 AS luong_nam
        FROM nhan_vien;
    """, "Linh co luong NULL -> NULL * 12 van la NULL, khong phai 0."),

    ("3.3", "WHERE: loc dong", """
        SELECT ho_ten, phong_id, luong
        FROM nhan_vien
        WHERE phong_id = 10 AND luong >= 18;
    """, "AND/OR/NOT ket hop duoc; nen dat ngoac khi tron AND voi OR."),

    ("3.4", "IN, BETWEEN, LIKE", """
        SELECT ho_ten, phong_id, luong FROM nhan_vien WHERE phong_id IN (10, 30);
        SELECT ho_ten, luong FROM nhan_vien WHERE luong BETWEEN 15 AND 22;
        SELECT ho_ten FROM nhan_vien WHERE ho_ten LIKE '%h%';
    """, "BETWEEN bao gom ca hai dau. LIKE: % = nhieu ky tu bat ky, _ = dung 1 ky tu."),

    ("3.5", "ORDER BY nhieu cot + LIMIT", """
        SELECT ho_ten, phong_id, luong
        FROM nhan_vien
        ORDER BY luong DESC, ho_ten ASC
        LIMIT 3;
    """, "Sap giam dan theo luong, bang nhau thi sap theo ten. LIMIT lay 3 dong dau."),

    ("3.6", "DISTINCT: bo trung", """
        SELECT DISTINCT phong_id FROM nhan_vien ORDER BY phong_id;
    """, "DISTINCT coi cac NULL la GIONG NHAU nen NULL chi hien 1 lan (khac han toan tu =)."),

    ("3.7", "CASE WHEN: if/else trong SQL", """
        SELECT ho_ten, luong,
               CASE WHEN luong IS NULL THEN 'chua chot'
                    WHEN luong >= 20   THEN 'cao'
                    WHEN luong >= 15   THEN 'trung binh'
                    ELSE 'thap'
               END AS muc_luong
        FROM nhan_vien
        ORDER BY luong DESC;
    """, "CASE xet lan luot tu tren xuong, gap dieu kien dung dau tien la dung lai."),

    ("3.8", "Thu tu thuc thi: alias dung duoc o dau?", """
        SELECT ho_ten, luong * 12 AS luong_nam FROM nhan_vien ORDER BY luong_nam DESC;
        SELECT ho_ten, luong * 12 AS luong_nam FROM nhan_vien WHERE luong_nam > 200;
    """, "ORDER BY chay SAU SELECT nen dung duoc alias. WHERE chay TRUOC SELECT nen theo chuan la KHONG "
         "duoc - SQLite de dai cho qua, nhung PostgreSQL/MySQL bao loi. Khong nen dua vao su de dai do."),

    # ---------------- 4. JOIN ----------------
    ("4.1", "INNER JOIN: chi giu cap KHOP nhau", """
        SELECT nv.nv_id, nv.ho_ten, nv.phong_id, pb.ten_phong
        FROM nhan_vien nv
        JOIN phong_ban pb ON nv.phong_id = pb.phong_id
        ORDER BY nv.nv_id;
    """, "Minh (phong_id NULL) BIEN MAT, phong 40 (khong ai) cung bien mat. 7 dong chu khong phai 8."),

    ("4.2", "LEFT JOIN: giu HET bang ben trai", """
        SELECT nv.nv_id, nv.ho_ten, nv.phong_id, pb.ten_phong
        FROM nhan_vien nv
        LEFT JOIN phong_ban pb ON nv.phong_id = pb.phong_id
        ORDER BY nv.nv_id;
    """, "Minh o lai, cac cot ben phai duoc do NULL vao. Day la kieu JOIN dung nhieu nhat di lam."),

    ("4.3", "Anti-join: phong nao KHONG co nhan vien", """
        SELECT pb.phong_id, pb.ten_phong
        FROM phong_ban pb
        LEFT JOIN nhan_vien nv ON pb.phong_id = nv.phong_id
        WHERE nv.nv_id IS NULL;
    """, "Mau LEFT JOIN + IS NULL tra loi cau 'ben nay co ma ben kia khong co' - rat hay bi hoi."),

    ("4.4", "RIGHT JOIN va FULL OUTER JOIN", """
        SELECT pb.ten_phong, nv.ho_ten
        FROM nhan_vien nv RIGHT JOIN phong_ban pb ON nv.phong_id = pb.phong_id
        ORDER BY pb.phong_id;

        SELECT nv.ho_ten, pb.ten_phong
        FROM nhan_vien nv FULL OUTER JOIN phong_ban pb ON nv.phong_id = pb.phong_id
        ORDER BY nv.nv_id;
    """, "RIGHT = LEFT viet nguoc, doi cho hai bang la thanh LEFT. FULL giu ca hai ben: 8 nhan vien "
         "+ phong 40 = 9 dong. SQLite chi ho tro RIGHT/FULL tu ban 3.39 tro len."),

    ("4.5", "SELF JOIN: bang tu noi voi chinh no", """
        SELECT nv.ho_ten AS nhan_vien, sep.ho_ten AS quan_ly
        FROM nhan_vien nv
        LEFT JOIN nhan_vien sep ON nv.quan_ly_id = sep.nv_id
        ORDER BY nv.nv_id;
    """, "Cung mot bang, hai alias khac nhau = hai 'ban sao'. LEFT de An (khong co sep) khong bi mat."),

    ("4.6", "JOIN NHAN dong len - vi sao hinh Venn sai", """
        SELECT (SELECT COUNT(*) FROM nhan_vien) AS so_nhan_vien,
               (SELECT COUNT(*) FROM doanh_so)  AS so_dong_doanh_so,
               (SELECT COUNT(*) FROM nhan_vien nv JOIN doanh_so ds ON nv.nv_id = ds.nv_id)
                   AS so_dong_sau_join;
    """, "3 nhan vien khop voi 12 dong doanh so -> ket qua 12 dong, moi nhan vien lap lai 4 lan. "
         "Hinh Venn khong the ve duoc chuyen 'mot dong nhan ra bon dong'."),

    ("4.7", "CROSS JOIN: ghep tat ca voi tat ca", """
        SELECT COUNT(*) AS so_dong FROM nhan_vien CROSS JOIN phong_ban;
    """, "8 x 4 = 32 dong. Quen dieu kien ON chinh la vo tinh tao CROSS JOIN -> query no ra khong lo."),

    ("4.8", "BAY KINH DIEN: dieu kien loc dat o WHERE hay o ON?", """
        SELECT pb.ten_phong, nv.ho_ten
        FROM phong_ban pb LEFT JOIN nhan_vien nv ON pb.phong_id = nv.phong_id
        WHERE nv.luong >= 18
        ORDER BY pb.phong_id;

        SELECT pb.ten_phong, nv.ho_ten
        FROM phong_ban pb LEFT JOIN nhan_vien nv ON pb.phong_id = nv.phong_id AND nv.luong >= 18
        ORDER BY pb.phong_id;
    """, "Cau tren: WHERE chay SAU khi da do NULL vao, ma NULL >= 18 khong dung -> LEFT JOIN bi bien "
         "thanh INNER JOIN, mat phong 30 va 40. Cau duoi: dieu kien nam trong ON nen phong nao cung con."),

    ("4.9", "JOIN ba bang", """
        SELECT pb.ten_phong, nv.ho_ten, ds.thang, ds.doanh_thu
        FROM doanh_so ds
        JOIN nhan_vien nv ON ds.nv_id = nv.nv_id
        JOIN phong_ban pb ON nv.phong_id = pb.phong_id
        WHERE ds.thang = '2025-02'
        ORDER BY ds.doanh_thu DESC;
    """, "Noi lan luot tung cap. Neu ten cot hai ben giong het nhau co the viet gon: USING (phong_id)."),

    # ---------------- 5. GROUP BY / HAVING ----------------
    ("5.1", "Ham gom nhom tren ca bang", """
        SELECT COUNT(*)             AS so_dong,
               COUNT(luong)         AS co_luong,
               SUM(luong)           AS tong_luong,
               ROUND(AVG(luong), 2) AS luong_tb,
               MIN(luong)           AS thap_nhat,
               MAX(luong)           AS cao_nhat
        FROM nhan_vien;
    """, "COUNT(*) = 8 dem ca dong co NULL; COUNT(luong) = 7 chi dem dong CO gia tri. "
         "AVG chia cho 7 chu khong phai 8 - cho nay phong van rat hay hoi."),

    ("5.2", "GROUP BY: gom dong thanh nhom", """
        SELECT phong_id, COUNT(*) AS so_nv, ROUND(AVG(luong), 1) AS luong_tb
        FROM nhan_vien
        GROUP BY phong_id
        ORDER BY phong_id;
    """, "Moi gia tri phong_id thanh 1 dong ket qua. Cac dong phong_id NULL duoc gom chung mot nhom."),

    ("5.3", "GROUP BY + JOIN de lay ten phong (giu ca phong rong)", """
        SELECT pb.ten_phong,
               COUNT(nv.nv_id) AS so_nv,
               COALESCE(SUM(nv.luong), 0) AS tong_luong
        FROM phong_ban pb
        LEFT JOIN nhan_vien nv ON pb.phong_id = nv.phong_id
        GROUP BY pb.phong_id, pb.ten_phong
        ORDER BY so_nv DESC;
    """, "Phai dung COUNT(nv.nv_id) chu KHONG dung COUNT(*): phong 40 khong co ai, COUNT(*) ra 1 "
         "(dem dong NULL do LEFT JOIN sinh ra) con COUNT(cot) ra dung 0."),

    ("5.4", "HAVING: loc SAU khi gom nhom", """
        SELECT phong_id, COUNT(*) AS so_nv, ROUND(AVG(luong), 1) AS luong_tb
        FROM nhan_vien
        GROUP BY phong_id
        HAVING COUNT(*) >= 2
        ORDER BY so_nv DESC;
    """, "WHERE loc TUNG DONG truoc khi gom; HAVING loc TUNG NHOM sau khi gom. "
         "Viet WHERE COUNT(*) >= 2 se bao loi."),

    ("5.5", "Du bo: WHERE + GROUP BY + HAVING + ORDER BY", """
        SELECT phong_id, COUNT(*) AS so_nv, SUM(luong) AS tong_luong
        FROM nhan_vien
        WHERE ngay_vao < '2024-01-01'
        GROUP BY phong_id
        HAVING SUM(luong) > 30
        ORDER BY tong_luong DESC;
    """, "Doc theo dung thu tu may chay: FROM -> WHERE -> GROUP BY -> HAVING -> SELECT -> ORDER BY."),

    ("5.6", "COUNT(*) / COUNT(cot) / COUNT(DISTINCT cot)", """
        SELECT COUNT(*) AS tat_ca,
               COUNT(phong_id) AS co_phong,
               COUNT(DISTINCT phong_id) AS so_phong_khac_nhau
        FROM nhan_vien;
    """, "8 dong, 7 dong co phong, 3 phong khac nhau (DISTINCT cung bo qua NULL)."),

    ("5.7", "GROUP_CONCAT: gom chuoi trong nhom", """
        SELECT phong_id, GROUP_CONCAT(ho_ten, ', ') AS danh_sach
        FROM nhan_vien
        GROUP BY phong_id;
    """, "MySQL: GROUP_CONCAT, PostgreSQL: STRING_AGG - y nghia nhu nhau."),

    ("5.8", "BAY: cot khong nam trong GROUP BY", """
        SELECT phong_id, ho_ten, MAX(luong) AS luong_cao_nhat
        FROM nhan_vien
        GROUP BY phong_id;
    """, "SQLite/MySQL cu cho chay va tra ve mot ho_ten (SQLite tra dung dong co MAX, khong dam bao "
         "o he khac). PostgreSQL bao loi thang. Muon chac dung -> window function, muc 8.4."),

    ("5.9", "GROUP BY theo bieu thuc", """
        SELECT substr(ngay_vao, 1, 4) AS nam_vao, COUNT(*) AS so_nguoi
        FROM nhan_vien
        GROUP BY substr(ngay_vao, 1, 4)
        ORDER BY nam_vao;
    """, "Gom nhom theo ket qua tinh toan, khong nhat thiet phai la mot cot co san."),

    # ---------------- 6. SUBQUERY ----------------
    ("6.1", "Subquery tra ve MOT gia tri (scalar)", """
        SELECT ho_ten, luong
        FROM nhan_vien
        WHERE luong > (SELECT AVG(luong) FROM nhan_vien)
        ORDER BY luong DESC;
    """, "Khong the viet WHERE luong > AVG(luong) - phai boc thanh subquery."),

    ("6.2", "Subquery voi IN", """
        SELECT ho_ten, phong_id
        FROM nhan_vien
        WHERE phong_id IN (SELECT phong_id FROM phong_ban WHERE dia_diem = 'Ha Noi');
    """, "Subquery tra ve mot DANH SACH gia tri de doi chieu."),

    ("6.3", "BAY NOT IN + NULL (cau hoi phong van kinh dien)", """
        SELECT phong_id, ten_phong
        FROM phong_ban
        WHERE phong_id NOT IN (SELECT phong_id FROM nhan_vien);
    """, "Dung ra phai ra phong 40, nhung ket qua LA RONG! Vi danh sach ben trong co Minh voi "
         "phong_id = NULL, ma 'x NOT IN (..., NULL)' khong bao gio dung duoc. Cach chua: 6.4 va 6.5."),

    ("6.4", "Chua bay NOT IN: loc NULL ra truoc", """
        SELECT phong_id, ten_phong
        FROM phong_ban
        WHERE phong_id NOT IN (SELECT phong_id FROM nhan_vien WHERE phong_id IS NOT NULL);
    """, "Them mot dieu kien IS NOT NULL la chay dung."),

    ("6.5", "Cach an toan hon: NOT EXISTS", """
        SELECT pb.phong_id, pb.ten_phong
        FROM phong_ban pb
        WHERE NOT EXISTS (SELECT 1 FROM nhan_vien nv WHERE nv.phong_id = pb.phong_id);
    """, "NOT EXISTS khong dinh bay NULL. Di lam nen uu tien NOT EXISTS hon NOT IN."),

    ("6.6", "EXISTS: chi can co it nhat mot dong", """
        SELECT nv.ho_ten
        FROM nhan_vien nv
        WHERE EXISTS (SELECT 1 FROM doanh_so ds WHERE ds.nv_id = nv.nv_id AND ds.doanh_thu > 100);
    """, "EXISTS chi tra ve dung/sai, tim thay dong dau tien la dung ngay - khong quan tam SELECT gi ben trong."),

    ("6.7", "Subquery TUONG QUAN (correlated)", """
        SELECT nv.ho_ten, nv.phong_id, nv.luong
        FROM nhan_vien nv
        WHERE nv.luong > (SELECT AVG(n2.luong) FROM nhan_vien n2 WHERE n2.phong_id = nv.phong_id);
    """, "Subquery nhac den nv o ngoai -> voi MOI dong ngoai no tinh lai mot lan. Manh nhung cham "
         "khi bang lon; thuong thay bang window function (muc 8.2)."),

    ("6.8", "Subquery o FROM (bang dan xuat)", """
        SELECT t.phong_id, ROUND(t.luong_tb, 1) AS luong_tb
        FROM (SELECT phong_id, AVG(luong) AS luong_tb FROM nhan_vien GROUP BY phong_id) AS t
        WHERE t.luong_tb > 15;
    """, "Coi ket qua mot query nhu mot bang tam. Muc 7 se viet lai cho de doc hon bang CTE."),

    ("6.9", "Luong cao THU HAI - cau kinh dien", """
        SELECT MAX(luong) AS luong_thu_2
        FROM nhan_vien
        WHERE luong < (SELECT MAX(luong) FROM nhan_vien);
    """, "Meo: 'lon nhat trong nhung cai nho hon cai lon nhat'. Neu khong co ai thi ra NULL chu khong "
         "bao loi - nho noi y nay khi tra loi phong van."),

    # ---------------- 7. CTE ----------------
    ("7.1", "WITH: dat ten cho mot buoc trung gian", """
        WITH tb_phong AS (
            SELECT phong_id, AVG(luong) AS luong_tb
            FROM nhan_vien
            GROUP BY phong_id
        )
        SELECT phong_id, ROUND(luong_tb, 1) AS luong_tb
        FROM tb_phong
        WHERE luong_tb > 15;
    """, "Y het vi du 6.8 nhung doc tu tren xuong nhu doc doan van, khong phai boc ngoac nguoc."),

    ("7.2", "Nhieu CTE noi tiep nhau thanh day chuyen", """
        WITH ds_theo_nv AS (
            SELECT nv_id, SUM(doanh_thu) AS tong_ds
            FROM doanh_so
            GROUP BY nv_id
        ),
        co_ten AS (
            SELECT nv.ho_ten, nv.phong_id, d.tong_ds
            FROM ds_theo_nv d
            JOIN nhan_vien nv ON nv.nv_id = d.nv_id
        )
        SELECT ho_ten, phong_id, tong_ds
        FROM co_ten
        ORDER BY tong_ds DESC;
    """, "CTE sau dung duoc CTE truoc. Query dai chia thanh 3-4 buoc thi de doc va de sua hon nhieu."),

    ("7.3", "CTE DE QUY: dung cay quan ly", """
        WITH RECURSIVE cay AS (
            SELECT nv_id, ho_ten, quan_ly_id, 1 AS cap, ho_ten AS duong_di
            FROM nhan_vien
            WHERE quan_ly_id IS NULL
            UNION ALL
            SELECT nv.nv_id, nv.ho_ten, nv.quan_ly_id, cay.cap + 1, cay.duong_di || ' > ' || nv.ho_ten
            FROM nhan_vien nv
            JOIN cay ON nv.quan_ly_id = cay.nv_id
        )
        SELECT cap, ho_ten, duong_di FROM cay ORDER BY duong_di;
    """, "Phan tren UNION ALL = diem xuat phat (sep tong). Phan duoi = buoc lap: lay nhung nguoi co sep "
         "vua tim duoc o vong truoc. Dung khi khong tim them duoc ai."),

    ("7.4", "CTE de quy sinh day so (de tao du lieu test)", """
        WITH RECURSIVE dem(n) AS (
            SELECT 1
            UNION ALL
            SELECT n + 1 FROM dem WHERE n < 10
        )
        SELECT n, n * n AS binh_phuong FROM dem;
    """, "Meo rat huu ich: sinh vai tram nghin dong gia de tu do toc do query (xem che do --index)."),

    # ---------------- 8. WINDOW FUNCTION ----------------
    ("8.1", "GROUP BY gom dong lai - WINDOW thi GIU nguyen dong", """
        SELECT phong_id, ROUND(AVG(luong), 1) AS luong_tb FROM nhan_vien GROUP BY phong_id;

        SELECT ho_ten, phong_id, luong,
               ROUND(AVG(luong) OVER (PARTITION BY phong_id), 1) AS luong_tb_phong
        FROM nhan_vien
        ORDER BY phong_id, luong DESC;
    """, "Cung mot con so trung binh, nhung window dan no CANH TUNG DONG thay vi bop 8 dong xuong 4."),

    ("8.2", "So voi trung binh phong, khong can subquery tuong quan", """
        SELECT ho_ten, phong_id, luong,
               ROUND(luong - AVG(luong) OVER (PARTITION BY phong_id), 1) AS lech_so_voi_phong
        FROM nhan_vien
        WHERE luong IS NOT NULL
        ORDER BY phong_id;
    """, "Viet lai vi du 6.7 bang window - ngan hon va thuong nhanh hon vi chi quet bang mot lan."),

    ("8.3", "ROW_NUMBER vs RANK vs DENSE_RANK (thang 2025-03 co hai nguoi bang diem)", """
        SELECT nv.ho_ten, ds.doanh_thu,
               ROW_NUMBER() OVER (ORDER BY ds.doanh_thu DESC) AS rn,
               RANK()       OVER (ORDER BY ds.doanh_thu DESC) AS rnk,
               DENSE_RANK() OVER (ORDER BY ds.doanh_thu DESC) AS drnk
        FROM doanh_so ds JOIN nhan_vien nv ON nv.nv_id = ds.nv_id
        WHERE ds.thang = '2025-03'
        ORDER BY ds.doanh_thu DESC;
    """, "Binh va Dung cung 90: ROW_NUMBER ep ra 2 va 3 (chon tuy y), RANK cho ca hai hang 2 roi NHAY "
         "sang 4, DENSE_RANK cho ca hai hang 2 roi tiep 3."),

    ("8.4", "Mau TOP-N MOI NHOM (hoi phong van rat nhieu)", """
        WITH xep_hang AS (
            SELECT ho_ten, phong_id, luong,
                   ROW_NUMBER() OVER (PARTITION BY phong_id ORDER BY luong DESC) AS thu_tu
            FROM nhan_vien
            WHERE phong_id IS NOT NULL
        )
        SELECT phong_id, ho_ten, luong, thu_tu
        FROM xep_hang
        WHERE thu_tu <= 2
        ORDER BY phong_id, thu_tu;
    """, "Khong loc thang duoc trong WHERE vi window chay SAU WHERE -> phai boc them mot lop CTE."),

    ("8.5", "LAG: so voi thang truoc", """
        SELECT nv.ho_ten, ds.thang, ds.doanh_thu,
               LAG(ds.doanh_thu) OVER (PARTITION BY ds.nv_id ORDER BY ds.thang) AS thang_truoc,
               ds.doanh_thu - LAG(ds.doanh_thu) OVER (PARTITION BY ds.nv_id ORDER BY ds.thang) AS chenh
        FROM doanh_so ds JOIN nhan_vien nv ON nv.nv_id = ds.nv_id
        ORDER BY nv.ho_ten, ds.thang;
    """, "Thang dau tien khong co thang truoc -> NULL. Muon thay bang 0 thi viet LAG(x, 1, 0)."),

    ("8.6", "LEAD: ngo sang thang sau", """
        SELECT nv.ho_ten, ds.thang, ds.doanh_thu,
               LEAD(ds.doanh_thu) OVER (PARTITION BY ds.nv_id ORDER BY ds.thang) AS thang_sau
        FROM doanh_so ds JOIN nhan_vien nv ON nv.nv_id = ds.nv_id
        WHERE nv.ho_ten = 'Ha'
        ORDER BY ds.thang;
    """, "LEAD la LAG nhin nguoc lai. Hay dung de tinh khoang cach giua hai su kien lien tiep."),

    ("8.7", "Luy ke va trung binh truot", """
        SELECT nv.ho_ten, ds.thang, ds.doanh_thu,
               SUM(ds.doanh_thu) OVER (PARTITION BY ds.nv_id ORDER BY ds.thang
                                       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS luy_ke,
               ROUND(AVG(ds.doanh_thu) OVER (PARTITION BY ds.nv_id ORDER BY ds.thang
                                       ROWS BETWEEN 1 PRECEDING AND CURRENT ROW), 1) AS tb_2_thang
        FROM doanh_so ds JOIN nhan_vien nv ON nv.nv_id = ds.nv_id
        WHERE nv.ho_ten = 'Dung'
        ORDER BY ds.thang;
    """, "Menh de ROWS BETWEEN = 'khung nhin': tinh tren nhung dong nao quanh dong hien tai."),

    ("8.8", "BAY tinh vi: ROWS khac RANGE khi co gia tri trung", """
        SELECT ho_ten, luong,
               SUM(luong) OVER (ORDER BY luong) AS mac_dinh_la_range,
               SUM(luong) OVER (ORDER BY luong ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
                   AS ep_dung_rows
        FROM nhan_vien
        WHERE luong IS NOT NULL
        ORDER BY luong;
    """, "Co ORDER BY ma khong ghi khung -> mac dinh RANGE: hai dong luong 18 bi gop chung, ca hai cung "
         "ra mot tong. Muon luy ke dung tung dong thi phai ghi ro ROWS."),

    ("8.9", "Vi du CO Y sai: window trong WHERE", """
        SELECT ho_ten, luong, RANK() OVER (ORDER BY luong DESC) AS hang
        FROM nhan_vien
        WHERE RANK() OVER (ORDER BY luong DESC) <= 3;
    """, "Bao loi la dung. Window function chay sau WHERE/GROUP BY/HAVING, chi dung duoc o SELECT va "
         "ORDER BY. Muon loc theo hang thi boc CTE nhu vi du 8.4."),

    # ---------------- 9. NULL ----------------
    ("9.1", "NULL khong bang chinh no", """
        SELECT NULL = NULL AS bang_nhau, NULL <> NULL AS khac_nhau,
               NULL IS NULL AS dung_is_null, 1 = NULL AS so_voi_so;
    """, "Chi cot IS NULL ra 1 (dung). Cac cot con lai ra NULL = 'khong biet'. NULL nghia la THIEU "
         "DU LIEU, khong phai mot gia tri de dem ra so sanh."),

    ("9.2", "Logic BA gia tri", """
        SELECT (1 = 1) AND NULL AS dung_and_null,
               (1 = 0) AND NULL AS sai_and_null,
               (1 = 1) OR  NULL AS dung_or_null,
               (1 = 0) OR  NULL AS sai_or_null,
               5 NOT IN (1, 2, NULL) AS not_in_co_null;
    """, "SAI AND khong-biet = SAI. DUNG OR khong-biet = DUNG. Con lai ra khong-biet. "
         "WHERE chi giu dong nao ra DUNG - dong ra NULL bi loai y het dong SAI."),

    ("9.3", "NULL bi loai ca o dieu kien phu dinh", """
        SELECT ho_ten, luong FROM nhan_vien WHERE luong <> 18;
    """, "Linh (luong NULL) KHONG xuat hien du 'chua chot luong' ro rang la khac 18. Muon giu phai "
         "viet WHERE luong <> 18 OR luong IS NULL."),

    ("9.4", "Ham gom nhom bo qua NULL", """
        SELECT COUNT(*) AS so_dong, COUNT(luong) AS co_luong, SUM(luong) AS tong,
               ROUND(AVG(luong), 3) AS avg_that,
               ROUND(SUM(luong) * 1.0 / COUNT(*), 3) AS neu_chia_cho_8
        FROM nhan_vien;
    """, "AVG = tong/7 chu khong phai tong/8. Neu nghiep vu coi 'chua chot luong = 0' thi phai viet "
         "ro AVG(COALESCE(luong, 0)) - dung de may tu quyet."),

    ("9.5", "NULL sap xep o dau?", """
        SELECT ho_ten, luong FROM nhan_vien ORDER BY luong ASC;
        SELECT ho_ten, luong FROM nhan_vien ORDER BY luong DESC;
        SELECT ho_ten, luong FROM nhan_vien ORDER BY luong ASC NULLS LAST;
    """, "SQLite/PostgreSQL coi NULL nho nhat -> ASC no len dau, DESC no xuong cuoi. Oracle nguoc lai. "
         "Muon chac chan thi ghi ro NULLS FIRST / NULLS LAST."),

    ("9.6", "COALESCE / IFNULL / NULLIF", """
        SELECT ho_ten,
               COALESCE(luong, 0) AS luong_hien_thi,
               COALESCE(CAST(phong_id AS TEXT), 'chua phan phong') AS phong,
               NULLIF(luong, 12) AS bo_muc_12
        FROM nhan_vien;
    """, "COALESCE tra ve gia tri KHONG NULL dau tien. NULLIF(a, b) tra ve NULL neu a = b - hay dung "
         "de tranh chia cho 0: x / NULLIF(y, 0)."),

    ("9.7", "Noi chuoi voi NULL thi mat trang dong", """
        SELECT ho_ten, ho_ten || ' - ' || luong AS mo_ta,
               ho_ten || ' - ' || COALESCE(luong, 0) AS mo_ta_da_chua
        FROM nhan_vien
        WHERE nv_id IN (2, 7);
    """, "Bat cu phep tinh nao dinh NULL deu ra NULL. Dong cua Linh mat sach ca chuoi mo ta."),

    ("9.8", "GROUP BY va DISTINCT lai coi cac NULL la GIONG nhau", """
        SELECT phong_id, COUNT(*) AS so_nguoi FROM nhan_vien GROUP BY phong_id ORDER BY phong_id;
    """, "Mau thuan de nho: toan tu = noi 'NULL khac NULL', nhung GROUP BY/DISTINCT/UNION lai gom "
         "cac NULL vao chung mot nhom."),

    # ---------------- 10. INDEX ----------------
    ("10.1", "Doc ke hoach chay: SCAN = quet ca bang", """
        EXPLAIN QUERY PLAN SELECT * FROM nhan_vien WHERE ho_ten = 'Chi';
    """, "SCAN nhan_vien = doc tung dong tu dau den cuoi. 8 dong thi khong sao, 8 trieu dong thi chet."),

    ("10.2", "SEARCH = nhay thang toi noi (khoa chinh co san index)", """
        EXPLAIN QUERY PLAN SELECT * FROM nhan_vien WHERE nv_id = 3;
    """, "INTEGER PRIMARY KEY chinh la rowid cua SQLite -> tim theo no la nhay thang, khong quet."),

    ("10.3", "Tao index roi xem ke hoach doi", """
        EXPLAIN QUERY PLAN SELECT * FROM nhan_vien WHERE phong_id = 10;
        CREATE INDEX idx_nv_phong ON nhan_vien(phong_id);
        EXPLAIN QUERY PLAN SELECT * FROM nhan_vien WHERE phong_id = 10;
    """, "Truoc: SCAN. Sau: SEARCH USING INDEX. Con so thoi gian thuc te do o che do --index."),

    ("10.4", "Boc ham quanh cot la GIET index", """
        CREATE INDEX IF NOT EXISTS idx_nv_ngay ON nhan_vien(ngay_vao);
        EXPLAIN QUERY PLAN SELECT * FROM nhan_vien WHERE substr(ngay_vao, 1, 4) = '2023';
        EXPLAIN QUERY PLAN SELECT * FROM nhan_vien WHERE ngay_vao >= '2023-01-01' AND ngay_vao < '2024-01-01';
    """, "Cau tren: cot bi boc trong substr() -> index vo dung -> SCAN. Cau duoi cung y nghia nhung "
         "viet dang khoang -> dung duoc index. Nguyen tac: de COT TRAN mot ben dau bang, dung boc ham quanh no."),

    ("10.5", "Index nhieu cot va quy tac 'tien to trai'", """
        CREATE INDEX idx_ds_nv_thang ON doanh_so(nv_id, thang);
        EXPLAIN QUERY PLAN SELECT * FROM doanh_so WHERE nv_id = 4 AND thang = '2025-02';
        EXPLAIN QUERY PLAN SELECT * FROM doanh_so WHERE nv_id = 4;
        EXPLAIN QUERY PLAN SELECT * FROM doanh_so WHERE thang = '2025-02';
    """, "Index (nv_id, thang) giong danh ba sap theo HO roi den TEN: tim theo ho - duoc; tim theo "
         "ho + ten - duoc; tim MOI ten ma khong biet ho - chiu, phai quet ca danh ba."),

    ("10.6", "Covering index: khong can mo lai bang goc", """
        EXPLAIN QUERY PLAN SELECT nv_id, thang FROM doanh_so WHERE nv_id = 4;
        EXPLAIN QUERY PLAN SELECT nv_id, thang, doanh_thu FROM doanh_so WHERE nv_id = 4;
    """, "Cau tren chi can hai cot da nam san trong index -> USING COVERING INDEX, khoi doc bang goc. "
         "Cau duoi can them doanh_thu -> phai quay ve bang lay tung dong."),

    ("10.7", "Index con giup ORDER BY", """
        EXPLAIN QUERY PLAN SELECT ho_ten, luong FROM nhan_vien ORDER BY luong;
        CREATE INDEX idx_nv_luong ON nhan_vien(luong);
        EXPLAIN QUERY PLAN SELECT ho_ten, luong FROM nhan_vien ORDER BY luong;
    """, "Truoc: USE TEMP B-TREE FOR ORDER BY = phai sap xep tam mot lan. Sau: doc theo index la da "
         "co san thu tu."),
]


# --------------------------------------------------------------------------------------
# 10 BAI TAP - loi giai
# --------------------------------------------------------------------------------------
BAI_TAP = [
    ("1", "Liet ke ho ten va luong cua nhan vien phong 10, luong cao truoc.", """
        SELECT ho_ten, luong
        FROM nhan_vien
        WHERE phong_id = 10
        ORDER BY luong DESC;
    """, "Bai khoi dong: SELECT - WHERE - ORDER BY."),

    ("2", "Cong ty co bao nhieu nguoi, bao nhieu nguoi da chot luong, luong trung binh thuc te?", """
        SELECT COUNT(*)             AS tong_nv,
               COUNT(luong)         AS da_chot_luong,
               ROUND(AVG(luong), 2) AS luong_tb
        FROM nhan_vien;
    """, "Bay o day la COUNT(*) khac COUNT(luong), va AVG chia cho so nguoi CO luong (7) chu khong "
         "phai tong so nguoi (8)."),

    ("3", "Moi phong co may nguoi va quy luong bao nhieu? Chi lay phong tu 2 nguoi tro len.", """
        SELECT phong_id, COUNT(*) AS so_nv, SUM(luong) AS quy_luong
        FROM nhan_vien
        GROUP BY phong_id
        HAVING COUNT(*) >= 2
        ORDER BY quy_luong DESC;
    """, "Dieu kien tren nhom -> HAVING. Phong 30 co 2 nguoi nhung quy luong chi tinh duoc 12 vi "
         "luong cua Linh la NULL."),

    ("4", "Liet ke TAT CA phong ban kem so nhan vien, ke ca phong chua co ai.", """
        SELECT pb.ten_phong, COUNT(nv.nv_id) AS so_nv
        FROM phong_ban pb
        LEFT JOIN nhan_vien nv ON pb.phong_id = nv.phong_id
        GROUP BY pb.phong_id, pb.ten_phong
        ORDER BY so_nv DESC, pb.phong_id;
    """, "Hai cho de sai: (1) phai LEFT JOIN va dat phong_ban ben trai; (2) phai COUNT(nv.nv_id), "
         "neu COUNT(*) thi phong Nghien cuu ra 1."),

    ("5", "Nhung ai chua tung co ban ghi doanh so nao?", """
        SELECT nv.nv_id, nv.ho_ten
        FROM nhan_vien nv
        WHERE NOT EXISTS (SELECT 1 FROM doanh_so ds WHERE ds.nv_id = nv.nv_id)
        ORDER BY nv.nv_id;
    """, "O bai nay NOT IN cung ra dung vi doanh_so.nv_id la NOT NULL. Nhung tra loi phong van nen "
         "chon NOT EXISTS va noi ro ly do: NOT IN se sai neu cot ben trong co NULL."),

    ("6", "Moi nhan vien di kem ten quan ly; ai khong co sep thi ghi '(khong co)'.", """
        SELECT nv.ho_ten AS nhan_vien,
               COALESCE(sep.ho_ten, '(khong co)') AS quan_ly
        FROM nhan_vien nv
        LEFT JOIN nhan_vien sep ON nv.quan_ly_id = sep.nv_id
        ORDER BY nv.nv_id;
    """, "SELF JOIN + LEFT de khong lam mat sep tong + COALESCE de dep so lieu."),

    ("7", "Tim muc luong CAO THU HAI trong cong ty (viet 3 cach).", """
        SELECT MAX(luong) AS cach_1
        FROM nhan_vien
        WHERE luong < (SELECT MAX(luong) FROM nhan_vien);

        SELECT DISTINCT luong AS cach_2
        FROM nhan_vien
        WHERE luong IS NOT NULL
        ORDER BY luong DESC
        LIMIT 1 OFFSET 1;

        WITH xh AS (
            SELECT luong, DENSE_RANK() OVER (ORDER BY luong DESC) AS hang
            FROM nhan_vien
            WHERE luong IS NOT NULL
        )
        SELECT DISTINCT luong AS cach_3 FROM xh WHERE hang = 2;
    """, "Phai la DENSE_RANK chu khong phai ROW_NUMBER, va phai DISTINCT: neu hai nguoi cung dung "
         "dinh thi 'cao thu hai' la muc luong khac tiep theo, khong phai nguoi thu hai."),

    ("8", "Top 2 muc luong cao nhat MOI PHONG, kem ten phong.", """
        WITH xh AS (
            SELECT pb.ten_phong, nv.ho_ten, nv.luong,
                   DENSE_RANK() OVER (PARTITION BY nv.phong_id ORDER BY nv.luong DESC) AS hang
            FROM nhan_vien nv
            JOIN phong_ban pb ON pb.phong_id = nv.phong_id
            WHERE nv.luong IS NOT NULL
        )
        SELECT ten_phong, ho_ten, luong, hang
        FROM xh
        WHERE hang <= 2
        ORDER BY ten_phong, hang, ho_ten;
    """, "Phong Ky thuat co Binh va Chi cung 18 -> DENSE_RANK giu ca hai (3 dong). Neu dung "
         "ROW_NUMBER thi mot trong hai bi cat oan. Luon hoi lai nguoi phong van: 'bang diem thi lay het "
         "hay lay dung 2?' - hoi duoc cau nay la duoc diem."),

    ("9", "Voi moi nhan vien co doanh so: doanh thu tung thang, thang truoc, va % tang truong.", """
        WITH t AS (
            SELECT nv.ho_ten, ds.thang, ds.doanh_thu,
                   LAG(ds.doanh_thu) OVER (PARTITION BY ds.nv_id ORDER BY ds.thang) AS thang_truoc
            FROM doanh_so ds
            JOIN nhan_vien nv ON nv.nv_id = ds.nv_id
        )
        SELECT ho_ten, thang, doanh_thu, thang_truoc,
               ROUND((doanh_thu - thang_truoc) * 100.0 / NULLIF(thang_truoc, 0), 1) AS tang_truong_pc
        FROM t
        ORDER BY ho_ten, thang;
    """, "Ba y an diem: PARTITION BY de khong lay nham thang cua nguoi khac; * 100.0 de khong bi chia "
         "nguyen; NULLIF(x, 0) de khong no loi chia cho 0."),

    ("10", "Bang xep hang phong ban: so nhan vien, tong doanh thu, ty trong % toan cong ty, thu hang. "
           "Phong khong co doanh thu van phai hien voi so 0.", """
        WITH ds_phong AS (
            SELECT pb.phong_id, pb.ten_phong,
                   COUNT(DISTINCT nv.nv_id)   AS so_nv,
                   COALESCE(SUM(ds.doanh_thu), 0) AS tong_ds
            FROM phong_ban pb
            LEFT JOIN nhan_vien nv ON nv.phong_id = pb.phong_id
            LEFT JOIN doanh_so  ds ON ds.nv_id   = nv.nv_id
            GROUP BY pb.phong_id, pb.ten_phong
        )
        SELECT ten_phong, so_nv, tong_ds,
               ROUND(tong_ds * 100.0 / NULLIF(SUM(tong_ds) OVER (), 0), 1) AS ty_trong_pc,
               RANK() OVER (ORDER BY tong_ds DESC) AS hang
        FROM ds_phong
        ORDER BY hang, ten_phong;
    """, "Cho chet nguoi: JOIN them bang doanh_so lam moi nhan vien NHAN ra 4 dong, nen phai "
         "COUNT(DISTINCT nv.nv_id) chu khong COUNT(nv.nv_id). SUM(...) OVER () la tong toan bang de "
         "tinh ty trong ma khong can query thu hai. Hai phong cung 0 -> RANK cho ca hai cung hang 3."),
]


# --------------------------------------------------------------------------------------
# MUC 11 - TRANSACTION (chay that, khong phai giai thich chay)
# --------------------------------------------------------------------------------------
def demo_transaction(conn):
    print("\n" + DAI)
    print("  MUC 11 - TRANSACTION: BEGIN / COMMIT / ROLLBACK")
    print(DAI)

    def luong(ten):
        return conn.execute("SELECT luong FROM nhan_vien WHERE ho_ten = ?", (ten,)).fetchone()[0]

    print(f"\n  [1] Luong cua Binh ban dau                      : {luong('Binh')}")

    conn.execute("BEGIN")
    conn.execute("UPDATE nhan_vien SET luong = 99 WHERE ho_ten = 'Binh'")
    print(f"  [2] BEGIN; UPDATE ... = 99  -> doc trong transaction: {luong('Binh')}")
    conn.execute("ROLLBACK")
    print(f"  [3] ROLLBACK                                    : {luong('Binh')}  <- nhu chua co gi xay ra")

    conn.execute("BEGIN")
    conn.execute("UPDATE nhan_vien SET luong = 20 WHERE ho_ten = 'Binh'")
    conn.execute("COMMIT")
    print(f"  [4] BEGIN; UPDATE ... = 20; COMMIT              : {luong('Binh')}  <- lan nay ghi that")

    print("\n  [5] NGUYEN KHOI (Atomicity): hai buoc trong mot transaction, buoc 2 loi")
    print(f"      Luong Dung truoc khi chuyen: {luong('Dung')}")
    try:
        conn.execute("BEGIN")
        conn.execute("UPDATE nhan_vien SET luong = luong - 5 WHERE ho_ten = 'Dung'")
        print(f"      buoc 1 (tru 5) da chay     : {luong('Dung')}")
        conn.execute(
            "INSERT INTO nhan_vien (nv_id, ho_ten, ngay_vao) VALUES (1, 'Trung khoa chinh', '2025-01-01')"
        )
        conn.execute("COMMIT")
    except sqlite3.Error as e:
        print(f"      buoc 2 BAO LOI             : {e}")
        conn.execute("ROLLBACK")
        print("      -> goi ROLLBACK")
    print(f"      Luong Dung sau tat ca      : {luong('Dung')}  <- khong bi tru nua chung")

    conn.execute("UPDATE nhan_vien SET luong = 18 WHERE ho_ten = 'Binh'")
    print("\n  (da tra luong Binh ve 18 de cac vi du khac chay dung)")


# --------------------------------------------------------------------------------------
# CHE DO --index: do thoi gian THAT tren bang lon
# --------------------------------------------------------------------------------------
def demo_index(so_dong=200_000):
    print("\n" + DAI)
    print(f"  DO THOI GIAN THAT - bang {so_dong:,} dong".replace(",", ".") + ", truoc va sau khi tao index")
    print(DAI)

    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.execute("CREATE TABLE log_lon (id INTEGER PRIMARY KEY, nv_id INTEGER, thang TEXT, doanh_thu INTEGER)")
    t0 = time.perf_counter()
    conn.execute("""
        INSERT INTO log_lon (id, nv_id, thang, doanh_thu)
        WITH RECURSIVE s(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM s WHERE n < ?)
        SELECT n, n % 5000, '2025-' || substr('0' || (n % 12 + 1), -2), n % 997 FROM s
    """, (so_dong,))
    print(f"\n  Sinh du lieu bang CTE de quy: {time.perf_counter() - t0:.2f} giay")

    def do_ms(sql, lan=20):
        t = time.perf_counter()
        for _ in range(lan):
            conn.execute(sql).fetchall()
        return (time.perf_counter() - t) / lan * 1000

    def plan(sql):
        return " | ".join(r[3] for r in conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall())

    q = "SELECT * FROM log_lon WHERE nv_id = 1234"
    truoc = do_ms(q)
    print("\n  [1] CHUA CO INDEX")
    print(f"      ke hoach : {plan(q)}")
    print(f"      thoi gian: {truoc:.3f} ms / lan")

    t0 = time.perf_counter()
    conn.execute("CREATE INDEX idx_log_nv ON log_lon(nv_id)")
    tao = (time.perf_counter() - t0) * 1000
    sau = do_ms(q)
    print(f"\n  [2] SAU KHI CREATE INDEX idx_log_nv ON log_lon(nv_id)  (mat {tao:.0f} ms de tao)")
    print(f"      ke hoach : {plan(q)}")
    print(f"      thoi gian: {sau:.3f} ms / lan   -> NHANH GAP {truoc / max(sau, 1e-9):.0f} LAN")

    q_ham = "SELECT * FROM log_lon WHERE nv_id + 0 = 1234"
    print("\n  [3] VAN CO INDEX, nhung boc cot trong bieu thuc: WHERE nv_id + 0 = 1234")
    print(f"      ke hoach : {plan(q_ham)}")
    print(f"      thoi gian: {do_ms(q_ham):.3f} ms / lan   -> index bi vut di, cham lai nhu cu")

    q_tp = "SELECT * FROM log_lon WHERE thang = '2025-03'"
    print("\n  [4] Cot thang CHUA co index: WHERE thang = '2025-03'")
    print(f"      ke hoach : {plan(q_tp)}")
    print(f"      thoi gian: {do_ms(q_tp, 5):.3f} ms / lan   (tra ve ~1/12 bang -> index cung it giup)")

    print("\n  Ket luan de nho: index bien 'doc het 200.000 dong' thanh 'nhay thang toi vai chuc dong'.")
    print("  Doi lai: moi INSERT/UPDATE/DELETE phai cap nhat them index, va index ton bo nho/dia.")
    conn.close()


# --------------------------------------------------------------------------------------
# CHE DO TUONG TAC
# --------------------------------------------------------------------------------------
TRO_GIUP = """
  LENH DAC BIET (bat dau bang dau cham):
    .help              hien bang nay
    .tables            liet ke cac bang
    .schema [ten]      xem cau lenh tao bang
    .data              in ca ba bang du lieu mau
    .reset             tao lai du lieu goc (lo UPDATE/DELETE bay thi go cai nay)
    .vidu              liet ke tat ca vi du trong bai giang
    .vidu 8.5          chay lai vi du 8.5
    .baitap            liet ke 10 bai tap
    .baitap 7          xem loi giai bai 7
    .quit              thoat (hoac Ctrl+C)

  GO SQL: go binh thuong, KET THUC bang dau cham phay ;  (co the xuong dong tuy y)
    vi du:  SELECT ho_ten, luong FROM nhan_vien WHERE luong > 15 ORDER BY luong DESC;
"""


def lenh_dac_biet(conn, dong):
    phan = dong.split(None, 1)
    lenh = phan[0].lower()
    tham_so = phan[1].strip() if len(phan) > 1 else ""

    if lenh in (".quit", ".exit", ".q"):
        return False
    if lenh == ".help":
        print(TRO_GIUP)
    elif lenh == ".tables":
        in_bang(conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"))
    elif lenh == ".schema":
        sql = "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL"
        rows = conn.execute(sql + (" AND name = ?" if tham_so else ""),
                            (tham_so,) if tham_so else ()).fetchall()
        for (s,) in rows:
            print("\n" + s + ";")
    elif lenh == ".data":
        for bang in ("phong_ban", "nhan_vien", "doanh_so"):
            print(f"\n  BANG {bang}:")
            in_bang(conn.execute(f"SELECT * FROM {bang}"))
    elif lenh == ".reset":
        conn.executescript(SCHEMA_SQL)
        print("  Da tao lai du lieu mau ban dau.")
    elif lenh == ".vidu":
        if tham_so:
            tim = [v for v in VI_DU if v[0] == tham_so or v[0].startswith(tham_so + ".")]
            if not tim:
                print(f"  Khong co vi du '{tham_so}'. Go .vidu de xem danh sach.")
            for v in tim:
                chay_vi_du(conn, *v)
        else:
            for ma, tieu_de, _, _ in VI_DU:
                print(f"  {ma:<6} {tieu_de}")
    elif lenh == ".baitap":
        if tham_so:
            tim = [b for b in BAI_TAP if b[0] == tham_so]
            if not tim:
                print(f"  Khong co bai '{tham_so}' (bai 1 den 10).")
            for so, de, sql, ghi_chu in tim:
                chay_vi_du(conn, f"BAI {so}", de, sql, ghi_chu)
        else:
            for so, de, _, _ in BAI_TAP:
                print(f"  Bai {so:<3} {de}")
    else:
        print(f"  Khong biet lenh '{lenh}'. Go .help de xem danh sach.")
    return True


def tuong_tac(conn):
    print(DAI)
    print("  DEMO SQL - go cau lenh SQL vao day, ket thuc bang dau cham phay ;")
    print("  Du lieu nam trong bo nho, khong pha duoc gi. Go .help de xem huong dan, .quit de thoat.")
    print(DAI)
    print(TRO_GIUP)
    for bang in ("phong_ban", "nhan_vien", "doanh_so"):
        print(f"\n  BANG {bang}:")
        in_bang(conn.execute(f"SELECT * FROM {bang}"))

    dem = ""
    while True:
        try:
            dong = input("\nsql> " if not dem else "...> ")
        except (EOFError, KeyboardInterrupt):
            print("\n  Tam biet.")
            return
        if not dem and dong.strip().startswith("."):
            if lenh_dac_biet(conn, dong.strip()) is False:
                print("  Tam biet.")
                return
            continue
        if not dem and not dong.strip():
            continue
        dem += dong + "\n"
        if sqlite3.complete_statement(dem):
            try:
                in_bang(conn.execute(dem))
            except sqlite3.Error as e:
                print(f"  LOI SQL: {e}")
            dem = ""


# --------------------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(
        description="Demo SQL chay that bang sqlite3 - hoc kem docs/HOC_SQL.md")
    p.add_argument("--demo", nargs="?", const="all", metavar="MUC",
                   help="chay lai vi du trong bai giang (--demo hoac --demo 8)")
    p.add_argument("--baitap", nargs="?", const="all", metavar="SO",
                   help="chay loi giai bai tap (--baitap hoac --baitap 7)")
    p.add_argument("--index", action="store_true",
                   help="do thoi gian query tren bang 200.000 dong, truoc va sau khi tao index")
    tham_so = p.parse_args()

    if tham_so.index:
        demo_index()
        return

    conn = tao_db()
    try:
        if tham_so.demo:
            muc = tham_so.demo
            chon = VI_DU if muc == "all" else [v for v in VI_DU if v[0].split(".")[0] == muc]
            if not chon and muc != "11":   # muc 11 khong nam trong VI_DU, chay bang ham rieng
                print(f"Khong co muc '{muc}'. Cac muc co vi du: 3, 4, 5, 6, 7, 8, 9, 10, 11.")
                return
            for v in chon:
                chay_vi_du(conn, *v)
            if muc in ("all", "11"):
                demo_transaction(conn)
            print("\n" + DAI)
            print("  Xong. Muon tu go SQL thi chay lai khong kem tham so nao.")
            print(DAI)
        elif tham_so.baitap:
            so = tham_so.baitap
            chon = BAI_TAP if so == "all" else [b for b in BAI_TAP if b[0] == so]
            if not chon:
                print(f"Khong co bai '{so}' (bai 1 den 10).")
                return
            for b_so, de, sql, ghi_chu in chon:
                chay_vi_du(conn, f"BAI {b_so}", de, sql, ghi_chu)
        else:
            tuong_tac(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
