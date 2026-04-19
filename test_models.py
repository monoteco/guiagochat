import os, replicate
os.environ["REPLICATE_API_TOKEN"] = os.environ.get("REPLICATE_API_TOKEN", "")
modelos = ["meta-llama/llama-2-7b-chat", "mistral-community/mistral-7b-instruct-v0.2"]
for m in modelos:
    try:
        print(f"Probando {m}...")
        r = replicate.run(m, input={"prompt":"hi","max_tokens":5})
        print(f"OK: {m}")
        break
    except Exception as e:
        print(f"FAIL {m}: {str(e)[:80]}")
