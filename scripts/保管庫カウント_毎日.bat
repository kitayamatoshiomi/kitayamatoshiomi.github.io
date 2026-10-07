@echo off
rem Obsidian 保管庫のノート数を数えて Work Base に反映する（毎日1回でよい）
rem タスクスケジューラから呼ぶ想定。PC が起動していない日は飛ばされる。
cd /d "%~dp0.."
py scripts\obsidian_count.py || exit /b 1
git add data/obsidian.json
git diff --cached --quiet && exit /b 0
git commit -m "data: 保管庫のノート数" || exit /b 1
git pull --rebase -q
git push -q
