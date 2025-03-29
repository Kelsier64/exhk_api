import os
import base64
import json
import asyncio
from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAI
from openai import AsyncAzureOpenAI, AsyncOpenAI

# Load environment variables
load_dotenv()
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
RESOURCE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

# Initialize Azure OpenAI and OpenAI clients
azure_client = AzureOpenAI(
    api_key=API_KEY,
    api_version="2024-09-01-preview",
    azure_endpoint=RESOURCE_ENDPOINT
)
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

async_azure_client = AsyncAzureOpenAI(
    api_key=API_KEY,
    api_version="2024-09-01-preview",
    azure_endpoint=RESOURCE_ENDPOINT
)
async_openai_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# Synchronous request functions (unchanged for reference)
def gpt4o_request(messages):
    """Send a request to the GPT-4o model and return the response content."""
    try:
        response = azure_client.chat.completions.create(
            model="gpt4o",
            messages=messages
        )
        return response.choices[0].message.content
    except:
        return "error"

def o1_request(messages):
    """Send a request to the O1 model and return the response content."""
    try:
        response = openai_client.chat.completions.create(
            model="o1",
            messages=messages
        )
        return response.choices[0].message.content
    except:
        return "error"

def json_request(messages):
    """Send a request and return the response content in JSON format."""
    response = azure_client.chat.completions.create(
        model="gpt4o",
        messages=messages,
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

# Asynchronous request functions
async def async_gpt4o_request(messages):
    """Send an asynchronous request to the GPT-4o model and return the response content."""
    try:
        response = await async_azure_client.chat.completions.create(
            model="gpt4o",
            messages=messages
        )
        return response.choices[0].message.content
    except:
        return "error"

async def async_o1_request(messages):
    """Send an asynchronous request to the O1 model and return the response content."""
    try:
        response = await async_openai_client.chat.completions.create(
            model="o1",
            messages=messages
        )
        return response.choices[0].message.content
    except:
        return "error"

async def async_json_request(messages):
    """Send an asynchronous request and return the response content in JSON format."""
    try:
        response = await async_azure_client.chat.completions.create(
            model="gpt4o",
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except:
        return {"error": "An error occurred"}

class ExamProcessor:
    def __init__(self):
        """Initialize ExamProcessor with default prompt and state."""
        self.class_prompt = "這是單選題 只有一個正確答案 只要回答我答案選項12345就好 不用答案内容"
        self.mixd = False
        self.bad_set = None
        self.bad_img = None
        self.bad_changed_class = None

    async def img_number(self, img):
        """Extract question numbers and sets from an image asynchronously."""
        prompt = """
        1.請忽略題目内容 列出本圖片中有題號且出現的獨立題目的題號，或是題組中在本圖片中出現的題目，但不包含題組中未在圖片中出現的題目。最後輸出一個題號list:"number":[int]
        2.假如看到紙上有寫 "xx-xx題為題組"（xx是一個整數 可能是個位數或十位數）列出題組的題號(xx-xx中的所有數字) 給我一個"set"list 告訴我幾到幾題為題組 假如沒有題組就給我一個空list
        3.注意1.和2.是互相獨立的任務
        4.有可能set不完全在number中 但set中至少有一題在number中
        Use JSON with keys: "set":[int],"number":[int]
        Example of a valid JSON response:
        {
            "set":[2,3],
            "number":[1,2,3,4]
        }
        """
        msgs = [
            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}", "detail": "high"}}]},
            {"role": "user", "content": prompt}
        ]
        return await async_json_request(msgs)

    async def img_change(self, img):
        """Detect question type changes and starting number asynchronously."""
        prompt = """
        假如有粗體字寫題型和配分 比如："一、單選題（占xx分）" , "二、多選題（占xx分）" , "第貳部分、混合題或非選擇題（占xx分）"
        請在json response中寫新題型和新題型的第一題的題號入比如:{"class":"單選題","n":4} 題型可能是"單選題" "多選題" "選填題" "混合題"(混合題或非選擇題) 之一
        若沒有有粗體字寫題型和配分 則 {"class":"無","n":0}

        Use JSON with keys: "class":str,"n":int
        Example of a valid JSON response:
        {
            "class": "",(value = "單選題" or "多選題" or "填充題" or "混合題" or "無")
            "n": 4
        }
        """
        msgs = [
            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}", "detail": "high"}}]},
            {"role": "user", "content": prompt}
        ]
        return await async_json_request(msgs)

    async def img_ans(self, imgs, prompt):
        """Generate answers for questions or sets using one or more images asynchronously."""
        # Placeholder implementation; replace with actual AI model call
        print(prompt)
        return "skip"
        # Uncomment and adjust for actual implementation:
        # msgs = [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}", "detail": "high"}} for img in imgs]},
        #         {"role": "user", "content": prompt}]
        # return await async_gpt4o_request(msgs)

    def class_match(self, class_type):
        """Map question type to the corresponding prompt."""
        match class_type:
            case "單選題":
                return "這是單選題 只有一個正確答案 只要回答我答案選項12345就好 不用答案内容"
            case "多選題":
                return "這是多選題 可能有多個正確答案 只要回答我答案選項12345就好 不用答案内容 請用list回答"
            case "選填題":
                return "這是選填題 只要回答我答案就好 請用latex回答"
            case "混合題":
                self.mixd = True
                return ("這是混合題 可能是 單選題（只要回答我答案就好） "
                        "多選題（用list回答 只要回答我答案就好） "
                        "填充題（用latex回答 只要回答我答案就好） "
                        "非選擇題（用latex回答 給我最簡計算過程）")
        return self.class_prompt  # Default fallback

    async def process_block(self, imgs, block, changed_class):
        start_n = block[0]
        # Update prompt if there’s a type change and not in mixed mode
        if start_n == changed_class["n"] and not self.mixd and changed_class["class"] != "無":
            self.class_prompt = self.class_match(changed_class["class"])

        if len(block) == 1:
            prompt = f"請回答第{block[0]}題 並忽略其他所有題目，{self.class_prompt}"
        else:
            prompt = f"請回答第{block}題 並忽略其他所有題目，{self.class_prompt}"
        
        answer = await self.img_ans(imgs, prompt)
        return f"第{block}題{answer}"

    async def process_bad_set(self, img1, img2, set_list, changed_class):
        for n in set_list:
            if n == changed_class["n"] and changed_class["class"] != "無":
                self.class_prompt = self.class_match(changed_class["class"])
        
        prompt = f"請回答第{set_list}題 並忽略其他所有題目，{self.class_prompt}"
        answer = await self.img_ans([img1, img2], prompt)
        return f"第{set_list}題{answer}"

    async def main(self, path):
        """
        Process a single image asynchronously.
        修改點：改成 async generator，完成一題就 yield 一個結果
        """
        with open(path, "rb") as image_file:
            img = base64.b64encode(image_file.read()).decode('utf-8')

        # Run img_number and img_change concurrently
        reply_number, reply_change = await asyncio.gather(
            self.img_number(img),
            self.img_change(img)
        )
        number = reply_number["number"]
        set_list = reply_number["set"]

        # 如果前一張圖片有跨頁的題組，先處理並 yield 結果
        if self.bad_set is not None:
            result = await self.process_bad_set(self.bad_img, img, self.bad_set, self.bad_changed_class)
            yield result
            # Exclude bad set questions from current processing
            number = [n for n in number if n not in self.bad_set]
            self.bad_set = None
            self.bad_img = None
            self.bad_changed_class = None

        # Determine blocks to process in the current image
        if set_list and not set(set_list).issubset(set(number)):
            # Set spans to the next image (bad set)
            self.bad_set = set_list
            self.bad_img = img
            self.bad_changed_class = reply_change
            blocks = [[n] for n in number if n not in set_list]
        else:
            # Normal case: set is fully contained or no set
            if set_list:
                blocks = [[n] for n in number if n not in set_list] + [set_list]
            else:
                blocks = [[n] for n in number]

        # Process all blocks concurrently and yield each result as完成
        tasks = [self.process_block([img], block, reply_change) for block in blocks]
        for coro in asyncio.as_completed(tasks):
            result = await coro
            yield result

# 修改 __main__ 部分，使用 async for 來即時印出每一 yield 出來的答案
if __name__ == "__main__":
    processor = ExamProcessor()
    async def run_processing():
        for i in range(5, 8):
            input("按 Enter 繼續...")
            # main 變成 async generator，使用 async for 遍歷 yield 的結果
            async for res in processor.main(f"physics/image{i}.png"):
                print(res)
    asyncio.run(run_processing())
