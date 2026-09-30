# MAGI — 三賢人による合議システム

エヴァンゲリオンの **MAGI** をモチーフにした、お題を練り上げる Claude Code / Codex 用スキル。赤木ナオコ博士が自身の人格の3側面を移植した3つのスーパーコンピュータに倣い、**科学者・母・女**の3人格（MELCHIOR / BALTHASAR / CASPER）が、与えられたお題を独立に採点する。全員が80点に達するまで自動で練り直し、合議で可決された完成版を返す。お題のジャンルは問わない ── 企画・ネーミング・コピー・解説・戦略・分析まで、練り上げる価値があるものなら何でも。途中でユーザーに質問せず、可決まで一気に自走する。

**ホスト共通:** Claude Code、Codex、piで同じスキルを利用できます。pi経由でローカルQwenなどにも各席を委任できます。

**席別Formation:** 3席それぞれに実行器・モデル・Thinkingを指定できます。未指定席はMAGIを起動したAI（primary）が担当します。既存のReal MELCHIOR指定も利用できます。

## 仕組み

外に立つ司会者はいない。3人は批評家ではなく**作者**だ ── 案を書くのも、鍛え合うのも、束ねるのも3人自身。

1. 3ユニットが各観点から**開幕案**を出し、突き合わせて叩き台にする。
2. 各ユニットが**独立に採点**し、否決理由と「次にどうすれば上がるか」を添える（自分の軸だけで採点し、妥協しない）。
3. 各ユニットが自分の観点で**次の版を自分で書く**（抽象的な指示ではなく、具体的な中身そのもの）。
4. 3案を統合して次版にし、全員80点に達するまで**くり返す**。
5. 全員80で**可決**。完成版を提示して終了。

点数は捏造しない。上限まで回しても全員が80に届かないときは、80を演出せず、到達点と**割れている理由**を正直に報告する（誠実なデッドロック報告）。

## 審議の一例（短縮）

MAGI の審議がどう進むかの一例（イメージ）:

```text
お題：「絶対に急かさない集中タイマーの名前」

━━━ MAGI ／ 開幕 ━━━
  MELCHIOR（論理）    「ポモ静音」── 機能が一目で分かる説明的な名前
  BALTHASAR（共感）   「ふぅ」── 静かで、ユーザーを急かさない
  CASPER（尖り）      「"ポモ静音"は仕様書。名前じゃない。心を動かせ」

━━━ MAGI ／ 第1議 ━━━
  MELCHIOR   78  否決 ──「ふぅ」は覚えやすいが、集中を何も語っていない
  BALTHASAR  84  可決
  CASPER     63  否決 ── 無難。ゆえに記憶に残らない。引き込む力は？

━━━ MAGI ／ 可決（第2議）━━━  M:83  B:86  C:82
  最終案：「とろり」── とろりと集中に引き込む静けさ。決して急かさない
```

点数は台本ではなく正直な計測 ── 全員80でしか可決せず、届かなければ誠実なデッドロックを報告する。

## インストール

### プラグインとして（推奨）

Claude Code の中で次を実行します:

```text
/plugin marketplace add tmknzz/MAGI
/plugin install magi@magi
```

スキルの登録が自動で行われます。

### 手動インストール（Claude Code）

スキルフォルダを Claude Code のスキルディレクトリにコピーします:

```bash
git clone https://github.com/tmknzz/MAGI.git
cd MAGI
mkdir -p ~/.claude/skills && cp -R skills/magi ~/.claude/skills/magi
```

### 手動インストール（Codex）

スキルフォルダを Codex のスキルディレクトリにコピーします:

```bash
git clone https://github.com/tmknzz/MAGI.git
cd MAGI
mkdir -p ~/.agents/skills && cp -R skills/magi ~/.agents/skills/magi
```

Codex はユーザーレベルのスキルを `~/.agents/skills` から読み込みます（リポジトリ直下の `.agents/skills` に置けばプロジェクト単位でも使えます）。

### piで使用

```sh
pi --skill /absolute/path/MAGI/skills/magi/SKILL.md
```

pi内で`/skill:magi`からお題を渡します。`~/.agents/skills/magi`へのインストールも利用できます。

## Formationの指定

`~/.config/magi/formations/local.conf`に例えば次のように書き、「MAGIのlocalで審議して」と指定します。

```text
MAGI-M: pi qwen38-local/Qwen3.8-27B-abliterated-MLX-4bit low
MAGI-B: primary
MAGI-C: codex gpt-6-astra high
```

モデルIDとThinkingの対応は接続環境に合わせます。未指定席はprimary。MAGI定義を選ばなければVDGGのMAGI席を継承し、それもなければ全席primaryです。単独実行にVDGGは不要です。

設定形式・優先順位・CLI・pi接続・失敗時の扱いは[Formationガイド](skills/magi/references/formations.md)を参照してください。ヘルパーにはPython 3が必要です。

## 使い方

次のいずれかで起動します:

- `/magi` と打つ
- 「MAGIで練って」「MAGIで審議して」のように MAGI を名指しで頼む
- 「MAGI」とはっきり名前を呼ぶ

お題を受け取ると、MAGIは**質問を挟まずに自走**する。審議のログ（各議の採点と詰め）は見せるが、途中で「どうしますか？」とは止まらない。可決まで一気に回す。

## VDGG連携

[VibesDeGoGo! for Claude Code](https://github.com/tmknzz/VibesDeGoGo-for-Claude-Code) または [VibesDeGoGo! for Codex](https://github.com/tmknzz/VibesDeGoGo-for-Codex) を併用している場合、MAGIは2つの役割も担う:

- **(a) Step 0 の要件審議** ── 要件ドラフトを3人格で叩き、判断材料をユーザーに渡す。
- **(b) 主観的成果物のレビューゲート** ── 文言・ドキュメント・デザイン・ネーミング等を可決/否決する。

発火条件はユーザーのグローバル指示（Claude Code は CLAUDE.md、Codex は AGENTS.md）に書かれている。レビューゲートを可決したときだけ、呼び出し元が現行VDGGのレビューゲートを通して記録する（Codexでは `vdgg_review_run`）。

このときは縮小版の**軽量議**で回す（基本3議。収束が明白なときだけ最大5議まで延長）。MAGIは**「望ましさの番人」であって「正しさの番人」ではない** ── コードの正しさ（動くか・バグがないか）は審議しない。それはテストと外部コードレビューの仕事だ。

## オマージュと非提携

MAGI は『新世紀エヴァンゲリオン』への独立した**ファン・オマージュ**です。作中のスーパーコンピュータ MAGI、および MELCHIOR / BALTHASAR / CASPER の名称は同作に由来し、それぞれの権利者（株式会社カラー／GAINAX）に帰属します。本プロジェクトはカラー・GAINAX とは**一切の提携・承認・出資関係がなく**、これらの名称や概念へのいかなる権利も主張しません ── 敬意を込めて用いているだけです。下記の MIT ライセンスが及ぶのは本リポジトリ自身のオリジナルのコードと文章のみで、参照している商標やキャラクターには及びません。

## ライセンス

MIT License. Copyright (c) 2026 tmknzz. 詳細は [LICENSE](LICENSE) を参照。
