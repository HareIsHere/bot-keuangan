import os
import json
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# === Google Sheets Setup ===
def get_gsheet_client():
    google_creds = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
    return gspread.authorize(credentials)
print("GOOGLE_CREDENTIALS exists?", "GOOGLE_CREDENTIALS" in os.environ)


SPREADSHEET_NAME = os.environ.get("SPREADSHEET_NAME", "Pencatatan Keuangan")
gc = get_gsheet_client()

# === Helper: ambil / buat worksheet bulanan ===
def get_monthly_sheet():
    today = datetime.date.today()
    sheet_name = f"{today.year}-{today.month:02d}"

    file = gc.open(SPREADSHEET_NAME)
    try:
        sheet = file.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        sheet = file.add_worksheet(title=sheet_name, rows=500, cols=4)
        sheet.append_row(["Tanggal", "Kategori", "Deskripsi", "Nominal"])
    return sheet

# === Helper: ambil / buat worksheet rekap ===
def get_rekap_sheet():
    file = gc.open(SPREADSHEET_NAME)
    try:
        sheet = file.worksheet("Rekap")
    except gspread.exceptions.WorksheetNotFound:
        sheet = file.add_worksheet(title="Rekap", rows=20, cols=5)
        sheet.append_row(["Tahun", "Bulan", "Total Pengeluaran"])
    return sheet

# === Update rekap tahunan ===
def update_rekap(nominal: int):
    today = datetime.date.today()
    tahun = today.year
    bulan = today.month

    sheet = get_rekap_sheet()
    records = sheet.get_all_records()

    # cek apakah sudah ada entry untuk tahun & bulan ini
    found = False
    for i, row in enumerate(records, start=2):  # mulai dari baris ke-2 (header di baris 1)
        if row["Tahun"] == tahun and row["Bulan"] == bulan:
            total = int(row["Total Pengeluaran"]) + nominal
            sheet.update_cell(i, 3, total)  # kolom C = Total Pengeluaran
            found = True
            break

    # kalau belum ada, tambah baris baru
    if not found:
        sheet.append_row([tahun, bulan, nominal])

# === Command: /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! 🎉\nKirim catatan keuangan dengan format:\n"
        "/catat <kategori> <deskripsi> <nominal>\n\n"
        "Contoh: /catat Makan SotoAyam 25000"
    )

# === Command: /catat ===
async def catat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        kategori = context.args[0]
        nominal = int(context.args[-1])
        deskripsi = " ".join(context.args[1:-1])

        # tulis ke sheet bulanan
        sheet = get_monthly_sheet()
        today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sheet.append_row([today, kategori, deskripsi, nominal])

        # update rekap tahunan
        update_rekap(nominal)

        await update.message.reply_text(
            f"✅ Tercatat: {kategori} - {deskripsi} Rp{nominal:,}"
        )
    except Exception as e:
        await update.message.reply_text(
            f"⚠️ Format salah.\nGunakan: /catat <kategori> <deskripsi> <nominal>\nError: {e}"
        )

# === Main App ===
def main():
    token = os.environ["BOT_TOKEN"]
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("catat", catat))

    print("Bot jalan... 🚀")
    app.run_polling()

if __name__ == "__main__":
    main()

