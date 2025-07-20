# game.py

import asyncio
from datetime import datetime, timedelta
import random

from pyrogram import filters
from pyrogram.types import Message

from word import word, WORD_SET
from word.database.db import update_stats, get_stats

active_games = {}
pending_games = {}

INACTIVE_TIMEOUT = 180  # 3 minutes


class Game:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.players = []
        self.starter = None
        self.start_time = None
        self.current_word = None
        self.used_words = set()
        self.turn_index = 0
        self.time_left = 45
        self.word_length = 3
        self.word_count = 0
        self.consecutive_count = 0
        self.created_at = datetime.utcnow()

    async def auto_cleanup(self):
        await asyncio.sleep(INACTIVE_TIMEOUT)
        if self.chat_id in pending_games and not self.start_time:
            await word.send_message(self.chat_id, "⚠️ Game expired due to inactivity.")
            del pending_games[self.chat_id]

    async def start_countdown(self):
        asyncio.create_task(self.auto_cleanup())

        for delay in [60, 30, 15, 10]:
            if self.chat_id in active_games:
                return

            await word.send_message(
                self.chat_id,
                f"Starting game in {delay} seconds..." if delay != 60 else
                "🕹️ Game starting in 1 minute! Join now with /join\n\nRules:\n- 45s per turn\n- Word must begin with last letter\n- Every 2 words: +1 letter\n- Every 4 words: -10s"
            )
            await asyncio.sleep(delay)

        if self.chat_id in active_games:
            return

        if len(self.players) >= 2:
            await self.start_game()
        else:
            await word.send_message(self.chat_id, "⚠️ Not enough players to start.")
            pending_games.pop(self.chat_id, None)

    async def start_game(self):
        self.start_time = datetime.utcnow()
        active_games[self.chat_id] = self
        pending_games.pop(self.chat_id, None)

        self.current_word = random.choice('abcdefghijklmnopqrstuvwxyz').upper()
        turn_order = "\n".join([f"• {p['mention']}" for p in self.players])
        await word.send_message(
            self.chat_id,
            f"✅ Game Started!\n\n🔤 First letter: **{self.current_word}**\n🔁 Turn order:\n{turn_order}"
        )
        await self.next_turn()

    async def next_turn(self):
        if self.chat_id not in active_games:
            return

        if not self.players:
            await word.send_message(self.chat_id, "❌ No players left. Ending game.")
            active_games.pop(self.chat_id, None)
            return

        if self.time_left <= 0:
            return await self.handle_timeout()

        player = self.players[self.turn_index]
        await word.send_message(
            self.chat_id,
            f"🎯 {player['mention']}'s turn\n"
            f"Start with: **{self.current_word[-1].upper()}**\n"
            f"Min length: {self.word_length} | Time: {self.time_left}s\n"
        )

        try:
            answer = await word.listen(
                filters=filters.user(player['id']) & filters.chat(self.chat_id) & filters.text,
                timeout=self.time_left
            )
            await self.validate_word(answer)
        except asyncio.TimeoutError:
            await self.handle_timeout()

    async def validate_word(self, msg: Message):
        wordd = msg.text.strip().lower()

        if not wordd.startswith(self.current_word[-1]):
            await msg.reply(f"❌ Must start with **{self.current_word[-1].upper()}**")
            return await self.next_turn()

        if len(wordd) < self.word_length:
            await msg.reply(f"❌ Too short! Needs {self.word_length}+ letters.")
            return await self.next_turn()

        if wordd not in WORD_SET:
            await msg.reply("❌ Word not in dictionary.")
            return await self.next_turn()

        if wordd in self.used_words:
            await msg.reply("❌ Already used!")
            return await self.next_turn()

        self.used_words.add(wordd)
        self.current_word = wordd
        self.word_count += 1
        self.consecutive_count += 1

        if self.consecutive_count % 4 == 0:
            self.time_left = max(10, self.time_left - 10)
        if self.consecutive_count % 2 == 0:
            self.word_length += 1

        await update_stats(msg.from_user.id, "total_words", 1)
        await update_stats(msg.from_user.id, "total_letters", len(wordd))

        self.turn_index = (self.turn_index + 1) % len(self.players)
        await word.send_message(self.chat_id, f"✅ **{wordd}** accepted!")
        await self.next_turn()

    async def handle_timeout(self):
        player = self.players.pop(self.turn_index)
        await word.send_message(self.chat_id, f"⏱️ {player['mention']} ran out of time and is eliminated.")

        if len(self.players) == 1:
            winner = self.players[0]
            duration = datetime.utcnow() - self.start_time
            longest = max(self.used_words, key=len) if self.used_words else "N/A"

            await word.send_message(
                self.chat_id,
                f"🏆 Winner: {winner['mention']}\nTotal words: {self.word_count}\nLongest: {longest}\nTime: {str(duration).split('.')[0]}"
            )

            await update_stats(winner['id'], "games_won", 1)
            for p in self.players:
                await update_stats(p['id'], "games_played", 1)

            prev_stats = await get_stats(winner['id'])
            if longest and len(longest) > len(prev_stats.get("longest_word", "")):
                await update_stats(winner['id'], "longest_word", longest)

            active_games.pop(self.chat_id, None)
        else:
            self.turn_index %= len(self.players)
            await self.next_turn()