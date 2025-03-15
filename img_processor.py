import os
import base64
import json
from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAI

# 載入環境變數
load_dotenv()
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
RESOURCE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

# 初始化 Azure OpenAI 與 OpenAI 客戶端
azure_client = AzureOpenAI(
    api_key=API_KEY,
    api_version="2024-09-01-preview",
    azure_endpoint=RESOURCE_ENDPOINT
)
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def gpt4o_request(messages):
    """發送請求到 GPT-4o 模型並返回回應內容。"""
    try:
        response = azure_client.chat.completions.create(
            model="gpt4o",
            messages=messages
        )
        return response.choices[0].message.content
    except:
        return "error"
    
def o1_request(messages):
    """發送請求到 O1 模型並返回回應內容。"""
    try:
        response = openai_client.chat.completions.create(
            model="o1",
            messages=messages
        )
        return response.choices[0].message.content
    except:
        return "error"
    
def json_request(messages):
    """發送請求並以 JSON 格式返回回應內容。"""
    response = azure_client.chat.completions.create(
        model="gpt4o",
        messages=messages,
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

class ExamProcessor:
    def __init__(self):
        """初始化 ExamProcessor，設置預設的提示語和狀態。"""
        self.class_prompt = "這是單選題 只有一個正確答案 只要回答我答案選項12345就好 不用答案内容"
        self.mixd = False
        self.bad_set = None
        self.bad_img = None
        self.bad_changed_class = None

    def img_number(self, img):
        """從圖像中提取問題編號和題組。"""
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
        return json_request(msgs)

    def img_change(self, img):
        """檢測題型變化和起始問題編號。"""
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
        return json_request(msgs)

    def img_ans(self, imgs, prompt):
        """使用一張或多張圖像生成問題或題組的答案。"""
        # 佔位符實現；請替換為實際的 AI 模型調用
        print(prompt)
        # return "skip"
        # 取消注釋並調整為實際實現：
        msgs = [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}", "detail": "high"}} for img in imgs]},
                {"role": "user", "content": prompt}]
        return gpt4o_request(msgs)

    def class_match(self, class_type):
        """將題型映射到相應的提示語。"""
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
        return self.class_prompt  # 默認回退

    def process_block(self, imgs, block, changed_class):
        """
        處理一個問題區塊（單個問題或題組）。
        
        參數：
            imgs: 圖像數據列表（base64 編碼）。
            block: 問題編號列表（單個問題或題組）。
            changed_class: 包含 "class"（題型）和 "n"（起始編號）的字典。
        """
        start_n = block[0]
        # 如果有題型變化且不在混合模式下，則更新提示語
        if start_n == changed_class["n"] and not self.mixd and changed_class["class"] != "無":
            self.class_prompt = self.class_match(changed_class["class"])

        if len(block) == 1:
            prompt = f"請回答第{block[0]}題 並忽略其他所有題目，{self.class_prompt}"
        else:
            prompt = f"請回答第{block}題 並忽略其他所有題目，{self.class_prompt}"
        
        answer = self.img_ans(imgs, prompt)
        return f"第{block}題"+answer

    def process_bad_set(self, img1, img2, set_list, changed_class):
        """
        處理跨越兩張圖片的題組，並考慮題型變化。
        """
        for n in set_list:
            # 檢查第一張圖片的題型變化
            if n == changed_class["n"] and changed_class["class"] != "無":
                self.class_prompt = self.class_match(changed_class["class"])
            
            # 使用當前的 class_prompt 生成提示並獲取答案
        prompt = f"請回答第{set_list}題 並忽略其他所有題目，{self.class_prompt}"
        answer = self.img_ans([img1, img2], prompt)
        return f"第{set_list}題"+answer

    def main(self, path):
        """主方法，處理從 image4.png 到 image7.png 的考試圖像。"""

        with open(path, "rb") as image_file:
            img = base64.b64encode(image_file.read()).decode('utf-8')

        reply_number = self.img_number(img)
        print(reply_number)
        reply_change = self.img_change(img)
        print(reply_change)

        number = reply_number["number"]
        set_list = reply_number["set"]

        if self.bad_set is not None:
            # 處理 bad set，並傳遞兩張圖片的題型變化信息
            print("處理 bad set:", self.bad_set)
            yield self.process_bad_set(self.bad_img, img, self.bad_set, self.bad_changed_class)

            # 排除已處理的 bad set 題目
            number = [n for n in number if n not in self.bad_set]
            self.bad_set = None
            self.bad_img = None
            self.bad_changed_class = None

        # 確定當前圖像中要處理的區塊
        if set_list and not set(set_list).issubset(set(number)):
            # 題組跨越到下一張圖像（bad set）
            self.bad_set = set_list
            self.bad_img = img
            self.bad_changed_class = reply_change
            blocks = [[n] for n in number if n not in set_list]
        else:
            # 正常情況：題組完全包含或無題組
            if set_list:
                blocks = [[n] for n in number if n not in set_list] + [set_list]
            else:
                blocks = [[n] for n in number]

        # 處理當前圖像中的每個區塊
        for block in blocks:
            yield self.process_block([img], block, reply_change)
            

        return 0


if __name__ == "__main__":
    processor = ExamProcessor()
    for i in range(5, 8):
        input("按 Enter 繼續...")
        processor.main(f"physics/image{i}.png")