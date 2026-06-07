# pdftotxtautomater
Project - Extracts certain specific fields from pdfs and returns txt files with those fields

How to setup-
1. Download https://ollama.com/download

2. Open terminal and run the following commands(Only need to run these once to setup, after that everything is automated)
   ```
   ollama pull llama3.2    (extracts the free ollama llm model which i have used)
   pip install pdfplumber watchdog ollama     (install dependencies)
   ```

3. Set up the following folder structure

        po_extractor/
            ├── extract_fields.py   
            ├── watcher.py          
            ├── inbox/              ← save PDFs here 
            └── output/             ← .txt results appear here 

5. If you want to change which fields are extracted then open extract_fields.py and edit FIELDS_TO_EXTRACT to add or remove fields

6. You can also change the model if you want in extract_fields.py. This is optional. I am currently using the llama 3.2 free model for this

How to run-
1. edit extract_fields.py to add or remove fields
2. drop pdfs in inbox folder
3. open terminal and run the following command
   ```
   cd file/path/to/po_extractor
   python watcher.py (this is for running in auto mode, will run for all pdfs in inbox)
   python extract_fields.py path/to/thepdf.pdf (this is for running in manual mode, will run only for the pdf whose path is mentioned in the command)
   ```
use auto mode when you want to extract the SAME fields from multiple pdfs. if you want different fields from different pdfs, then use manual mode.

example working-

if i wanted to extract name and date from pdfs 1,2,3 then i would first put those fields in extract_fields.py then use auto mode 

if i wanted to extact name from pdf 1 but date from pdf 2 then i would first put name in extract_field.py, run in manual mode for pdf 1 then edit extract_field and replace name with date then run in manual mode for pdf 2



