# Author:"Carlwang"
# Date:2024/10/22 11:58
import os
import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")

modelList = openai.Model.list()

OUTPUT_FILE = "model_list.txt"

with open(OUTPUT_FILE, "a") as f:
    for d in modelList.data:
        f.write(d.id)
        f.write("\n")

# response = openai.Completion.create(
#     # engine="gpt-4o-mini-2024-07-18",
#     engine="gpt-3.5-turbo",
#     prompt="Hello, world!",
#     max_tokens=5
# )
# print(response)
