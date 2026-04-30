import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize Supabase with SERVICE key (backend can use it safely)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ========== COMMANDS ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Register user in DB and send welcome message"""
    telegram_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name

    # Try to insert user (ignore if already exists)
    try:
        supabase.table("users").upsert({
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name
        }, on_conflict="telegram_id").execute()
        
        await update.message.reply_text(
            f"🔥 Welcome to MemTrack Sniper, {first_name}!\n\n"
            "Here's what I can do:\n"
            "/signals – Get AI-filtered coin picks\n"
            "/trade – Log a trade\n"
            "/portfolio – See your open positions\n"
            "/report – Download your trading report\n"
            "/help – Show all commands"
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    await update.message.reply_text(
        "📋 *MemTrack Commands*\n\n"
        "/start – Register & welcome\n"
        "/signals – Get top filtered coin signals\n"
        "/trade – Log a new trade (format: BUY/SOLD SYMBOL PRICE AMOUNT)\n"
        "/portfolio – View your open trades\n"
        "/report – Generate & download your report\n"
        "/help – Show this message",
        parse_mode="Markdown"
    )


async def signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return latest signals from DB"""
    try:
        result = supabase.table("signals").select("*").order("created_at", desc=True).limit(5).execute()
        signals_list = result.data
        
        if not signals_list:
            await update.message.reply_text("🔍 No signals yet. Generating AI signals coming soon!")
            return
        
        msg = "📊 *Top Signals*\n\n"
        for s in signals_list:
            msg += f"🪙 *{s['coin_symbol'].upper()}* – {s['coin_name']}\n"
            msg += f"   Price: ${s['current_price']}\n"
            msg += f"   Entry: ${s['suggested_entry']}\n"
            msg += f"   TP: +{s['take_profit']}% | SL: {s['stop_loss']}%\n"
            msg += f"   Confidence: {s['confidence_score']}/10\n"
            msg += f"   {s['reason']}\n\n"
        
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error fetching signals: {e}")


async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show open trades for this user"""
    telegram_id = update.effective_user.id
    
    try:
        # Get user UUID first
        user = supabase.table("users").select("id").eq("telegram_id", telegram_id).single().execute()
        if not user.data:
            await update.message.reply_text("Please /start first!")
            return
        
        user_id = user.data["id"]
        
        # Get open trades
        trades = supabase.table("trades").select("*").eq("user_id", user_id).eq("status", "open").execute()
        
        if not trades.data:
            await update.message.reply_text("📭 No open positions.")
            return
        
        msg = "📊 *Your Open Positions*\n\n"
        total_pl = 0
        for t in trades.data:
            msg += f"🪙 {t['coin_symbol'].upper()} – {t['side'].upper()}\n"
            msg += f"   Entry: ${t['entry_price']} | Amount: {t['amount']}\n"
            msg += f"   TP: +{t['take_profit']}% | SL: {t['stop_loss']}%\n"
            msg += f"   Opened: {t['opened_at'][:10]}\n\n"
        
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


# ========== MAIN ==========

def main():
    """Start the bot"""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("signals", signals))
    app.add_handler(CommandHandler("portfolio", portfolio))
    
    # Start polling
    print("🤖 Bot is running... Press Ctrl+C to stop")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()