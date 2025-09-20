import os
import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from credentials import get_gsheet_client

# --- Setup Google Sheets ---
SPREADSHEET_NAME = "Pencatatan Keuangan"  # ganti sesuai nama sheet kamu
gc = get_gsheet_client()

def get_monthly_sheet():
    today = datetime.date.today()
    sheet_name = f"{today.year}-{today.month:02d}"

    file = gc.open(SPREADSHEET_NAME)
    try:
        sheet = file.worksheet(sheet_name)
    except:
        # buat worksheet baru kalau belum ada
        sheet = file.add_worksheet(title=sheet_name, rows=500, cols=4)
        sheet.append_row(["Tanggal", "Kategori", "Deskripsi", "Nominal"])
    return sheet

# --- Command Handler: /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Kirim catatan keuangan dengan format:\n"
        "/catat <kategori> <deskripsi> <nominal>\n"
        "Gunakan /rekap untuk lihat total bulan ini."
    )

# --- Command Handler: /catat ---
async def catat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        kategori = context.args[0]
        nominal = int(context.args[-1])
        deskripsi = " ".join(context.args[1:-1])

        sheet = get_monthly_sheet()
        today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        sheet.append_row([today, kategori, deskripsi, nominal])
        await update.message.reply_text(
            f"✅ Tercatat: {kategori} - {deskripsi} Rp{nominal:,}"
        )
    except Exception as e:
        await update.message.reply_text(
            f"⚠️ Format salah.\nGunakan: /catat <kategori> <deskripsi> <nominal>\nError: {e}"
        )

# --- Command Handler: /rekap ---
async def rekap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sheet = get_monthly_sheet()
        records = sheet.get_all_records()

        if not records:
            await update.message.reply_text("📊 Belum ada catatan bulan ini.")
            return

        total = sum(row["Nominal"] for row in records)
        # Rekap per kategori
        kategori_total = {}
        for row in records:
            kategori = row["Kategori"]
            kategori_total[kategori] = kategori_total.get(kategori, 0) + row["Nominal"]

        # Buat output
        pesan = "📊 Rekap Bulan Ini:\n"
        for k, v in kategori_total.items():
            pesan += f"- {k}: Rp{v:,}\n"
        pesan += f"\n💰 Total: Rp{total:,}"

        await update.message.reply_text(pesan)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Gagal ambil rekap: {e}")

# --- Setup Bot ---
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("⚠️ TELEGRAM_BOT_TOKEN tidak ditemukan di environment!")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("catat", catat))
app.add_handler(CommandHandler("rekap", rekap))

if __name__ == "__main__":
    print("Bot jalan... 🚀")
    app.run_polling()
