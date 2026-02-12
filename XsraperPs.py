import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import asyncio
import threading
import json
import os
import re
from datetime import datetime
from twikit import Client

# د رنګونو او ډیزاین تنظیمات
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ElyasPashtoScraper(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("د الیاس سکریپر - پښتو نسخه (اصلاح شوی)")
        self.geometry("1200x850")
        
        # اصلي ګریډ (Grid) جوړښت
        self.grid_columnconfigure(0, weight=1) # ښي اړخ (تنظیمات)
        self.grid_columnconfigure(1, weight=2) # کیڼ اړخ (ډیټا)
        self.grid_rowconfigure(0, weight=1)

        self.scraped_data = []
        self.is_scraping = False

        # ==================== ښي اړخ پنل (تنظیمات او کوکیز) ====================
        self.right_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.right_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # --- ۱. د کوکیز مدیریت پنل ---
        self.auth_frame = ctk.CTkFrame(self.right_panel, corner_radius=15, border_width=1, border_color="#404040")
        self.auth_frame.pack(fill="x", pady=(0, 15), ipady=5)
        
        self.auth_title = ctk.CTkLabel(self.auth_frame, text="🔑 د کوکیز مدیریت", font=("Arial", 16, "bold"), text_color="#3B8ED0")
        self.auth_title.pack(anchor="e", padx=15, pady=10)
        
        # CT0
        ctk.CTkLabel(self.auth_frame, text=":CT0 کوډ").pack(anchor="e", padx=15)
        self.ct0_entry = ctk.CTkEntry(self.auth_frame, justify="right")
        self.ct0_entry.pack(padx=15, pady=5, fill="x")
        self.ct0_entry.insert(0, "2620c27ebc24a02176f8d9680beb65b99a2688b40808ffa9628a8f4bb6cc16129b56e7e3b881c7d69887b51ce9e14f735ae73372ca032cdcb9e9d938fddcaf5e7fc5fff2a9ad0ec06ce56482dc3def6f")

        # Auth Token
        ctk.CTkLabel(self.auth_frame, text=":Auth Token کوډ").pack(anchor="e", padx=15)
        self.auth_entry = ctk.CTkEntry(self.auth_frame, justify="right")
        self.auth_entry.pack(padx=15, pady=(5, 15), fill="x")
        self.auth_entry.insert(0, "1de0ebceee7c99e2fd6af6c8e953fd341af3478c")

        # د کوکیز بیکپ او ریسټور بټنې
        self.cookie_btn_frame = ctk.CTkFrame(self.auth_frame, fg_color="transparent")
        self.cookie_btn_frame.pack(fill="x", padx=10, pady=10)
        
        self.backup_btn = ctk.CTkButton(self.cookie_btn_frame, text="بیکپ (Save)", width=100, command=self.backup_cookies, fg_color="#E59400")
        self.backup_btn.pack(side="left", padx=5)
        
        self.restore_btn = ctk.CTkButton(self.cookie_btn_frame, text="راپورته کول (Load)", width=100, command=self.restore_cookies, fg_color="#555555")
        self.restore_btn.pack(side="right", padx=5)

        # --- ۲. اصلي ټیبونه (Tabs) ---
        self.tab_view = ctk.CTkTabview(self.right_panel)
        self.tab_view.pack(fill="both", expand=True)
        
        self.tab_search = self.tab_view.add("لټون (Search)")
        self.tab_settings = self.tab_view.add("تنظیمات (Settings)")

        # >>> ټیب ۱: د لټون برخه <<<
        self.search_lbl = ctk.CTkLabel(self.tab_search, text=":دلته خپل کیورډونه یا هشټاګونه ولیکئ", font=("Arial", 13, "bold"))
        self.search_lbl.pack(anchor="e", padx=10, pady=5)
        
        # اصلاح: justify="right" دلته لرې شو ځکه Textbox یې نه مني
        self.query_box = ctk.CTkTextbox(self.tab_search, height=180, font=("Arial", 14))
        self.query_box.pack(padx=10, pady=5, fill="x")
        self.query_box.insert("0.0", "#خلافت_یوازینی_انتخاب")

        self.limit_lbl = ctk.CTkLabel(self.tab_search, text=":د پوسټونو تعداد (حد اکثر)")
        self.limit_lbl.pack(anchor="e", padx=10, pady=(15, 0))
        self.limit_entry = ctk.CTkEntry(self.tab_search, justify="center")
        self.limit_entry.pack(padx=10, pady=5, fill="x")
        self.limit_entry.insert(0, "50")

        self.start_btn = ctk.CTkButton(self.tab_search, text="پیل کړئ (Start)", command=self.start_scraping_thread, fg_color="#2CC985", height=50, font=("Arial", 16, "bold"))
        self.start_btn.pack(padx=10, pady=30, fill="x")

        # >>> ټیب ۲: پرمختللي تنظیمات (نوی ډیزاین) <<<
        # د تنظیماتو ګروپ ۱
        self.set_grp1 = ctk.CTkFrame(self.tab_settings, corner_radius=10, border_width=1, border_color="#505050")
        self.set_grp1.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(self.set_grp1, text=":د پلټنې ډول", font=("Arial", 14, "bold")).pack(anchor="e", padx=15, pady=(10, 5))
        self.post_type_var = ctk.StringVar(value="Latest")
        self.type_menu = ctk.CTkOptionMenu(self.set_grp1, variable=self.post_type_var, 
                                           values=["Latest (تر ټولو نوي)", "Top (مشهور/برترین)", "Normal (ګډ)"])
        self.type_menu.pack(padx=15, pady=(0, 15), fill="x")

        # د تنظیماتو ګروپ ۲
        self.set_grp2 = ctk.CTkFrame(self.tab_settings, corner_radius=10, border_width=1, border_color="#505050")
        self.set_grp2.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(self.set_grp2, text=":وروستی ترتیب (Sort)", font=("Arial", 14, "bold")).pack(anchor="e", padx=15, pady=(10, 5))
        self.sort_algo_var = ctk.StringVar(value="None")
        self.sort_menu = ctk.CTkOptionMenu(self.set_grp2, variable=self.sort_algo_var, 
                                           values=["None (نارمل)", "Shortest First (لنډ اول)", "Longest First (اوږد اول)"])
        self.sort_menu.pack(padx=15, pady=(0, 15), fill="x")

        # ==================== کیڼ اړخ پنل (ډیټا او لاګ) ====================
        self.left_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.left_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # ۱. د فایل بټنې
        self.data_frame = ctk.CTkFrame(self.left_panel, corner_radius=10)
        self.data_frame.pack(fill="x", pady=(0, 10))

        self.data_label = ctk.CTkLabel(self.data_frame, text="📂 فایل او راپور", font=("Arial", 16, "bold"))
        self.data_label.pack(side="right", padx=20, pady=15)

        self.save_btn = ctk.CTkButton(self.data_frame, text="ذخیره کول", command=self.save_to_json, state="disabled", fg_color="#3B8ED0")
        self.save_btn.pack(side="left", padx=10)
        
        self.view_btn = ctk.CTkButton(self.data_frame, text="جدول لیدل", command=self.open_view_window, state="disabled")
        self.view_btn.pack(side="left", padx=10)

        # ۲. لاګ (راپورونه)
        self.log_container = ctk.CTkFrame(self.left_panel, corner_radius=10)
        self.log_container.pack(fill="both", expand=True)

        self.log_header = ctk.CTkFrame(self.log_container, height=30, fg_color="transparent")
        self.log_header.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(self.log_header, text="ژوندی راپور (Live Log)").pack(side="right", padx=10)
        
        # د لاګ پاکولو بټن
        self.clear_log_btn = ctk.CTkButton(self.log_header, text="پاکول 🗑️", width=60, height=25, 
                                           fg_color="#CC0000", hover_color="#990000", command=self.clear_log)
        self.clear_log_btn.pack(side="left", padx=10)

        self.log_box = ctk.CTkTextbox(self.log_container, font=("Consolas", 12))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_box.configure(state="disabled")

    # ------------------ منطقي برخې (Logic) ------------------

    def log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def clear_log(self):
        """ لاګ پاکوي """
        self.log_box.configure(state="normal")
        self.log_box.delete("0.0", "end")
        self.log_box.configure(state="disabled")

    def backup_cookies(self):
        """ کوکیز په فایل کې ذخیره کوي """
        data = {
            "ct0": self.ct0_entry.get(),
            "auth_token": self.auth_entry.get()
        }
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json")],
                initialfile="my_cookies.json",
                title="کوکیز ذخیره کړئ"
            )
            if file_path:
                with open(file_path, 'w') as f:
                    json.dump(data, f)
                messagebox.showinfo("بريالی", "کوکیز په خوندي ډول ذخیره شول!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def restore_cookies(self):
        """ کوکیز له فایل څخه پورته کوي """
        try:
            file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")], title="کوکیز فایل انتخاب کړئ")
            if file_path:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                self.ct0_entry.delete(0, "end")
                self.ct0_entry.insert(0, data.get("ct0", ""))
                
                self.auth_entry.delete(0, "end")
                self.auth_entry.insert(0, data.get("auth_token", ""))
                
                messagebox.showinfo("بريالی", "کوکیز اپډیټ شول!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clean_tweet_content(self, text):
        """
        متن پاکوي خو لاینونه (Lines) نه خرابوي.
        """
        # ۱. لینکونه لرې کول
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'www\.\S+', '', text)
        
        # ۲. یوزرنیمونه لرې کول
        text = re.sub(r'@\w+', '', text)
        
        # ۳. د اضافي افقي فاصلو پاکول (خو Enter نه)
        # یوازې Space او Tab پاکوي، Newline (\n) پریږدي
        text = re.sub(r'[ \t]+', ' ', text)
        
        # ۴. د متن له سر او پای څخه تش ځایونه لرې کول
        text = text.strip()
        
        return text

    def extract_hashtags(self, text):
        return re.findall(r'#\w+', text)

    def start_scraping_thread(self):
        if self.is_scraping: return
        threading.Thread(target=self.run_scraping_process).start()

    def run_scraping_process(self):
        asyncio.run(self.scrape_twitter())

    async def scrape_twitter(self):
        self.is_scraping = True
        self.start_btn.configure(state="disabled", text="په کار بوخت دی...")
        self.save_btn.configure(state="disabled")
        self.view_btn.configure(state="disabled")

        raw_queries = self.query_box.get("0.0", "end").strip().split('\n')
        queries = [q.strip() for q in raw_queries if q.strip()]
        
        try: limit = int(self.limit_entry.get())
        except: limit = 50
            
        ct0 = self.ct0_entry.get()
        auth = self.auth_entry.get()
        
        # Search Type Logic
        selected_type = self.post_type_var.get()
        if "Latest" in selected_type: product_type = 'Latest'
        elif "Top" in selected_type: product_type = 'Top'
        else: product_type = 'Top'

        try:
            self.log("Initializing Client...")
            client = Client('en-US')
            client.set_cookies({"ct0": ct0, "auth_token": auth})

            all_results = []
            seen_content_hashes = set()
            global_count = 0

            for query in queries:
                if global_count >= limit: break
                
                self.log(f"--- Searching: {query} ({product_type}) ---")
                
                try:
                    tweets = await client.search_tweet(query, product=product_type, count=limit)
                except Exception as e:
                    self.log(f"Error: {e}")
                    continue

                if not tweets:
                    self.log(f"پوسټ ونه موندل شو.")
                    continue

                while tweets:
                    for tweet in tweets:
                        if global_count >= limit: break
                        
                        original_text = tweet.text
                        
                        # پاکول (د لاینونو ساتلو سره)
                        clean_text = self.clean_tweet_content(original_text)
                        
                        # که متن ډیر لنډ وي، پریږده یې
                        if not clean_text or len(clean_text) < 5: continue

                        # تکرار چک
                        text_hash = hash(clean_text)
                        if text_hash in seen_content_hashes: continue
                        seen_content_hashes.add(text_hash)
                        
                        tags = self.extract_hashtags(original_text)
                        global_count += 1
                        
                        post_obj = {
                            "PostNo": str(global_count),
                            "MyPost": clean_text,
                            "Tags": ", ".join(tags)
                        }
                        all_results.append(post_obj)
                        
                        if global_count % 10 == 0:
                            self.log(f"Collected {global_count} tweets...")

                    if global_count >= limit: break
                    
                    if hasattr(tweets, 'next'):
                        try: tweets = await tweets.next()
                        except: break
                    else: break
            
            # Sorting
            sort_mode = self.sort_algo_var.get()
            if "Shortest" in sort_mode:
                self.log("Sorting: لنډ پوسټونه اول...")
                all_results.sort(key=lambda x: len(x["MyPost"]))
            elif "Longest" in sort_mode:
                self.log("Sorting: اوږد پوسټونه اول...")
                all_results.sort(key=lambda x: len(x["MyPost"]), reverse=True)
            
            # Re-numbering
            for idx, item in enumerate(all_results):
                item["PostNo"] = str(idx + 1)

            self.scraped_data = all_results
            self.log(f"✅ بشپړ شو! ټول پوسټونه: {len(all_results)}")

        except Exception as e:
            self.log(f"Critical Error: {str(e)}")
        
        finally:
            self.is_scraping = False
            self.start_btn.configure(state="normal", text="پیل کړئ (Start)")
            self.save_btn.configure(state="normal")
            self.view_btn.configure(state="normal")

    def save_to_json(self):
        if not self.scraped_data: return
        
        raw_queries = self.query_box.get("0.0", "end").strip().split('\n')
        default_name = "output"
        if raw_queries: default_name = raw_queries[0].replace("#", "").strip()
        
        try:
            file_path = filedialog.asksaveasfilename(
                initialdir=os.path.expanduser("~/Documents"),
                initialfile=f"{default_name}.json",
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json")],
                title="فایل چیرته ذخیره کوئ؟"
            )
            
            if not file_path: return 
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.scraped_data, f, ensure_ascii=False, indent=4)
            
            messagebox.showinfo("بریالی", f"فایل ذخیره شو:\n{file_path}")
            self.log(f"Saved: {file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def open_view_window(self):
        if not self.scraped_data: return
        
        view = ctk.CTkToplevel(self)
        view.title("استخراج شوې ډیټا")
        view.geometry("1000x600")
        view.attributes('-topmost', True) 
        
        columns = ("No", "Post", "Tags")
        tree = ttk.Treeview(view, columns=columns, show="headings")
        
        tree.heading("No", text="شمېره")
        tree.heading("Post", text="متن (MyPost)")
        tree.heading("Tags", text="هشټاګونه")
        
        tree.column("No", width=50, anchor="center")
        tree.column("Post", width=700, anchor="e") # RTL visual
        tree.column("Tags", width=250, anchor="e")
        
        vsb = ttk.Scrollbar(view, orient="vertical", command=tree.yview)
        tree.configure(yscroll=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)
        
        for item in self.scraped_data:
            # د لیدلو لپاره لاینونه په ↵ بدلوو (خو فایل کې به اصلي وي)
            display_text = item["MyPost"].replace("\n", " ↵ ") 
            tree.insert("", "end", values=(item["PostNo"], display_text, item["Tags"]))

if __name__ == "__main__":
    app = ElyasPashtoScraper()
    app.mainloop()