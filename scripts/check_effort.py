#!/usr/bin/env python3
"""Check what a reasoning_effort value really does on a TensorFold server, before a benchmark run.

For each effort value it prints the prompt the server renders (/tokenize then /detokenize) and the usage of one
short request (completion tokens and reasoning tokens). Use it to prove that "low" and "high" render different
effort lines, and that "none" turns thinking off (no think block, 0 reasoning tokens).

  python3 check_effort.py http://<head>:8888 <served model name> low high none

Standard library only. It sends one request per effort value.
"""
import json
import sys
import urllib.request

QUESTION = "How many primes are there below 60? Answer with the number."


def post(base, path, body):
    req = urllib.request.Request(base.rstrip("/") + path, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.load(r)


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    base, model, efforts = sys.argv[1], sys.argv[2], sys.argv[3:]
    msgs = [{"role": "user", "content": QUESTION}]
    for e in efforts:
        body = {"model": model, "messages": msgs, "reasoning_effort": e}
        ids = post(base, "/tokenize", body)["tokens"]
        prompt = post(base, "/detokenize", {"model": model, "tokens": ids})["prompt"]
        r = post(base, "/v1/chat/completions", dict(body, max_tokens=4096))
        u = r.get("usage") or {}
        msg = r["choices"][0]["message"]
        print("== reasoning_effort=%s" % e)
        print("rendered prompt: %r" % prompt)
        print("completion_tokens=%s reasoning_tokens=%s reasoning_chars=%d" % (
            u.get("completion_tokens"), (u.get("completion_tokens_details") or {}).get("reasoning_tokens"),
            len(msg.get("reasoning_content") or "")))
        print("content: %r" % (msg.get("content") or "")[:200])


if __name__ == "__main__":
    main()
