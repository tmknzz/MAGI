# 席別Formation

単独実行はPython 3と使用するCLIだけで動く。VDGGは必須ではない。
`~/.config/magi/formations/<名前>.conf` に定義する（`MAGI_CONFIG_DIR`で設定ルートを変更可）。

```text
MAGI-M: pi qwen38-local/Qwen3.8-27B-abliterated-MLX-4bit low
MAGI-B: primary
MAGI-C: codex gpt-6-astra high
--
ここから下は自由メモ。
```

各行は `MAGI-M/B/C: 実行器 [モデル] [Thinking]`。`M/B/C`も可。
実行器は `primary`（`inline`も可）、`pi`、`claude`、`codex`。
piは曖昧なモデル選択を避けるため完全な`provider/model-ID`を必須とする。
モデルIDに`/`が含まれていてもよい。ThinkingはモデルIDの末尾に付けず別トークンにする。
Claude/Codexはモデル・Thinkingを省略するとそのCLIの設定を使う。
未指定席は常にprimary。モデルもThinkingも起動元のままで、新しいCLIは起動しない。
受理するThinkingはpi=`off|minimal|low|medium|high|xhigh|max`、Codex=`minimal|low|medium|high|xhigh|max|ultra`、Claude=`low|medium|high|xhigh|max`。各モデルの対応は別途確認する。
モデルとThinkingの両方を書く場合は必ずこの順。1トークンだけならThinking語彙を優先する。
未指定のThinkingはCLI/providerの既定。どのAIでも同じ強さを意味するものではない。

## 選択と優先順位

1. `--formation <名前>`、または環境変数`MAGI_FORMATION`で選んだMAGI定義。
2. MAGI定義がないとき、呼び出し元が渡した`--vdgg-helper /絶対パス/vdgg-state.sh`でVDGGのMAGI3席を解決。
3. 両方なければ全席primary。

MAGI定義を選んだら未記載席はprimary。VDGGの席を部分合成しない。
指定されたファイルの欠落・不正行・重複席はエラー。無指定と設定ミスを区別する。
MAGI定義には`*`やfallbackを追加していない。VDGG経路は既存のalias/custom executor/明示fallbackをそのままVDGGに任せる。
VDGGフォーメーションの`*`はMAGI席を対象にしない。
VDGG本体が未対応の`pi model thinking`をVDGG定義へ直接追加しない。pi用はMAGI定義を選択する。

## ホストの実行手順

`SCRIPT`はこのスキル内の`scripts/magi-seat.py`の絶対パス。

```sh
python3 "$SCRIPT" resolve --formation local > /絶対パス/lineup.json
python3 "$SCRIPT" prepare --seat M --input /絶対パス/round-1-candidate.txt
python3 "$SCRIPT" run --formation local --seat M \
  --expected-lineup /絶対パス/lineup.json \
  --input /絶対パス/round-1-candidate.txt --output /絶対パス/round-1-M.txt
python3 "$SCRIPT" validate --input /絶対パス/round-1-M.txt
```

- VDGG内では呼び出し元ホストのhelperを`resolve`と`run`の両方へ同じ値で渡す。Step 0は`VDGG_FORMATION`を渡し、開始後はhelperがactive stateのformationを読む。フォーメーション無指定のVDGGではhelperを渡さず全席primary。
- `resolve`を開幕前に実行して3席の割当を保存・表示する。`run`には毎回`--expected-lineup`を渡し、審議中に設定・VDGG stateを変更しない。primary席は`prepare`した人格・規範・対象に従い**現在のホスト自身**が応答し、保存した応答を`validate`する。スクリプトの`run`はprimaryを実行せずエラーにする。
- 開幕案では`prepare/run/validate`に`--opening`を付ける。通常の議ではSCORE・詰め・提案の3行を使う。開幕案は票ではない。
- 全席に同一ファイルの審議対象を渡し、3席が完了するまで変更しない。当該議の他席の点数・提案は渡さない。ローカルモデルでは順番に実行してよい。
- 外部席は毎回別プロセス。piはツール・拡張・コンテキスト・スキルの自動読込を無効化。Codex read-onlyはシェル禁止を意味しない。審議対象だけを渡し、他のファイルを調べるよう指示しない。
- 実行が成功し、応答検証も成功して初めて票を採用。80未満は正常な否決。失敗・欠席・空応答・不正形式は可決不能。ホストが外部応答を書き換えて形式を通さない。
- 外部返答は指定したファイルへそのまま保存。隣の`.json`には設定、対象と返答のハッシュ、時間、点数を記録。モデルやThinkingの**実効値の証明ではない**。CLIの引数受理とバックエンドの実対応を区別する。
- 既存出力を再利用しない。ラウンド・席ごとに一意な保存先を使う。タイムアウトは既定180秒、`--timeout`で変更可。自動リトライはしない。

## piとローカルQwen

pi上での単独起動はスキルを通常どおり読み込む。

```sh
pi --skill /絶対パス/MAGI/skills/magi/SKILL.md
```

pi内で`/skill:magi`からお題とFormation名を指定する。
`~/.agents/skills/magi`もpiの探索先。外部席の実行時には再帰起動を防ぐためスキルを読ませない。

外部席のpi実行ファイルは`MAGI_PI_BIN`、pi設定ディレクトリは`MAGI_PI_AGENT_DIR`で指定できる。
後者がなければ通常の`PI_CODING_AGENT_DIR`を使う。
`MAGI_CODEX_BIN`、`MAGI_CLAUDE_BIN`も指定可。値は単一の実行ファイルで、シェルコマンド文字列ではない。

piの`models.json`で正確なprovider/modelとエンドポイントを登録する。
Qwenのテンプレートがdeveloperロールを受けない場合は`supportsDeveloperRole: false`を指定する。
Qwenでは`reasoning: true`と`compat.thinkingFormat: "qwen"`によりThinkingのON/OFFを送る。
`supportsReasoningEffort: true`でeffortも送るが、受信側による上書き・非対応・丸めは別途検証する。
共有プロキシがThinkingを固定する場合、設定表示だけで成功としない。
helperはpiのモデル一覧で完全一致する登録とThinking対応の宣言を検査する。バックエンドが各強度をどう扱うかは呼び出し元が接続ごとに事前検証し、不対応なら審議を開始しない。
APIキーはFormationへ書かず、providerの環境変数参照を使う。
