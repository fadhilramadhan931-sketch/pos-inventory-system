# ==========================================
# SISTEM KASIR DAN MANAJEMEN STOK TOKO
# ==========================================

import os
import math
from datetime import datetime

# =====================
# DATA GLOBAL
# =====================
produk_list = []
riwayat_transaksi = []

# =====================
# FUNGSI CLEAR SCREEN
# =====================
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

# =====================
# TAMBAH PRODUK
# =====================
def tambah_produk():
    print("\n=== TAMBAH PRODUK ===")

    nama = input("Nama Produk : ")
    harga = float(input("Harga Produk : Rp "))
    stok = int(input("Stok Awal : "))

    produk = {
        "nama": nama,
        "harga": harga,
        "stok": stok,
        "terjual": 0
    }

    produk_list.append(produk)

    print("Produk berhasil ditambahkan!")

# =====================
# LIHAT STOK
# =====================
def lihat_stok():
    print("\n=== DAFTAR PRODUK ===")

    if len(produk_list) == 0:
        print("Belum ada produk.")
        return

    print("-" * 55)
    print(f"{'No':<5}{'Nama':<20}{'Harga':<15}{'Stok'}")
    print("-" * 55)

    for i, p in enumerate(produk_list, start=1):
        print(
            f"{i:<5}{p['nama']:<20}Rp {p['harga']:<12,.0f}{p['stok']}"
        )

# =====================
# CETAK STRUK
# =====================
def cetak_struk(
    keranjang,
    subtotal,
    diskon_persen,
    diskon,
    ppn,
    total_bayar,
    uang,
    kembalian
):

    print("\n")
    print("=" * 45)
    print("        TOKO PARA IMO")
    print("       Kasir Para Imortal")
    print("=" * 45)

    for item in keranjang:
        print(
            f"{item['nama']} x{item['qty']}"
        )
        print(
            f"   Rp {item['harga']:,.0f} = Rp {item['subtotal']:,.0f}"
        )

    print("-" * 45)
    print(f"Subtotal     : Rp {subtotal:,.0f}")
    print(f"Diskon {diskon_persen}%   : Rp {diskon:,.0f}")
    print(f"PPN 11%      : Rp {ppn:,.0f}")
    print(f"Total Bayar  : Rp {total_bayar:,.0f}")
    print(f"Tunai        : Rp {uang:,.0f}")
    print(f"Kembalian    : Rp {kembalian:,.0f}")

    print("-" * 45)
    print(
        "Tanggal :",
        datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    )
    print("=" * 45)

# =====================
# TRANSAKSI
# =====================
def proses_transaksi():

    if len(produk_list) == 0:
        print("Belum ada produk!")
        return

    keranjang = []

    while True:

        lihat_stok()

        try:
            pilihan = int(
                input("\nPilih nomor produk (0 selesai): ")
            )

            if pilihan == 0:
                break

            produk = produk_list[pilihan - 1]

            qty = int(
                input(
                    f"Jumlah {produk['nama']} : "
                )
            )

            # Validasi stok
            if qty > produk["stok"]:
                print("Stok tidak mencukupi!")
                continue

            subtotal_item = qty * produk["harga"]

            keranjang.append({
                "nama": produk["nama"],
                "harga": produk["harga"],
                "qty": qty,
                "subtotal": subtotal_item,
                "index_produk": pilihan - 1
            })

        except:
            print("Input tidak valid!")

    if len(keranjang) == 0:
        print("Tidak ada transaksi.")
        return

    # =====================
    # HITUNG TOTAL
    # =====================
    subtotal = sum(
        item["subtotal"] for item in keranjang
    )

    # Diskon otomatis
    diskon_persen = 0

    if subtotal > 500000:
        diskon_persen = 15
    elif subtotal > 200000:
        diskon_persen = 10
    elif subtotal > 100000:
        diskon_persen = 5

    diskon = subtotal * diskon_persen / 100

    setelah_diskon = subtotal - diskon

    ppn = setelah_diskon * 0.11

    total_bayar = setelah_diskon + ppn

    total_bayar = math.ceil(total_bayar)

    # =====================
    # INPUT PEMBAYARAN
    # =====================
    while True:

        uang = float(
            input(
                f"\nTotal Bayar Rp {total_bayar:,.0f}\nUang Tunai : Rp "
            )
        )

        if uang < total_bayar:
            print("Uang tidak cukup!")
        else:
            break

    kembalian = uang - total_bayar

    # =====================
    # UPDATE STOK
    # =====================
    for item in keranjang:

        idx = item["index_produk"]

        produk_list[idx]["stok"] -= item["qty"]

        produk_list[idx]["terjual"] += item["qty"]

    # =====================
    # SIMPAN RIWAYAT
    # =====================
    transaksi = {
        "tanggal":
        datetime.now().strftime(
            "%d-%m-%Y %H:%M:%S"
        ),
        "total": total_bayar
    }

    riwayat_transaksi.append(transaksi)

    # =====================
    # CETAK STRUK
    # =====================
    cetak_struk(
        keranjang,
        subtotal,
        diskon_persen,
        diskon,
        ppn,
        total_bayar,
        uang,
        kembalian
    )

# =====================
# RIWAYAT TRANSAKSI
# =====================
def lihat_riwayat():

    print("\n=== RIWAYAT TRANSAKSI ===")

    if len(riwayat_transaksi) == 0:
        print("Belum ada transaksi.")
        return

    total_pendapatan = 0

    for i, trx in enumerate(
        riwayat_transaksi,
        start=1
    ):
        print(
            f"{i}. {trx['tanggal']} | Rp {trx['total']:,.0f}"
        )
        total_pendapatan += trx["total"]

    print("\nJumlah Transaksi :", len(riwayat_transaksi))
    print(
        f"Total Pendapatan : Rp {total_pendapatan:,.0f}"
    )

    # Produk terlaris
    if len(produk_list) > 0:

        terlaris = max(
            produk_list,
            key=lambda x: x["terjual"]
        )

        print(
            f"Produk Terlaris : {terlaris['nama']} ({terlaris['terjual']} terjual)"
        )

# =====================
# MENU UTAMA
# =====================
while True:

    print("\n")
    print("=" * 40)
    print(" SISTEM KASIR DAN MANAJEMEN STOK ")
    print("=" * 40)
    print("1. Tambah Produk")
    print("2. Transaksi Baru")
    print("3. Lihat Stok")
    print("4. Riwayat Transaksi")
    print("5. Keluar")

    pilihan = input("Pilih Menu : ")

    if pilihan == "1":
        tambah_produk()

    elif pilihan == "2":
        proses_transaksi()

    elif pilihan == "3":
        lihat_stok()

    elif pilihan == "4":
        lihat_riwayat()

    elif pilihan == "5":
        print("Program selesai.")
        break

    else:
        print("Menu tidak tersedia!")
