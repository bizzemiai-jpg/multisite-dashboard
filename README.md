# multisite-dashboard

3サイト（biz-english-ai / ai-gyomu / side-invest）の統合ダッシュボード。

公開URL: https://bizzemiai-jpg.github.io/multisite-dashboard/

## 自動更新の仕組み
ローカル `C:\Temp\dashboard\build_dashboard.py` が走るたびに自動で git push される。

## 「次にやるべきこと」のメンテ方法
`actions.json` を編集して push するだけ。サイトごとの未対応タスクを `[icon, 説明]` 配列で記述。
- 🔥 / 🔥🔥 → 緊急（赤色表示）
- それ以外 → 通常（黄色表示）

## build_dashboard.py への組み込み（ローカル側で1回だけ設定）
`build_dashboard.py` の publish ブロックの中、`shutil.copy` の直後に以下を1行追加:
```python
subprocess.run(["python", os.path.join(repo, "inject_actions.py")], cwd=repo, capture_output=True)
```
これで毎回のビルドで「次にやるべきこと」セクションが自動再注入される。
