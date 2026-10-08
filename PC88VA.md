# VZ Editor PC-88VA (PC-Engine) 版

PC-88VA の V3 モード OS「PC-Engine」上で動く VZ Editor 1.60 です。
PC-98 版のソースに `IFDEF PC88VA` で差分を加えた派生ターゲットで、
`PC88VA` を定義すると `PC98` も定義されます。

動作確認は PC-Engine 1.1 (vaeg エミュレータ上) で行っています。実機と
他の版の PC-Engine では未確認です。

## ビルド

Linux 等で、MASM 互換のフリーのアセンブラ [JWasm](https://github.com/Baron-von-Riedesel/JWasm)
とリンカ [JWlink](https://github.com/Baron-von-Riedesel/JWlink) を使ってビルドできます
(python3 も必要)。ソースは MASM 5.1 用のままです。

```sh
export JWASM_BIN=/path/to/jwasm JWLINK_BIN=/path/to/jwlink
tools/build.sh VA      # -> build/VA/VZVA.COM
tools/build.sh 98      # -> build/98/VZ.COM (PC-98 版)
python3 tools/cmpcom.py build/98/VZ.COM VZ-PC98/VZ.COM
```

`cmpcom.py` は、ビルドした PC-98 版が配布版 `VZ-PC98/VZ.COM` と一致する
ことを確かめます。違いは命令の符号化だけです (MASM の `cmp ax,imm16`
等の短縮形と、JWasm の `83 /r` 形式。同じ長さ・同じ動作) 。
環境変数 `JWASM` は jwasm 自身がオプションとして読むので、パスの指定には
`JWASM_BIN` を使います。

MS-DOS 上では従来どおり `mk va` (MASM 5.1) でもビルドできるはずです
(未確認)。

## インストールディスク

`FDImage/VZ_VA.D88` は PC-88VA 版のインストール用 2HD イメージ (D88 形式) です。
PC-98 の MS-DOS 形式 (1024 バイト x 8 セクタ x 77 シリンダ, FAT12) で、
システムは入っていません。`VZVA.COM`, `VZVA.DOC` (説明), PC-98 版の
DEF ファイルとドキュメント、ライセンスを収録しています。

PC-Engine を起動し、このディスクを 2 台目のドライブに入れて、必要な
ファイルをコピーしてください。

```
copy b:vzva.com a:
copy b:vz.def a:
copy b:vzfl.def a:
```

イメージは `tools/mkvadisk.sh` で `build/VA/VZVA.COM` から作り直せます
(何度作っても同じイメージになります)。

## 使い方

`VZVA.COM` と、PC-98 版の `VZ.DEF`, `VZFL.DEF` を同じディレクトリに置いて
起動します。DEF ファイルは PC-98 版のものがそのまま使えます。

```
VZVA README.DOC
```

## PC-Engine 版の動作

- 画面: VZ の実行中は 25 行表示・システムライン非表示にし、PC-Engine の
  システムラインが出ていた場合は最下行に VZ がファンクションキーを
  表示します (SHIFT/CTRL/GRPH で切り替わります)。終了時に元の行数と
  システムラインに戻します。
- キー入力はキーボード BIOS 経由です。日本語入力は PC-Engine の JFP
  がそのまま使えます (全角キーで ON)。
- DOS コマンド (ESC E): PC-Engine の内部コマンド (dir, type, copy など)
  と .COM / .EXE ファイルを実行できます。COMMAND.COM が無いので、
  シェルを起動することはできません。
- 常駐モード (`-z`) は使えません (オプションは無視されます)。
- EMS/XMS、コンソール出力の取込み (XSCR) は使いません。
- スムーススクロールはドット単位ではなく行単位です。

## 移植メモ: PC-Engine と MS-DOS の違い

移植で問題になった点です。PC-Engine 1.1 で実際に確かめた内容を含みます。

- INT 21h は MS-DOS のサブセットです。コンソール入出力 (01h-0Ch),
  2Ah, 2Ch, 37h, 44h, 50h, 51h, 52h, 62h は CF=1, AX=1 で返ります。
  30h は 2.0 を返します。
- プロセスには標準ハンドル (0-4) がありません。文字表示はスクリーン
  エディタ BIOS (INT 94h) を使います。
- PSP の親 PSP (16h) は 0 です。環境 (2Ch) はあります。
- 48h で確保したブロックの MCB の所有者欄は、ブロック自身のセグメント
  になっています。
- INT 9Fh (内部コマンドの実行) は、内部コマンドでないとき AX=FFFFh を
  返しました。
- テキスト VRAM は A000:0000 から 1 文字 1 ワードで、属性は +8000h
  です。全角文字のコードは PC-98 と同じ形式ですが、右半分の印は
  ビット 15 です (PC-98 はビット 7) 。
- スキャンコードは PC-98 とほぼ同じですが、SHIFT/CTRL を押しながらの
  矢印キーはスキャンコードが変わります (AAh-ADh, BAh-BDh)。

## テスト用スクリプト

`tools/va-run.sh` は、vaeg エミュレータで PC-Engine のシステムディスクの
コピーにファイルを書き込み、キー入力スクリプトを流して画面を保存します。
ROM、システムディスクのパスは環境変数で与えます (スクリプト先頭参照)。
