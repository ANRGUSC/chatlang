import pathlib
import json
import pandas

thisdir = pathlib.Path(__file__).parent.absolute()

prices = {
    "prompt_tokens": 0.0015 / 1000, # 0.0015 USD per 1000 tokens
    "completion_tokens": 0.002 / 1000, # 0.002 USD per 1000 tokens
}

def main():
    logs = thisdir.joinpath("logs.txt").read_text().splitlines()
    records = []
    for log in logs:
        if "tokens:" in log:
            records.append(json.loads(log.split("tokens: ")[1]))

    df = pandas.DataFrame.from_records(records)

    df["prompt_cost"] = df["prompt_tokens"] * prices["prompt_tokens"]
    df["completion_cost"] = df["completion_tokens"] * prices["completion_tokens"]
    df["total_cost"] = df["prompt_cost"] + df["completion_cost"]

    df_per_req = df.groupby(["req_id"]).sum()
    # drop index
    df_per_req = df_per_req.reset_index().drop(columns=["req_id", "agent"])
    print(df_per_req)

    print(f"Cost for {len(df_per_req)} requests: {df_per_req['total_cost'].sum():.2f} USD")

if __name__ == "__main__":
    main()
