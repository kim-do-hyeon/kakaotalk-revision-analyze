#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import base64
import json
import sqlite3
import sys
from typing import Any, List, Optional, Tuple
from resource.ios_core import ios_decrypter
from resource.android_core import android_decrypter

def sqlite_connect(db_path: str) -> sqlite3.Connection:
	try:
		conn = sqlite3.connect(db_path)
		conn.row_factory = sqlite3.Row
		return conn
	except sqlite3.Error as e:
		fail(f"Failed to open DB: {e}")
		return None  # type: ignore

def process_ios(db_path: str) -> None:
	conn = sqlite_connect(db_path)
	cur = conn.cursor()
	try:
		cur.execute("""
			SELECT id, userId, message, extraInfo
			FROM Message
		""")
	except sqlite3.Error as e:
		conn.close()
		fail(f"Query failed on Message: {e}")

	rows = cur.fetchall()
	if not rows:
		print("[iOS] No rows found in Message.")
	for row in rows:
		row_id = row["id"]
		user_id = int(row["userId"]) if row["userId"] is not None else 0
		message = str(row["message"]) if row["message"] is not None else ""
		extra_info = row["extraInfo"] or ""
		if "modifyHistory" in extra_info:
			extra_info = json.loads(extra_info)
			modify_history = []
			for entry in extra_info["modifyHistory"]:
				if "message" in entry:
					modify_history.append(entry["message"].replace("\r", "").replace("\n", ""))
			print(f"id = {row_id} / 노출 메시지 : {ios_decrypter().decrypt(user_id, message)}")			
			print("--------------------------------")
			for i, message in enumerate(modify_history):
				print(f"수정 {i+1} : {ios_decrypter().decrypt(user_id, message)}")
			print("--------------------------------")

	conn.close()


def guess_user_id_from_row(row: sqlite3.Row) -> Optional[int]:
	candidates = ["userId", "userid", "user_id", "uid", "ownerId", "owner_id"]
	for key in row.keys():
		if key in candidates:
			try:
				return int(row[key])
			except Exception:
				continue
	return None


def process_android(db_path: str, cli_user_id: Optional[int]) -> None:
	conn = sqlite_connect(db_path)
	cur = conn.cursor()
	try:
		cur.execute("""
			SELECT rowid AS id, *
			FROM chat_logs
			WHERE v IS NOT NULL AND v != ''
		""")
	except sqlite3.Error as e:
		conn.close()
		fail(f"Query failed on chat_logs: {e}")

	rows = cur.fetchall()
	if not rows:
		print("[Android] No rows found in chat_logs.")
	for row in rows:
		row_id = row["id"]
		user_id = guess_user_id_from_row(row)
		if user_id is None:
			user_id = cli_user_id
		if user_id is None:
			print(f"[Android] id={row_id} (skip) - userId not found; provide --user-id", file=sys.stderr)
			print("")
			continue
		message = str(row["message"]) if row["message"] is not None else ""

		v_raw = row["v"]
		v_obj = json.loads(v_raw)
		if "modifyLog" in v_obj:
			extra_info = json.loads(v_obj['modifyLog'])
			modify_history = []
			for entry in extra_info:
				modify_history.append(entry["message"].replace("\r", "").replace("\n", ""))
			print(f"id = {row_id} / 노출 메시지 : {android_decrypter().decrypt_try_all(user_id, message)[1]}")
			print("--------------------------------")
			for i, message in enumerate(modify_history):
				print(f"수정 {i+1} : {android_decrypter().decrypt_try_all(user_id, message)[1]}")
			print("--------------------------------")

	conn.close()


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="KakaoTalk DB decryptor for iOS/Android with modify history support.")
	parser.add_argument("--platform", "-p", choices=["ios", "android"], required=True, help="Target platform database format.")
	parser.add_argument("--db", "-d", required=True, help="Path to SQLite DB file.")
	parser.add_argument("--user-id", "-u", type=int, help="Fallback user_id when not obtainable from rows (Android).")
	return parser


def main() -> None:
	parser = build_parser()
	args = parser.parse_args()
	if args.platform == "ios":
		process_ios(args.db)
	elif args.platform == "android":
		process_android(args.db, args.user_id)
	else:
		fail("Unknown platform.")


if __name__ == "__main__":
	main()
